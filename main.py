from dotenv import load_dotenv
from os import getenv
from discord import ApplicationContext, Bot
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from collections import deque

load_dotenv()

bot = Bot()
ai = OpenAI()


class Context:
    # system + 30 * (user + assistant)
    MAX_CONTEXT_LENGTH = 61

    SYSTEM_PROMPT: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": "You are a assistant.",
    }

    messages: dict[
        int,
        deque[
            ChatCompletionAssistantMessageParam
            | ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
        ],
    ]

    def __init__(self):
        self.messages = {}

    def add(
        self,
        channel_id: int,
        message: (
            ChatCompletionAssistantMessageParam
            | ChatCompletionSystemMessageParam
            | ChatCompletionUserMessageParam
        ),
    ):
        if channel_id not in self.messages:
            self.messages[channel_id] = deque(
                maxlen=Context.MAX_CONTEXT_LENGTH,
            )
            self.messages[channel_id].append(Context.SYSTEM_PROMPT)
        self.messages[channel_id].append(message)

    def get(
        self, channel_id: int
    ) -> list[
        ChatCompletionAssistantMessageParam
        | ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
    ]:
        return list(self.messages[channel_id])

    def print(self, channel_id: int):
        print(f"{channel_id}: {self.messages[channel_id]}")


context = Context()


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(name="chat", description="Chat with GPT-4o")
async def chat(ctx: ApplicationContext, prompt: str):
    user_prompt: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": prompt,
    }
    context.add(ctx.channel_id, user_prompt)

    messages = context.get(ctx.channel_id)
    completion = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            *messages,
            user_prompt,
        ],
    )
    message = completion.choices[0].message
    content = message.content
    assistant_prompt: ChatCompletionAssistantMessageParam = {
        "role": "assistant",
        "content": content,
    }
    context.add(ctx.channel_id, assistant_prompt)

    context.print(ctx.channel_id)

    await ctx.respond(content)


token = getenv("TOKEN")
bot.run(token)
