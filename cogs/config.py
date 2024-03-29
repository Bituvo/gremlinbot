from discord.ext import commands
from discord import app_commands
from datetime import time, timezone
from os import path
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
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
        data.config.set(elections=channel.id)

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
        data.config.set(submissions=thread.id)

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
    async def set_role_id(self, interaction, roleid: str):
        if roleid.isdigit():
            data.config.set(role=int(roleid))
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
        description = "Set the daily election time (GMT)"
    )
    @app_commands.describe(hour="Hour")
    @app_commands.describe(minute="Minute")
    async def set_election_time(self, interaction, hour: int, minute: int):
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            data.config.set(electionhour=hour)
            data.config.set(electionminute=minute)
            tasks.publish_candidate.change_interval(time=[time(hour=hour, minute=minute, tzinfo=timezone.utc)])
        else:
            await interaction.response.send_message(
                "Please input a valid time.",
                ephemeral = True
            )
            return

        await interaction.response.send_message(
            f"Daily election time set to {hour}:{minute} GMT.",
            ephemeral = True
        )

    @app_commands.command(
        name = "monthlycleanse",
        description = "Enable or disable monthly candidate cleanse"
    )
    @app_commands.describe(option="Option ('enable' or 'disable')")
    async def toggle_monthly_cleanse(self, interaction, option: str):
        option = option.lower()

        if "enable" in option or "disable" in option:
            data.config.set(monthlycleanse=(1 if "enable" in option else 0))
        else:
            await interaction.response.send_message(
                "Please input a valid option.",
                ephemeral = True
            )
            return

        await interaction.response.send_message(
            f"Monthly candidate cleanse {'enabled' if 'enable' in option else 'disabled'}.",
            ephemeral = True
        )

    @app_commands.command(
        name = "cleanseremainders",
        description = "Set how many of the newest candidates remain after the monthly cleanse"
    )
    @app_commands.describe(remainders="Amount of newest candidates to keep")
    async def set_cleanse_remainders(self, interaction, remainders: int):
        if remainders >= 0:
            data.config.set(cleanseremainders=remainders)
        else:
            await interaction.response.send_message(
                "Please input a valid option.",
                ephemeral = True
            )
            return

        message = f"Monthly cleanse remainder count set to {remainders}."
        message += (" (Monthly cleanse is disabled)" if not data.config.get("monthlycleanse") else "")
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(
        name = "view",
        description = "View current configuration"
    )
    async def view_config(self, interaction):
        config_elections = data.config.get("elections")
        config_submissions = data.config.get("submissions")
        config_electionhour = data.config.get("electionhour")
        config_electionminute = data.config.get("electionminute")
        config_role = data.config.get("role")
        config_monthlycleanse = data.config.get("monthlycleanse")
        config_cleanseremainders = data.config.get("cleanseremainders")

        embed = discord.Embed(title="Gremlin Bot Configuration", color=data.ACCENT)

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
            name = "Daily election time",
            value = f"{config_electionhour}:{config_electionminute} GMT",
            inline = False
        )
        embed.add_field(
            name = "Monthly cleanse (`monthlycleanse`)",
            value = f"{config_monthlycleanse} ({'Enabled' if config_monthlycleanse else 'Disabled'})",
            inline = False
        )
        embed.add_field(
            name = "Cleanse remainders (`cleanseremainders`)",
            value = f"{config_cleanseremainders} {'post' if config_cleanseremainders == 1 else 'posts'}",
            inline = False
        )
        embed.add_field(
            name = "Current day count",
            value = f"{data.day_count} {'day' if data.day_count == 1 else 'days'}",
            inline = False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Config(bot))
