from discord.ext import commands
import discord
import data

class GremlinBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_reactions = True
        intents.guilds = True
        intents.members = True

        super().__init__(command_prefix="/", intents=intents, application_id=data.APPLICATION_ID)

    async def setup_hook(self):
        await self.load_extension("cogs.contextmenu")
        await self.load_extension("cogs.candidates")
        await self.load_extension("cogs.election")
        await self.load_extension("cogs.config")

bot = GremlinBot()
