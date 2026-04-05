import os
import feedparser
import requests
from datetime import datetime

# -------------------------
# 读取 Notion Key & Database
# -------------------------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")

NOTION_URL = "https://api.notion.com/v1/pages"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# -------------------------
# RSS 源列表 (示例)
# -------------------------
RSS_FEEDS = [
    "https://arxiv.org/rss/cs",
    "https://arxiv.org/rss/stat",
    "https://arxiv.org/rss/econ",
    # 后续加入剩余 50 个 RSS
]

# -------------------------
# 遍历 RSS
# -------------------------
for feed_url in RSS_FEEDS:
    print(f"\n📡 Processing RSS feed: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print("⚠️ No entries found in this feed.")
            continue

        # 取第一条文章
        entry = feed.entries[0]
        title = entry.get("title", "No Title")
        summary = entry.get("summary", "")
        link = entry.get("link", "")

        # 忽略摘要少于 150 个词的文章
        if len(summary.split()) < 150:
            print(f"⚠️ Skipping article, summary too short ({len(summary.split())} words).")
            continue

        # 构建 Notion payload
        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Abstract": {"rich_text": [{"text": {"content": summary}}]},
                "Source_URL": {"url": link},
                "Status": {"select": {"name": "New"}},
                "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}}
            }
        }

        # 推送到 Notion
        response = requests.post(NOTION_URL, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        print(f"✅ Article pushed successfully: {title}")
        print(response.json())

        # 只测试第一条，推送成功后 break
        break

    except requests.exceptions.RequestException as e:
        print(f"❌ Network/HTTP error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
