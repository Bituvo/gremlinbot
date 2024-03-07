from discord.ext import tasks
from os import path
from datetime import datetime, timedelta
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import elections
import bot

def monthly_candidate_cleanse():
    now = datetime.now()
    current_month = now.month
    if (now + timedelta(days=1)).month != current_month:
        data.candidates = sorted(data.candidates, key=lambda candidate: candidate["message-id"])[-5:]

@tasks.loop(time=data.NOON_EST)
async def publish_candidate(forced=False):
    if data.candidates:
        channel = bot.bot.get_channel(data.GREMLINS_ID)
        elected_candidate = elections.elect_candidate()
        await elections.publish_election(channel, elected_candidate, forced)

    monthly_candidate_cleanse()

    data.save_data()
