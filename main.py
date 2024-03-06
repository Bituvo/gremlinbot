from math import ceil
from datetime import time
from dotenv import load_dotenv
from gzip import compress, decompress
from json import loads, dumps
from random import choices
from urllib.parse import urlparse
from os import getcwd, environ
from os.path import join, basename
from io import BytesIO
from discord.ext import tasks, commands
from discord import app_commands, ui
import discord
import aiohttp

load_dotenv(join(getcwd(), ".env"))

TOKEN = environ.get("TOKEN")
APPLICATION_ID = int(environ.get("APPLICATION_ID"))
BOT_USER_ID = int(environ.get("BOT_USER_ID"))
ROLE_ID = int(environ.get("ROLE_ID"))
GREMLINS_ID = int(environ.get("GREMLINS_ID"))
THREAD_ID = int(environ.get("THREAD_ID"))
CANDIDATES_PER_PAGE = 10
ACCENT = 0x1199ff
NOON_EST = time(hour=17)

intents = discord.Intents.default()
intents.message_content = True
intents.guild_reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents, application_id=APPLICATION_ID)

def load_data():
    with open("gremlins.dat", "rb") as file:
        return loads(decompress(file.read())).values()
    
def save_data():
    with open("gremlins.dat", "wb") as file:
        file.write(compress(dumps({
            "amount-elected": amount_elected,
            "elected-message-ids": elected_message_ids,
            "candidates": candidates
        }).encode()))

amount_elected, elected_message_ids, candidates = load_data()

class SetDescriptionModal(ui.Modal):
    def __init__(self, index, title="Gremlin Description"):
        super().__init__(title=title)
        self.index = index
        self.add_item(ui.TextInput(label="New description"))

    async def on_submit(self, interaction):
        candidates[self.index]["description"] = self.children[0].value
        save_data()

        try:
            await interaction.response.edit_message(
                content = f"Gremlin description set!",
                view = None
            )
        except discord.errors.NotFound:
            await interaction.response.send_message(
                f"Gremlin description set!",
                ephemeral = True
            )

class AddDescriptionView(ui.View):
    def __init__(self, index):
        super().__init__()
        self.index = index

    @ui.button(label="Add description", style=discord.ButtonStyle.primary)
    async def add_description(self, interaction, button):
        await interaction.response.send_modal(SetDescriptionModal(self.index))

class PaginatedCandidatesView(ui.View):
    def __init__(self):
        super().__init__()
        self.total_pages = ceil(len(candidates) / CANDIDATES_PER_PAGE)
        self.page = 1

    async def get_page(self):
        embed = discord.Embed(title=f"Gremlin Candidates ({len(candidates)})", color=ACCENT)
    
        start_index = (self.page - 1) * CANDIDATES_PER_PAGE
        candidates_to_show = candidates[start_index:start_index + CANDIDATES_PER_PAGE]

        for i, candidate in enumerate(candidates_to_show):
            name = candidate["description"] or "[No description given]"
            embed.add_field(
                name = f"`#{start_index + i + 1}`: *{name}* by __{candidate['author-name']}__",
                value = candidate["message-url"],
                inline = False
            )
        
        embed.set_footer(text=f"Page {self.page} / {self.total_pages}")

        return embed

    async def initial_page(self, interaction):
        embed = await self.get_page()
        await self.update_buttons()
        await interaction.response.send_message(embed=embed, view=self, ephemeral=True)

    async def refresh_page(self, interaction):
        embed = await self.get_page()
        await self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_buttons(self):
        self.children[0].disabled = self.page == 1
        self.children[1].disabled = self.page == 1
        self.children[2].disabled = self.page == self.total_pages
        self.children[3].disabled = self.page == self.total_pages

    @ui.button(emoji="⏮️", style=discord.ButtonStyle.primary)
    async def beginning(self, interaction, button):
        self.page = 1
        await self.refresh_page(interaction)

    @ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction, button):
        self.page -= 1
        await self.refresh_page(interaction)

    @ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        self.page += 1
        await self.refresh_page(interaction)

    @ui.button(emoji="⏭️", style=discord.ButtonStyle.primary)
    async def end(self, interaction, button):
        self.page = self.total_pages
        await self.refresh_page(interaction)

class ConfirmClearCandidatesView(ui.View):
    def __init__(self):
        super().__init__()
    
    @ui.button(label="Clear all candidates", style=discord.ButtonStyle.danger)
    async def clear_candidates(self, interaction, button):
        global candidates
        candidates = []
        save_data()

        await interaction.response.edit_message(content="Gremlin candidates cleared!", view=None)

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Candidate deletion cancelled.", view=None)

class ConfirmClearElectedView(ui.View):
    def __init__(self):
        super().__init__()
    
    @ui.button(label="Clear elected list", style=discord.ButtonStyle.danger)
    async def clear_candidates(self, interaction, button):
        global elected_message_ids
        elected_message_ids = []
        save_data()

        await interaction.response.edit_message(content="Elected gremlins cleared!", view=None)

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Elected gremlin deletion cancelled.", view=None)

class ForceElectionView(ui.View):
    def __init__(self, message, candidate_index):
        super().__init__()
        self.message = message
        self.candidate_index = candidate_index

    @ui.button(label="Elect now", style=discord.ButtonStyle.danger)
    async def elect_now(self, interaction, button):
        global amount_elected, elected_message_ids, candidates

        if self.candidate_index is not None:
            del candidates[self.candidate_index]

        elected_message_ids.append(self.message.id)

        channel = bot.get_channel(GREMLINS_ID)
        await publish_election(channel, {
            "image-url": self.message.attachments[0].url,
            "author-name": self.message.author.display_name,
            "author-avatar-url": self.message.author.display_avatar.url,
            "author-mention": self.message.author.mention,
            "message-url": self.message.jump_url,
            "message-id": self.message.id,
            "description": self.message.content
        }, True)

        await interaction.response.edit_message(
            content = "Gremlin elected!",
            view = None
        )

    @ui.button(label="Choose for next election", style=discord.ButtonStyle.primary)
    async def choose_for_next_election(self, interaction, button):
        if self.candidate_index is None:
            candidates.append({
                "image-url": self.message.attachments[0].url,
                "author-name": self.message.author.display_name,
                "author-avatar-url": self.message.author.display_avatar.url,
                "author-mention": self.message.author.mention,
                "message-url": self.message.jump_url,
                "message-id": self.message.id,
                "description": self.message.content,
                "manually-elected": True
            })
            self.candidate_index = len(candidates) - 1

        await interaction.response.edit_message(
            content = "Gremlin will be picked for the next election.",
            view = None
        )

    @ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="Forced gremlin election cancelled.", view=None)

@app_commands.context_menu(name="Add gremlin as candidate")
async def add_as_candidate(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return

    attachment_found = False
    if message.attachments and len(message.attachments) == 1:
        attachment = message.attachments[0]
        if "image" in attachment.content_type:
            attachment_found = True

    if not attachment_found:
        await reply("Gremlin not found. Make sure that the message has one picture.")
        return
    
    if any(candidate["message-id"] == message.id for candidate in candidates):
        await reply("This gremlin is already in the list of candidates.")
        return
    
    if message.id in elected_message_ids:
        await reply("This gremlin has already been elected!")
        return
    
    index = len(candidates)
    candidates.append({
        "image-url": message.attachments[0].url,
        "author-name": message.author.display_name,
        "author-avatar-url": message.author.display_avatar.url,
        "author-mention": message.author.mention,
        "message-url": message.jump_url,
        "message-id": message.id,
        "description": message.content
    })
    save_data()

    if message.content:
        await reply(f"Gremlin added! ID: **`#{index + 1}`**")
    else:
        await reply((
            f"Gremlin added! ID: **`#{index + 1}`**"
            "\nIt has no description. Would you like to add one?"
        ), view=AddDescriptionView(index))

@app_commands.context_menu(name="Remove gremlin from candidates")
async def remove_from_candidates(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return

    candidate_index = next(
        (i for i, candidate in enumerate(candidates) if candidate["message-id"] == message.id),
        None
    )

    if candidate_index is None:
        await reply("This message is not in the list of candidates.")
        return
    
    del candidates[candidate_index]
    save_data()

    await reply(f"Removed candidate with ID **`{candidate_index + 1}`**.")

@app_commands.context_menu(name="Set gremlin description")
async def set_description(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return
    
    candidate_index = next(
        (i for i, candidate in enumerate(candidates) if candidate["message-id"] == message.id),
        None
    )

    if candidate_index is None:
        await reply("This message is not in the list of candidates.")
        return
    
    await interaction.response.send_modal(SetDescriptionModal(candidate_index))

@app_commands.context_menu(name="Force gremlin election")
async def force_election(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return
    
    attachment_found = False
    if message.attachments and len(message.attachments) == 1:
        attachment = message.attachments[0]
        if "image" in attachment.content_type:
            attachment_found = True

    if not attachment_found:
        await reply("Gremlin not found. Make sure that the message has one picture.")
        return
    
    if message.id in elected_message_ids:
        await reply("This gremlin has already been elected!")
        return
    
    candidate_index = next(
        (i for i, candidate in enumerate(candidates) if candidate["message-id"] == message.id),
        None
    )

    await reply(
        "Should this gremlin be elected now, or for the next election?",
        view = ForceElectionView(message, candidate_index)
    )

bot.tree.add_command(add_as_candidate)
bot.tree.add_command(remove_from_candidates)
bot.tree.add_command(set_description)
bot.tree.add_command(force_election)

@bot.tree.command(
    name = "gremlincandidates",
    description = "List all gremlin candidates"
)
async def list_candidates(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return
    
    if not candidates:
        await reply("There are no gremlin candidates to view.")
        return

    await PaginatedCandidatesView().initial_page(interaction)

@bot.tree.command(
    name = "clearcandidates",
    description = "Clears all gremlin candidates"
)
async def clear_candidates(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not candidates:
        await reply("The list of gremlin candidates is already empty.")
        return
    
    await reply(
        "Are you sure you want to clear the list of gremlin candidates? **This action is irreversible!**",
        view = ConfirmClearCandidatesView()
    )

@bot.tree.command(
    name = "clearelected",
    description = "Clears the internal list of elected gremlins"
)
async def clear_elected(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not elected_message_ids:
        await reply("The list of elected gremlins is already empty.")
        return
    
    await reply(
        "Are you sure you want to clear the list of elected gremlins? **This action is irreversible! Double elections can occur!**",
        view = ConfirmClearElectedView()
    )

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def elect_candidate():
    global amount_elected, elected_message_ids, candidates

    if len(candidates) == 1:
        elected_candidate = candidates.pop(0)
        elected_message_ids.append(elected_candidate["message-id"])
        amount_elected += 1
        save_data()

        return elected_candidate
    
    for i, candidate in enumerate(candidates):
        if candidate["manually-elected"]:
            elected_candidate = candidates.pop(i)
            elected_message_ids.append(elected_candidate["message-id"])
            amount_elected += 1

            return elected_candidate

    message_ids = [candidate["message-id"] for candidate in candidates]
    delta = max(message_ids) - min(message_ids)
    weights = [weight_function((message_id - min(message_ids)) / delta) for message_id in message_ids]

    elected_candidate_index = choices(
        population = range(len(candidates)),
        weights = weights
    )[0]

    elected_candidate = candidates.pop(elected_candidate_index)
    elected_message_ids.append(elected_candidate["message-id"])
    amount_elected += 1

    return elected_candidate

async def publish_election(channel, elected_candidate, forced):
    thread = channel.get_thread(THREAD_ID)

    if forced:
        content = "# Bonus Gremlin!"
    else:
        content = f"# Gremlin of the Day #{amount_elected}"
    content += f'''
## {f'"{elected_candidate["description"]}"' if elected_candidate["description"] else "*[No description given]*"}
*Submitted by {elected_candidate["author-mention"]}*
||Submit your gremlins in {thread.jump_url}||'''
    
    async with aiohttp.ClientSession() as session:
        async with session.get(elected_candidate["image-url"]) as response:
            buffer = BytesIO(await response.read())

    await channel.send(
        content,
        file = discord.File(
            filename = basename(urlparse(elected_candidate["image-url"]).path),
            fp = buffer
        ),
        suppress_embeds = True
    )

    save_data()

@tasks.loop(time=NOON_EST)
async def publish_candidate():
    if candidates:
        channel = bot.get_channel(GREMLINS_ID)
        elected_candidate = elect_candidate()
        await publish_election(channel, elected_candidate)

    save_data()

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    await bot.tree.sync()

    print("Connected")
    publish_candidate.start()

bot.run(TOKEN)
