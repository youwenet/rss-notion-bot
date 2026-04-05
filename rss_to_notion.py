# rss_to_notion.py
import os
import requests
import feedparser
from datetime import datetime

# ===== 配置 =====
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")

RSS_FEEDS = [
    "https://arxiv.org/rss/cs.LG",
    "https://www.nature.com/nature.rss",
    # 你可以继续加 RSS 链接
]

MIN_ABSTRACT_WORDS = 20  # 摘要词数门槛

# ===== Notion API 写入函数 =====
def create_notion_page(title, abstract, url, journal, published_date, rss_tag):
    notion_url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
            "Source_URL": {"url": url},
            "Journal": {"rich_text": [{"text": {"content": journal}}]},
            "Published_Date": {"date": {"start": published_date}},
            "RSS_Feed_Tag": {"select": {"name": rss_tag}},
            "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}},
            "Scanned": {"checkbox": False},
        }
    }

    response = requests.post(notion_url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 成功写入 Notion: {title}")
    else:
        print(f"❌ 写入失败: {response.status_code} {response.text}")

# ===== RSS 解析函数 =====
def fetch_rss_articles(rss_url, rss_tag):
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        abstract = entry.get("summary", "") or entry.get("description", "")
        word_count = len(abstract.split())
        if word_count >= MIN_ABSTRACT_WORDS:
            title = entry.get("title", "No Title")
            url = entry.get("link", "")
            journal = rss_tag  # 简单用 RSS tag 作为 Journal
            published_date = entry.get("published", datetime.utcnow().isoformat())
            create_notion_page(title, abstract, url, journal, published_date, rss_tag)
            break  # 只写入一条，测试模式
    else:
        print(f"⚠️ RSS 没有符合条件的文章: {rss_tag}")

# ===== 主函数 =====
def main():
    for rss_url in RSS_FEEDS:
        tag = rss_url.split("//")[-1].split("/")[0]
        print(f"🔎 处理 RSS 源: {rss_url} (tag={tag})")
        fetch_rss_articles(rss_url, tag)

if __name__ == "__main__":
    main()
