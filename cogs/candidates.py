from discord.ext import commands
from discord import app_commands
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import uiclasses

class Candidates(commands.GroupCog, group_name="candidates"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def interaction_check(self, interaction):
        if not any(role.id == data.config.get("role") for role in interaction.user.roles):
            await interaction.response.send_message("You do not have the necessary permissions.", ephemeral=True)
        else:
            return True

    @app_commands.command(
        name = "list",
        description = "List all gremlin candidates"
    )
    async def list_candidates(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)
        
        if not data.candidates:
            await reply("There are no gremlin candidates to view.")
            return

        await uiclasses.PaginatedCandidatesView().initial_page(interaction)

    @app_commands.command(
        name = "clear",
        description = "Clears all gremlin candidates"
    )
    async def clear_candidates(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not data.candidates:
            await reply("The list of gremlin candidates is already empty.")
            return
        
        await reply(
            "Are you sure you want to clear the list of gremlin candidates? **This action is irreversible!**",
            view = uiclasses.ConfirmClearCandidatesView()
        )
    
    @app_commands.command(
        name = "cleanse",
        description = "Immediately performs the monthly candidate cleanse"
    )
    async def cleanse_candidates(self, interaction):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not data.candidates:
            await reply("The list of gremlin candidates is already empty.")
            return

        cleanse_remainders = data.config.get("cleanseremainders")

        if not cleanse_remainders:
            await reply("The amount of cleanse remainders is set to 0, try clearing instead.")
            return

        if cleanse_remainders >= len(data.candidates):
            await reply("The amount of cleanse remainders is too high to affect the list of current candidates.")
            return

        message = "Are you sure you want to delete all but the newest "
        if cleanse_remainders == 1:
            message += "candidate?"
        else:
            message += f"{cleanse_remainders} candidates?"
        message += " **This action is irreversible!**"

        await reply(
            message,
            view = uiclasses.ConfirmCleanseCandidatesView()
        )
    
    @app_commands.command(
        name = "legacyscan",
        description = "Scans the submissions thread for legacy-reacted gremlins"
    )
    @app_commands.describe(limit="Message limit")
    async def legacy_scan(self, interaction, limit: int):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if limit <= 0:
            await reply("Please input a valid limit.")
            return
        
        await interaction.response.defer(ephemeral=True)

        channel = self.bot.get_channel(data.config.get("elections"))
        thread = channel.get_thread(data.config.get("submissions"))

        amount_added = 0
        total = 0

        async for message in thread.history(limit=limit):
            if data.is_eligible(message)[0]:
                for reaction in message.reactions:
                    if reaction.emoji == "⭐":
                        async for user in reaction.users():
                            if user.id in [466987423046565908, 456226577798135808]:
                                data.add_candidate(message)
                                amount_added += 1

            total += 1
        
        await interaction.followup.send(f"{amount_added} / {total} messages {'was' if amount_added == 1 else 'were'} added.")

async def setup(bot):
    await bot.add_cog(Candidates(bot))
