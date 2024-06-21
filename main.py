from dotenv import load_dotenv
from os import getenv
from discord import ApplicationContext, Bot
from openai import OpenAI

load_dotenv()

bot = Bot()
ai = OpenAI()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="chat", description="Chat with GPT-4o")
async def chat(ctx: ApplicationContext, prompt: str):
    completion = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    message = completion.choices[0].message
    content = message.content
    await ctx.respond(content)


token = getenv("TOKEN")
bot.run(token)
