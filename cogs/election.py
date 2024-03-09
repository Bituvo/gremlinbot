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
    
    async def interaction_check(self, interaction):
        if not any(role.id == data.config.get("role") for role in interaction.user.roles):
            await interaction.response.send_message("You do not have the necessary permissions.", ephemeral=True)
        else:
            return True

    @app_commands.command(
        name = "clear",
        description = "Clears the internal list of elected gremlins"
    )
    async def clear_elected(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not data.elected_message_ids:
            await reply("The list of elected gremlins is already empty.")
            return
        
        await reply(
            "Are you sure you want to clear the list of elected gremlins?\n" + 
            "***This action is irreversible!*** The day count will reset to 0, and **double elections can occur!**",
            view = uiclasses.ConfirmClearElectedView()
        )

    @app_commands.command(
        name = "bonus",
        description = "Forces an election to occur"
    )
    async def force_election(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not data.candidates:
            await reply("There are no gremlin candidates.")
            return
    
        await interaction.response.defer(ephemeral=True)
        await tasks.publish_candidate(forced=True)

        await interaction.followup.send("Bonus gremlin posted!")
    
    @app_commands.command(
        name = "daycount",
        description = "Get and set the current day count"
    )
    async def elected_amount(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        await reply(f"Day count: **`{data.day_count}`**", view=uiclasses.SetAmountElectedView())

async def setup(bot):
    await bot.add_cog(Election(bot))
