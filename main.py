from datetime import datetime, timedelta
from random import choices
from urllib.parse import urlparse
from os.path import basename
from io import BytesIO
from discord.ext import tasks, commands
from discord import app_commands
import discord
import aiohttp
import uiclasses
import data

intents = discord.Intents.default()
intents.message_content = True
intents.guild_reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents, application_id=data.APPLICATION_ID)

@app_commands.context_menu(name="Add gremlin as candidate")
async def add_as_candidate(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != data.THREAD_ID:
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
    
    if any(candidate["message-id"] == message.id for candidate in data.candidates):
        await reply("This gremlin is already in the list of candidates.")
        return
    
    if message.id in data.elected_message_ids:
        await reply("This gremlin has already been elected!")
        return
    
    index = len(data.candidates)
    data.candidates.append({
        "image-url": message.attachments[0].url,
        "author-name": message.author.display_name,
        "author-avatar-url": message.author.display_avatar.url,
        "author-mention": message.author.mention,
        "message-url": message.jump_url,
        "message-id": message.id,
        "description": message.content
    })
    data.save_data()

    if message.content:
        await reply(f"Gremlin added! ID: **`#{index + 1}`**")
    else:
        await reply((
            f"Gremlin added! ID: **`#{index + 1}`**"
            "\nIt has no description. Would you like to add one?"
        ), view=uiclasses.AddDescriptionView(index))

@app_commands.context_menu(name="Remove gremlin from candidates")
async def remove_from_candidates(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != data.THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return

    candidate_index = next(
        (i for i, candidate in enumerate(data.candidates) if candidate["message-id"] == message.id),
        None
    )

    if candidate_index is None:
        await reply("This message is not in the list of candidates.")
        return
    
    del data.candidates[candidate_index]
    data.save_data()

    await reply(f"Removed candidate with ID **`{candidate_index + 1}`**.")

@app_commands.context_menu(name="Set gremlin description")
async def set_description(interaction, message: discord.Message):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if message.channel.id != data.THREAD_ID:
        await reply("You must be in the gremlin thread.")
        return
    
    candidate_index = next(
        (i for i, candidate in enumerate(data.candidates) if candidate["message-id"] == message.id),
        None
    )

    if candidate_index is None:
        await reply("This message is not in the list of candidates.")
        return
    
    await interaction.response.send_modal(uiclasses.SetDescriptionModal(candidate_index))

bot.tree.add_command(add_as_candidate)
bot.tree.add_command(remove_from_candidates)
bot.tree.add_command(set_description)

@bot.tree.command(
    name = "gremlincandidates",
    description = "List all gremlin candidates"
)
async def list_candidates(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return
    
    if not data.candidates:
        await reply("There are no gremlin candidates to view.")
        return

    await uiclasses.PaginatedCandidatesView().initial_page(interaction)

@bot.tree.command(
    name = "clearcandidates",
    description = "Clears all gremlin candidates"
)
async def clear_candidates(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not data.candidates:
        await reply("The list of gremlin candidates is already empty.")
        return
    
    await reply(
        "Are you sure you want to clear the list of gremlin candidates? **This action is irreversible!**",
        view = uiclasses.ConfirmClearCandidatesView()
    )

@bot.tree.command(
    name = "clearelected",
    description = "Clears the internal list of elected gremlins"
)
async def clear_elected(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not data.elected_message_ids:
        await reply("The list of elected gremlins is already empty.")
        return
    
    await reply(
        "Are you sure you want to clear the list of elected gremlins?\n" + 
        "***This action is irreversible!*** The day count will reset to 0, and **double elections can occur!**",
        view = uiclasses.ConfirmClearElectedView()
    )

@bot.tree.command(
    name = "forceelection",
    description = "Forces an election to occur"
)
async def force_election(interaction):
    reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

    if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
        await reply("You do not have the necessary permissions.")
        return

    if not data.candidates:
        await reply("There are no gremlin candidates.")
        return
    
    await publish_candidate(forced=True)
    await reply("Bonus gremlin posted!")

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def elect_candidate():
    if len(data.candidates) == 1:
        elected_candidate = data.candidates.pop(0)
        data.elected_message_ids.append(elected_candidate["message-id"])

        return elected_candidate

    message_ids = [candidate["message-id"] for candidate in data.candidates]
    delta = max(message_ids) - min(message_ids)
    weights = [weight_function((message_id - min(message_ids)) / delta) for message_id in message_ids]

    elected_candidate_index = choices(
        population = range(len(data.candidates)),
        weights = weights
    )[0]

    elected_candidate = data.candidates.pop(elected_candidate_index)
    data.elected_message_ids.append(elected_candidate["message-id"])

    return elected_candidate

async def publish_election(channel, elected_candidate, forced):
    global amount_elected

    thread = channel.get_thread(data.THREAD_ID)

    if forced:
        content = "# Bonus Gremlin!"
    else:
        amount_elected += 1
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

def monthly_candidate_cleanse():
    now = datetime.now()
    current_month = now.month
    if (now + timedelta(days=1)).month != current_month:
        data.candidates = sorted(data.candidates, key=lambda candidate: candidate["message-id"])[-5:]

@tasks.loop(time=data.NOON_EST)
async def publish_candidate(forced=False):
    if data.candidates:
        channel = bot.get_channel(data.GREMLINS_ID)
        elected_candidate = elect_candidate()
        await publish_election(channel, elected_candidate, forced)

    monthly_candidate_cleanse()

    data.save_data()

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    await bot.tree.sync()

    print("Connected")
    publish_candidate.start()

bot.run(data.TOKEN)
