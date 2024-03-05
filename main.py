from math import ceil
from pytz import timezone
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
ADMIN_ROLE_ID = int(environ.get("ADMIN_ROLE_ID"))
GREMLINS_ID = int(environ.get("GREMLINS_ID"))
THREAD_ID = int(environ.get("THREAD_ID"))
CANDIDATES_PER_PAGE = 10
ACCENT = 0x1199ff
NOON_EST = time(hour=12, tzinfo=timezone("EST"))

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
            "candidates": candidates
        }).encode()))

amount_elected, candidates = load_data()

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
                ephemeral=True
            )

class SetDescriptionView(ui.View):
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

@app_commands.context_menu(name="Add gremlin as candidate")
async def add_as_candidate(interaction, message: discord.Message):
    reply = interaction.response.send_message

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.", ephemeral=True)
        return

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.", ephemeral=True)
        return

    attachment_found = False
    if message.attachments and len(message.attachments) == 1:
        attachment = message.attachments[0]
        if "image" in attachment.content_type:
            attachment_found = True

    if not attachment_found:
        await reply("Gremlin not found. Make sure that the message has one picture.", ephemeral=True)
        return
    
    if any(candidate["message-id"] == message.id for candidate in candidates):
        await reply("This gremlin is already in the list of candidates.", ephemeral=True)
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
        await reply(f"Gremlin added! ID: **`#{index + 1}`**", ephemeral=True)
    else:
        await reply((
            f"Gremlin added! ID: **`#{index + 1}`**"
            "\nIt has no description. Would you like to add one?"
        ), view=SetDescriptionView(index), ephemeral=True)

@app_commands.context_menu(name="Remove gremlin from candidates")
async def remove_from_candidates(interaction, message: discord.Message):
    reply = lambda content: interaction.response.send_message(content, ephemeral=True)

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
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
    reply = lambda content: interaction.response.send_message(content, ephemeral=True)

    if message.channel.id != THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return
    
    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return
    
    candidate_index = next(
        (i for i, candidate in enumerate(candidates) if candidate["message-id"] == message.id),
        None
    )

    if candidate_index is None:
        await reply("This message is not in the list of candidates.")
        return
    
    await interaction.response.send_modal(SetDescriptionModal(candidate_index))

bot.tree.add_command(add_as_candidate)
bot.tree.add_command(remove_from_candidates)
bot.tree.add_command(set_description)

@bot.tree.command(
    name = "gremlincandidates",
    description = "List all gremlin candidates"
)
async def list_candidates(interaction):
    reply = lambda content: interaction.response.send_message(content, ephemeral=True)

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
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
    reply = lambda content: interaction.response.send_message(content, ephemeral=True)

    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not candidates:
        await reply("The list of gremlin candidates is already empty.")
        return
    
    await interaction.response.send_message(
        "Are you sure you want to clear the list of gremlin candidates? **This action is irreversible!**",
        view = ConfirmClearCandidatesView(),
        ephemeral = True
    )

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def elect_candidate():
    global amount_elected, candidates

    if len(candidates) == 1:
        elected_candidate = candidates[0]
        candidates = []
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
    amount_elected += 1

    return elected_candidate

async def publish_election(channel, elected_candidate):
    thread = channel.get_thread(THREAD_ID)
    content = f'''
# Gremlin of the Day #{amount_elected}
## "{elected_candidate["description"]}"
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
