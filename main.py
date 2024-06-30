from i18n import load_path, set as i18n_set, t
from locale import getlocale as locale_getlocale
from dotenv import load_dotenv
from os import getenv
from discord import ApplicationContext, Bot, Intents, Message
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from collections import deque


def getlocale() -> str:
    locale = locale_getlocale()[0]
    if locale is None:
        return "en"
    elif locale.startswith(("ja_", "Japanese_")):
        return "ja"
    else:
        return "en"


load_path.append("translations")
i18n_set("filename_format", "{locale}.{format}")
i18n_set("locale", getlocale())
i18n_set("fallback", "en")

load_dotenv()

intents = Intents.default()
intents.message_content = True

bot = Bot(intents=intents)
ai = OpenAI()


class Context:
    # system + 30 * (user + assistant)
    MAX_CONTEXT_LENGTH = 61

    SYSTEM_PROMPT: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": t("SYSTEM_PROMPT"),
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
            self.initialize(channel_id)
        self.messages[channel_id].append(message)

    def get(
        self, channel_id: int
    ) -> list[
        ChatCompletionAssistantMessageParam
        | ChatCompletionSystemMessageParam
        | ChatCompletionUserMessageParam
    ]:
        return list(self.messages[channel_id])

    def initialize(self, channel_id: int):
        self.messages[channel_id] = deque(
            maxlen=Context.MAX_CONTEXT_LENGTH,
        )
        self.messages[channel_id].append(Context.SYSTEM_PROMPT)

    def print(self, channel_id: int):
        print(f"{channel_id}: {self.messages[channel_id]}")

    def reset(self, channel_id: int):
        if channel_id in self.messages:
            del self.messages[channel_id]


context = Context()


@bot.event
async def on_ready():
    print(t("%{name} is ready and online!", name=bot.user))


@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    if message.author.bot:
        return

    prompt = message.content

    user_prompt: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": prompt,
    }
    context.add(message.channel.id, user_prompt)

    messages = context.get(message.channel.id)
    completion = ai.chat.completions.create(
        model="gpt-4o",
        messages=[
            *messages,
            user_prompt,
        ],
    )
    m = completion.choices[0].message
    content = m.content
    assistant_prompt: ChatCompletionAssistantMessageParam = {
        "role": "assistant",
        "content": content,
    }
    context.add(message.channel.id, assistant_prompt)

    context.print(message.channel.id)

    await message.channel.send(content)


@bot.slash_command(name="chat", description=t("Chat with GPT-4o"))
@bot.slash_command(name="c", description=t("Chat with GPT-4o"))
async def chat(ctx: ApplicationContext, prompt: str):
    await ctx.defer()

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


@bot.slash_command(name="reset", description=t("Reset the context"))
@bot.slash_command(name="r", description=t("Reset the context"))
async def reset(ctx: ApplicationContext):
    context.reset(ctx.channel_id)

    await ctx.respond(t("The context has been reset."))


token = getenv("TOKEN")
bot.run(token)
