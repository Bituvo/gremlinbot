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
        config.set(role=int(roleid))

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
        config.set(electionhour=hour)
        tasks.publish_candidate.change_interval(time=time(hour=hour))

        await interaction.response.send_message(
            f"Daily election time set to {hour}:00 GMT.",
            ephemeral = True
        )

async def setup(bot):
    await bot.add_cog(Config(bot))
