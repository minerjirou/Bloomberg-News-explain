import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json
from urllib.request import Request, urlopen

# OpenAI APIキーを設定
api_key = ''  # 自分のAPIキーに置き換えてください

client = OpenAI(api_key=api_key)
# GPT-3.5-Turboモデルを指定
model = "gpt-3.5-turbo"

# RSSフィードのURLを指定
rss_feed_url = 'https://assets.wor.jp/rss/rdf/bloomberg/economy.rdf'
"""
RSSはここのやつを取ってきている
https://rss.wor.jp/
"""
# Discord Webhook URLを設定
webhook_url = ''  # 自分のDiscord Webhook URLに置き換えてください

# Discordに結果を送信する関数
def post_discord(message: str, webhook_url: str):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (private use) Python-urllib/3.10",
    }
    data = {"content": message}
    request = Request(
        webhook_url,
        data=json.dumps(data).encode(),
        headers=headers,
    )

    with urlopen(request) as res:
        assert res.getcode() == 204

# RSSフィードを取得
feed = feedparser.parse(rss_feed_url)

# 記事を逆順で処理し、最新の記事から順に送信
for entry in reversed(feed.entries):
    article_url = entry.link
    print(f"記事のURL: {article_url}")

    # 記事のURLにアクセス
    response = requests.get(article_url)

    if response.status_code == 200:
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')

        # 本文を正確に特定する方法を見つける
        # 例: <div>要素のclass属性が "body-columns" の中のテキストを取得
        div_body_columns = soup.find('div', class_='body-columns')
        if div_body_columns:
            body_text = div_body_columns.get_text()
        else:
            body_text = "本文が見つかりませんでした"

        # 1回目のGPT-3.5-Turbo呼び出し
        prompt_1 = f"以下の記事について、経済アナリストになりきり説明を行うこと:\n\n{body_text}"
        response_1 = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an economic analyst."},
                {"role": "user", "content": prompt_1}
            ],
            max_tokens=650
        )
        response_message_1 = response_1.choices[0].message.content.strip()

        # 2回目のGPT-3.5-Turbo呼び出し
        prompt_2 = "次の内容を200文字以内に日本語で要約する。"
        response_2 = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are summarizing the following text."},
                {"role": "user", "content": prompt_2 + "\n\n" + response_message_1}
            ],
            max_tokens=400
        )
        response_message_2 = response_2.choices[0].message.content.strip()

        # 結果をDiscordに送信
        message = f"記事のURL: {article_url}\n\nGPT-3.5-Turboに経済アナリストになりきって解説してもらった結果:\n{response_message_1}\n\nGPT-3.5-Turboの解説結果を要約した情報:\n{response_message_2}"

        # Discordに結果を送信する関数を呼び出す
        post_discord(message, webhook_url)

    else:
        print(f"Failed to access URL: {article_url}")
    print("\n")
