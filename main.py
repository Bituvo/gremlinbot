import discord
import tasks
import data
import bot

@bot.bot.event
async def on_ready():
    await bot.bot.change_presence(status=discord.Status.online)
    await bot.bot.tree.sync()

    print("Connected")
    tasks.publish_candidate.start()

bot.bot.run(data.TOKEN)
