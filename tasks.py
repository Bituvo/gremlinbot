from discord.ext import tasks
from datetime import time, timezone
import data
import utils
import elections
import bot

sorting_function = lambda candidate: candidate["message-id"]

def cleanse_candidates(remainders):
    sorted_candidates = sorted(data.candidates, key=sorting_function)
    data.candidates = sorted_candidates[-remainders:]

def check_for_cleanse():
    if not data.config.get("monthlycleanse"):
        return

    if utils.is_last_day_of_month():
        remainders = data.config.get("cleanseremainders")

        if remainders:
            cleanse_candidates(remainders)

hour = data.config.get("electionhour", 17)
minute = data.config.get("electionminute", 0)
@tasks.loop(time=[time(hour=hour, minute=minute, tzinfo=timezone.utc)])
async def publish_candidate(forced=False):
    if data.candidates:
        channel = bot.bot.get_channel(data.config.get("elections"))
        elected_candidate = elections.elect_candidate()
        await elections.publish_election(channel, elected_candidate, forced)

    check_for_cleanse()

    data.save_data()
