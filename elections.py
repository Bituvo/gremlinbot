from random import choices
from io import BytesIO
import data
import utils
import discord
import aiohttp

def elect_candidate():
    if len(data.candidates) == 1:
        elected_candidate = data.candidates.pop(0)
        data.elected_message_ids.append(elected_candidate["message-id"])

        return elected_candidate

    message_ids = [candidate["message-id"] for candidate in data.candidates]
    delta = (max(message_ids) - min(message_ids)) or 1
    weights = [utils.weight_function((message_id - min(message_ids)) / delta) for message_id in message_ids]

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
        content = "# Bonus Gremlin!\n"
    else:
        data.day_count += 1
        content = f"# Gremlin of the Day #{data.day_count}\n"
    
    if elected_candidate["description"]:
        content += f"## {f'"{elected_candidate["description"]}"'}\n"

    content += (f"*Submitted by {elected_candidate["author-mention"]}*\n" +
                f"||Submit your gremlins in {thread.jump_url}||")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(elected_candidate["content-url"]) as response:
            buffer = BytesIO(await response.read())

    await channel.send(
        content,
        file = discord.File(
            filename = elected_candidate["filename"],
            fp = buffer
        ),
        suppress_embeds = True
    )
