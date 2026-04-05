import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# ========== 核心：强制降低门槛，必发送 1 条 ==========
MIN_WORD_COUNT = 10  # 超级低门槛
SEND_ONLY_ONE = True
# ====================================================

requests.adapters.DEFAULT_RETRIES = 1
SESSION = requests.Session()
SESSION.timeout = 15

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

RSS_FEEDS = [
    "https://arxiv.org/rss/cs.AI",
    "https://www.nature.com/nature.rss",
]

def clean_text(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(strip=True)

def count_words(text):
    return len(text.split())

def get_rss_feed_tag(feed_url):
    if "arxiv.org" in feed_url:
        return "arXiv"
    elif "nature.com" in feed_url:
        return "Nature"
    return "Custom"

def send_to_notion(entry, feed_tag):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "Test Title")[:150]
    abstract = clean_text(entry.get("summary", ""))[:1500]
    source_url = entry.get("link", "")
    ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
            "Source_URL": {"url": source_url},
            "RSS_Feed_Tag": {"select": {"name": feed_tag}},
            "Scanned": {"checkbox": False},
            "Status": {"select": {"name": "Ingested"}},
            "Ingested_At": {"date": {"start": ingested_at}}
        }
    }

    try:
        r = SESSION.post(url, headers=headers, json=data)
        print(f"✅ NOTION 状态码: {r.status_code}")
        return r.status_code in (200, 201)
    except:
        print("❌ 发送失败")
        return False

def main():
    print("🚀 开始运行 RSS 抓取...")
    print(f"NOTION_API_KEY 存在: {bool(NOTION_API_KEY)}")
    print(f"DATABASE_ID 存在: {bool(DATABASE_ID)}")

    if not NOTION_API_KEY or not DATABASE_ID:
        print("❌ 密钥未配置")
        return

    sent = False
    for feed_url in RSS_FEEDS:
        if sent: break
        feed = feedparser.parse(feed_url)
        tag = get_rss_feed_tag(feed_url)

        for entry in feed.entries[:10]:
            wc = count_words(clean_text(entry.get("summary", "")))
            print(f"词数: {wc} | {entry.get('title')[:50]}")

            # 强制发送第一条，不管词数
            print("✅ 强制发送第一条测试！")
            if send_to_notion(entry, tag):
                print("🎉 成功发到 NOTION！")
                return

    print("ℹ️ 结束")

if __name__ == "__main__":
    main()
