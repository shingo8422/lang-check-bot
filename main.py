from pydantic import BaseModel
import discord
from openai import OpenAI
import json, os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class Feedback(BaseModel):
    is_not_natural: bool
    natural_sentence: str
    explanation: str

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not ":react:" in message.content:
        return

    chat_completion = openai_client.beta.chat.completions.parse(
        messages=[
            {
                "role": "system",
                "content": """
あなたは日本語と英語の文法と表現をチェックする専門家です。
ユーザーが入力した`日本語`または`英語`を分析し、あまりにも不自然な使用方法の場合は，指摘してください。
Discordで使われている文章なので，多少くだけたカジュアルな内容は許容してください．
natural_sentenceからは，`:react:`という文字列を含めないでください．
フィードバックや解説は、Discordでわかりやすく表示されるように，強調表示，斜め文字，引用のデコレーションをうまく使ってください
解説も加えてください．
"""
            },
            {
                "role": "user",
                "content": f"Please evaluate the following message: '{message.content}'. Provide feedback. Example: {{'is_not_natural': true or false, 'feedback': 'natural_sentence: **xxx**', explanation: yyy}}",
            }
        ],
        model="gpt-4o-2024-08-06",
        response_format=Feedback,
    )

    feedback = chat_completion.choices[0].message.parsed

    print(f"message: {message}, feedback: {{ is_not_natural: {feedback.is_not_natural}, feedback: {feedback.natural_sentence}, explanation: {feedback.explanation} }}")

    # 不自然な表現がある場合にフィードバックを送信
    if feedback.is_not_natural:
        await message.channel.send(f"""
**feedback**: {feedback.natural_sentence}
**explanation**: {feedback.explanation}""")

client.run(os.environ.get("DISCORD_BOT_TOKEN"))
