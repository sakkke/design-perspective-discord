from dotenv import load_dotenv
from os import getenv
from discord import ApplicationContext, Bot

load_dotenv()

bot = Bot()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="hello", description="Say hello to the bot")
async def hello(ctx: ApplicationContext):
    await ctx.respond("Hey!")


token = getenv("TOKEN")
bot.run(token)
