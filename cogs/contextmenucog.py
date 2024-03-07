from discord.ext import commands
from discord import app_commands
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
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

    async def remove_from_candidates(self, interaction, message: discord.Message):
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

    async def set_description(self, interaction, message: discord.Message):
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

async def setup(bot):
    await bot.add_cog(ContextMenu(bot))
