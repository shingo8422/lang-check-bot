from flask import Flask
import threading
from pydantic import BaseModel
import discord
from openai import OpenAI
import json, os

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running"


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class Feedback(BaseModel):
    is_not_natural: bool
    natural_sentence: str
    explanation: str


async def point_out(message, context_message_limit=10):
    context_messages = []

    async for msg in message.channel.history(
        limit=context_message_limit, before=message
    ):
        context_messages.append(f"{msg.author.name}: {msg.content}")
    context_messages.reverse()  # Sort in chronological order

    context_str = "\n".join(context_messages)

    main_message = message.content.replace(":pls_ck:", "")

    prompt_messages = [
        {
            "role": "system",
            "content": """
あなたは日本語と英語の文法と表現をチェックするBot`langcheck-bot`です。
ユーザーが入力した`日本語`または`英語`を分析し、あまりにも不自然な使用方法の場合は，指摘してください。
Discordで使われている文章なので，カジュアルな会話表現は許容してください．
フィードバックや解説は、Discordでわかりやすく表示されるように，強調表示(**)などのデコレーションをうまく使ってください
解説も加えてください．
文脈も考慮して判断してください。
""",
        },
        {
            "role": "user",
            "content": f"以下は直前のメッセージの文脈です：\n{context_str}\n\n次のメッセージを評価してください: '{main_message}'. フィードバックを提供してください。例: {{'is_not_natural': true or false, 'natural_sentence': 'xxx', 'explanation': 'yyy'}}",
        },
    ]

    print(prompt_messages)

    chat_completion = openai_client.beta.chat.completions.parse(
        messages=prompt_messages,
        model="gpt-4o-2024-08-06",
        response_format=Feedback,
    )

    feedback = chat_completion.choices[0].message.parsed

    print(
        f"message: {message}, feedback: {{ is_not_natural: {feedback.is_not_natural}, feedback: {feedback.natural_sentence}, explanation: {feedback.explanation} }}"
    )

    if feedback.is_not_natural:
        pointed_out_channel = discord.utils.get(
            message.guild.channels, name="pointed-out"
        )
        if pointed_out_channel:
            await pointed_out_channel.send(
                f"""
original_message: {main_message}
sender: {message.author.mention}

feedback: {feedback.natural_sentence}
explanation: {feedback.explanation}"""
            )
        else:
            await message.channel.send(
                "'pointed-out' is not found. Contact to Administrator"
            )


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if ":pls_ck:" in message.content:
        await point_out(message)

    if (
        message.reference is not None
        and message.reference.resolved is not None
        and message.reference.resolved.author == client.user
        and message.reference
    ):
        # Process replies to the bot's messages
        await handle_reply(message)


async def handle_reply(message):
    reply_content = message.content
    original_message = message.reference.resolved.content

    response = await generate_reply_response(reply_content, original_message)
    await message.channel.send(response)


async def generate_reply_response(reply_content, original_message):
    chat_completion = openai_client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are a bilingual bot named 'langcheck-bot', fluent in both Japanese and English. Please respond to user questions and replies appropriately and naturally.",
            },
            {"role": "assistant", "content": original_message},
            {"role": "user", "content": reply_content},
        ],
    )
    return chat_completion.choices[0].message.content


def run_discord_bot():
    client.run(os.environ.get("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    threading.Thread(target=run_discord_bot).start()
    app.run(host="0.0.0.0", port=80)
