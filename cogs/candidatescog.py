from discord.ext import commands
from discord import app_commands
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import uiclasses
import tasks

class Candidates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name = "gremlincandidates",
        description = "List all gremlin candidates"
    )
    async def list_candidates(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not any(role.id == data.ROLE_ID for role in interaction.user.roles):
            await reply("You do not have the necessary permissions.")
            return
        
        if not data.candidates:
            await reply("There are no gremlin candidates to view.")
            return

        await uiclasses.PaginatedCandidatesView().initial_page(interaction)

    @app_commands.command(
        name = "clearcandidates",
        description = "Clears all gremlin candidates"
    )
    async def clear_candidates(self, interaction):
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

async def setup(bot):
    await bot.add_cog(Candidates(bot))
