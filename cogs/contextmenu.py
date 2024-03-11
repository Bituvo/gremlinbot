from discord.ext import commands
from discord import app_commands
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import utils
import data
import discord
import uiclasses

class ContextMenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name = "Add gremlin as candidate",
                callback = self.add_as_candidate
            )
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name = "Remove gremlin from candidates",
                callback = self.remove_from_candidates
            )
        )
        self.bot.tree.add_command(
            app_commands.ContextMenu(
                name = "Set gremlin description",
                callback = self.set_description
            )
        )

    async def add_as_candidate(self, interaction, message: discord.Message):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not any(role.id == data.config.get("role") for role in interaction.user.roles):
            await reply("You do not have the necessary permissions.")
            return

        if message.channel.id != data.config.get("submissions"):
            await reply("You must be in the gremlin thread.")
            return

        success, why = data.is_eligible(message)
        if not success:
            await reply(why)
            return
        
        indexes = data.add_candidate(message)
        plural = 's' if len(indexes) > 1 else ''
        readable_indexes = f"ID{plural}: **`"
        readable_indexes += f"#{indexes[0] + 1}" if len(indexes) == 1 else f"#{indexes[0] + 1} - #{indexes[-1] + 1}"
        readable_indexes += "`**"

        if message.content:
            await reply(f"Gremlin{plural} added! {readable_indexes}")
        else:
            await reply((
                f"Gremlin{plural} added! {readable_indexes}"
                f"\n{'They have' if plural else 'It has'} no description. Would you like to add one?"
            ), view=uiclasses.AddDescriptionView(indexes))

    async def remove_from_candidates(self, interaction, message: discord.Message):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not any(role.id == data.config.get("role") for role in interaction.user.roles):
            await reply("You do not have the necessary permissions.")
            return

        if message.channel.id != data.config.get("submissions"):
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

    async def set_description(self, interaction, message: discord.Message):
        reply = lambda *args, **kwargs: interaction.response.send_message(*args, ephemeral=True, **kwargs)

        if not any(role.id == data.config.get("role") for role in interaction.user.roles):
            await reply("You do not have the necessary permissions.")
            return

        if message.channel.id != data.config.get("submissions"):
            await reply("You must be in the gremlin thread.")
            return
        
        candidate_indexes = [i for i, candidate in enumerate(data.candidates) if candidate["message-id"] == message.id]

        if not candidate_indexes:
            await reply("This message is not in the list of candidates.")
            return
        
        await interaction.response.send_modal(uiclasses.SetDescriptionModal(candidate_indexes))

async def setup(bot):
    await bot.add_cog(ContextMenu(bot))
