from os import path
from random import choices
from io import BytesIO
from os.path import basename
from urllib.parse import urlparse
import sys
sys.path.insert(1, path.join(sys.path[0], ".."))
import data
import discord
import aiohttp

weight_function = lambda x: max(-4 * x ** 2 + 0.6, 0.5 * (x + 0.3) ** 2)

def elect_candidate():
    if len(data.candidates) == 1:
        elected_candidate = data.candidates.pop(0)
        data.elected_message_ids.append(elected_candidate["message-id"])

        return elected_candidate

    message_ids = [candidate["message-id"] for candidate in data.candidates]
    delta = max(message_ids) - min(message_ids)
    weights = [weight_function((message_id - min(message_ids)) / delta) for message_id in message_ids]

    elected_candidate_index = choices(
        population = range(len(data.candidates)),
        weights = weights
    )[0]

    elected_candidate = data.candidates.pop(elected_candidate_index)
    data.elected_message_ids.append(elected_candidate["message-id"])

    return elected_candidate

async def publish_election(channel, elected_candidate, forced):
    thread = channel.get_thread(data.config.get("submissions"))

    if forced:
        content = "# Bonus Gremlin!"
    else:
        data.amount_elected += 1
        content = f"# Gremlin of the Day #{data.amount_elected}"
    content += f'''
## {f'"{elected_candidate["description"]}"' if elected_candidate["description"] else "*[No description given]*"}
*Submitted by {elected_candidate["author-mention"]}*
||Submit your gremlins in {thread.jump_url}||'''
    
    async with aiohttp.ClientSession() as session:
        async with session.get(elected_candidate["image-url"]) as response:
            buffer = BytesIO(await response.read())

    await channel.send(
        content,
        file = discord.File(
            filename = basename(urlparse(elected_candidate["image-url"]).path),
            fp = buffer
        ),
        suppress_embeds = True
    )
