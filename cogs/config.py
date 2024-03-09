from discord.ext import commands
from discord import app_commands
from datetime import time
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
from data import config
import tasks
import discord

class Config(commands.GroupCog, group_name="config"):
    def __init__(self, bot):
        self.bot = bot
    
    async def interaction_check(self, interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have the necessary permissions.", ephemeral=True)
        else:
            return True

    @app_commands.command(
        name = "elections",
        description = "Set the election channel"
    )
    @app_commands.describe(channel="Election channel")
    async def set_elections_channel(self, interaction, channel: discord.TextChannel):
        config.set(elections=channel.id)

        await interaction.response.send_message(
            f"Gremlin election channel set to {channel.jump_url}.",
            suppress_embeds = True,
            ephemeral = True
        )
    
    @app_commands.command(
        name = "submissions",
        description = "Set the submissions thread"
    )
    @app_commands.describe(thread="Submissions thread")
    async def set_submissions_channel(self, interaction, thread: discord.Thread):
        config.set(submissions=thread.id)

        await interaction.response.send_message(
            f"Gremlin submission channel set to {thread.jump_url}.",
            suppress_embeds = True,
            ephemeral = True
        )

    @app_commands.command(
        name = "role",
        description = "Set the role required to manage gremlins"
    )
    @app_commands.describe(roleid="Role ID")
    async def set_submissions_channel(self, interaction, roleid: str):
        if roleid.isdigit():
            config.set(role=int(roleid))
        else:
            await interaction.response.send_message(
                "Please input a valid role ID.",
                ephemeral = True
            )
            return

        await interaction.response.send_message(
            "Gremlin management role set.",
            ephemeral = True
        )
    
    @app_commands.command(
        name = "election-time",
        description = "Set the daily election time (GMT hour)"
    )
    @app_commands.describe(hour="GMT hour")
    async def set_election_time(self, interaction, hour: int):
        if 0 <= hour <= 24:
            config.set(electionhour=hour)
            tasks.publish_candidate.change_interval(time=time(hour=hour))
        else:
            await interaction.response.send_message(
                "Please input a valid hour.",
                ephemeral = True
            )
            return

        await interaction.response.send_message(
            f"Daily election time set to {hour}:00 GMT.",
            ephemeral = True
        )
    
    @app_commands.command(
        name = "view",
        description = "View current configuration"
    )
    async def view_config(self, interaction):
        config_elections = config.get("elections")
        config_submissions = config.get("submissions")
        config_electionhour = config.get("electionhour")
        config_role = config.get("role")

        embed = discord.Embed(title="Gremlin Bot Configuration")

        embed.add_field(
            name = "Election channel (`elections`)",
            value = f"{config_elections} (<#{config_elections}>)",
            inline = False
        )
        embed.add_field(
            name = "Submission thread (`submissions`)",
            value = f"{config_submissions} (<#{config_submissions}>)",
            inline = False
        )
        embed.add_field(
            name = "Management role (`role`)",
            value = f"{config_role} (<@&{config_role}>)",
            inline = False
        )
        embed.add_field(
            name = "Daily election hour (`electionhour`)",
            value = f"{config_electionhour} (<t:{config_electionhour * 3600}:t>)",
            inline = False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Config(bot))
