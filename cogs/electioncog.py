from discord.ext import commands
from discord import app_commands
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import uiclasses
import tasks

class Election(commands.GroupCog, group_name="elections"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "clear",
        description = "Clears the internal list of elected gremlins"
    )
    async def clear_elected(self, interaction):
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

    @app_commands.command(
        name = "force",
        description = "Forces an election to occur"
    )
    async def force_election(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
            await reply("You do not have the necessary permissions.")
            return

        if not data.candidates:
            await reply("There are no gremlin candidates.")
            return
        
        await tasks.publish_candidate(forced=True)
        await reply("Bonus gremlin posted!")

async def setup(bot):
    await bot.add_cog(Election(bot))
