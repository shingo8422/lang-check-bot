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

async def point_out(message):
    chat_completion = openai_client.beta.chat.completions.parse(
        messages=[
            {
                "role": "system",
                "content": """
あなたは日本語と英語の文法と表現をチェックする専門家です。
ユーザーが入力した`日本語`または`英語`を分析し、あまりにも不自然な使用方法の場合は，指摘してください。
Discordで使われている文章なので，多少くだけたカジュアルな内容は許容してください．
natural_sentenceには，`:pls_ck:`という文字列を含めないでください．
フィードバックや解説は、Discordでわかりやすく表示されるように，強調表示(**)などのデコレーションをうまく使ってください
解説も加えてください．
"""
            },
            {
                "role": "user",
                "content": f"Please evaluate the following message: '{message.content}'. Provide feedback. Example: {{'is_not_natural': true or false, 'feedback': 'natural_sentence': 'xxx', 'explanation': 'yyy'}}",
            }
        ],
        model="gpt-4o-2024-08-06",
        response_format=Feedback,
    )

    feedback = chat_completion.choices[0].message.parsed

    print(f"message: {message}, feedback: {{ is_not_natural: {feedback.is_not_natural}, feedback: {feedback.natural_sentence}, explanation: {feedback.explanation} }}")
    # 不自然な表現がある場合にフィードバックを送信
    if feedback.is_not_natural:
        pointed_out_channel = discord.utils.get(message.guild.channels, name='pointed-out')
        if pointed_out_channel:
            await pointed_out_channel.send(f"""
original_message: {message.content.replace(":pls_ck:", "")}
sender: {message.author.mention}

feedback: {feedback.natural_sentence}
explanation: {feedback.explanation}""")
        else:
            await message.channel.send("'pointed-out' is not found.Contact to Administrator")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if ":pls_ck:" in message.content:
        await point_out(message)

client.run(os.environ.get("DISCORD_BOT_TOKEN"))
