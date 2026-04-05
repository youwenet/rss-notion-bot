import os
import feedparser
import requests
from datetime import datetime

# ==============================
# Notion API
# ==============================

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]

NOTION_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ==============================
# 测试RSS（只用一个）
# ==============================

RSS_FEEDS = [
"https://rss.arxiv.org/rss/cs.AI"
]

# ==============================
# 推送到Notion
# ==============================

def push_to_notion(title, abstract, url):

    data = {

        "parent": {"database_id": DATABASE_ID},

        "properties": {

            "Title": {
                "title": [
                    {"text": {"content": title}}
                ]
            },

            "Abstract": {
                "rich_text": [
                    {"text": {"content": abstract[:2000]}}
                ]
            },

            "Source_URL": {
                "url": url
            },

            "Journal": {
                "rich_text":[
                    {"text":{"content": "Test Source"}}
                ]
            },

            "Status":{
                "select":{
                    "name":"Ingested"
                }
            },

            "Published_Date":{
                "date":{
                    "start":datetime.utcnow().isoformat()+"Z"
                }
            },

            "Ingested_At":{
                "date":{
                    "start":datetime.utcnow().isoformat()+"Z"
                }
            },

            "Scanned":{
                "checkbox":False
            }

        }
    }

    response = requests.post(NOTION_URL, headers=HEADERS, json=data)

    print("Status Code:", response.status_code)
    print("Response:", response.text)


# ==============================
# 处理RSS
# ==============================

def process_feed(feed_url):

    print("Scanning RSS:", feed_url)

    feed = feedparser.parse(feed_url)

    if len(feed.entries) == 0:
        print("RSS没有文章")
        return

    entry = feed.entries[0]

    title = entry.get("title","")
    abstract = entry.get("summary","")
    url = entry.get("link","")

    print("\n找到文章:")
    print(title)

    push_to_notion(title, abstract, url)

    print("\n测试完成，只推送1篇文章")


# ==============================
# MAIN
# ==============================

def main():

    print("DATABASE:", DATABASE_ID)

    for feed in RSS_FEEDS:

        process_feed(feed)

        break


if __name__ == "__main__":
    main()
