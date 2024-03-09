from discord.ext import tasks
from os import path
from datetime import datetime, timedelta, time
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import elections
import bot

sorting_function = lambda candidate: candidate["message-id"]

def cleanse_candidates(remainders):
    sorted_candidates = sorted(data.candidates, key=sorting_function)
    data.candidates = sorted_candidates[-remainders:]

def check_for_cleanse():
    if not data.config.get("monthlycleanse"):
        return

    now = datetime.now()
    current_month = now.month
    if (now + timedelta(days=1)).month != current_month:
        remainders = data.config.get("cleanseremainders")

        if remainders:
            cleanse_candidates(remainders)

@tasks.loop(time=time(hour=data.config.get("electionhour", 17)))
async def publish_candidate(forced=False):
    if data.candidates:
        channel = bot.bot.get_channel(data.config.get("elections"))
        elected_candidate = elections.elect_candidate()
        await elections.publish_election(channel, elected_candidate, forced)

    check_for_cleanse()

    data.save_data()
