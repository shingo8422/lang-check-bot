from flask import Flask
import threading
from pydantic import BaseModel
import discord
from openai import OpenAI
import os
import tempfile
import random

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
    alternative_expression: str


async def point_out(message, context_message_limit=10):
    context_messages = []

    async for msg in message.channel.history(
        limit=context_message_limit, before=message
    ):
        context_messages.append(f"{msg.author.name}: {msg.content}")
    context_messages.reverse()  # Sort in chronological order

    context_str = "\n".join(context_messages)

    main_message = message.content.replace(":pls_ck:", "").replace(
        "<1276158789220958258>", ""
    )

    prompt_messages = [
        {
            "role": "system",
            "content": """
あなたは日本語と英語の文法と表現をチェックするBot`langcheck-bot`です。
ユーザーが入力した`日本語`または`英語`を分析し、あまりにも不自然な使用方法の場合は，指摘してください。
Discordで使われている文章なので，カジュアルな会話表現は`不自然`判定しないでください．
また，シングルクォーテーションを忘れていたり，先頭の文字を大文字にするの忘れている等の細かいミスは`不自然`判定しないでください．
フィードバックや解説は、Discordでわかりやすく表示されるように，強調表示(**)などのデコレーションをうまく使ってください
解説も加えてください．
文脈も考慮して判断してください。
文章が正しい場合は、その旨を通知してください。
また，文章が正しい場合は，別の言い回し('alternative_expression')も教えてください．
""",
        },
        {
            "role": "user",
            "content": f"以下は直前のメッセージの文脈です：\n{context_str}\n\n次のメッセージを評価してください: '{main_message}'. フィードバックを提供してください。例: {{'is_not_natural': true or false, 'natural_sentence': 'xxx', 'explanation': 'yyy', 'alternative_expression': 'zzz'}}",
        },
    ]

    print(prompt_messages)

    chat_completion = openai_client.beta.chat.completions.parse(
        messages=prompt_messages,
        model="gpt-4o-2024-08-06",
        response_format=Feedback,
        max_tokens=3000,
    )

    feedback = chat_completion.choices[0].message.parsed

    print(
        f"message: {message}, feedback: {{ is_not_natural: {feedback.is_not_natural}, feedback: {feedback.natural_sentence}, explanation: {feedback.explanation} }}"
    )

    pointed_out_channel = discord.utils.get(message.guild.channels, name="pointed-out")
    if pointed_out_channel:
        if feedback.is_not_natural:
            await pointed_out_channel.send(
                f"""
original_message: {main_message}
sender: {message.author.mention}

feedback: {feedback.natural_sentence}
explanation: {feedback.explanation}"""
            )
        else:
            await pointed_out_channel.send(
                f"""
sender: {message.author.mention}

Congratulations! Your sentence is natural and correct.
original_message: {main_message}
alternative_expression: {feedback.alternative_expression}"""
            )
            await message.add_reaction("👍")
    else:
        await message.channel.send(
            "'pointed-out' チャンネルが見つかりません。管理者に連絡してください。"
        )


# 音声のリストを定義
VOICE_LIST = [
    "alloy",
    # "onyx"
]


async def voice_out(message):
    main_message = message.content.replace("<:pls_vo:1276968827477037137>", "").strip()

    # ランダムに音声を選択
    selected_voice = random.choice(VOICE_LIST)

    # テキストを音声に変換
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice=selected_voice,
        input=main_message,
    )

    # 一時ファイルを作成して音声データを保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name

    # voicesチャンネルを取得
    voices_channel = discord.utils.get(message.guild.channels, name="voices")

    if voices_channel:
        # 音声ファイルを送信
        await voices_channel.send(
            f"sender: {message.author.mention}\nvoice: {selected_voice}",
            file=discord.File(temp_file_path, filename="voice_message.mp3"),
        )
        # 一時ファイルを削除
        os.unlink(temp_file_path)
    else:
        await message.channel.send(
            "'voices' チャンネルが見つかりません。管理者に連絡してください。"
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

    if ":pls_vo:" in message.content:
        print(f"voice_message: {message.content}")
        await voice_out(message)

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
