import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# 强制发第一条，不做任何判断
FORCE_SEND_FIRST = True

# 超时防卡死
requests.adapters.DEFAULT_RETRIES = 0
SESSION = requests.Session()
SESSION.timeout = 10

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

# 只留一个最稳的 RSS
RSS_FEEDS = ["https://arxiv.org/rss/cs.AI"]

# ==========================================

def clean_text(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(strip=True)

def send_to_notion(entry):
    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "TEST 标题")[:100]
    abstract = clean_text(entry.get("summary", ""))[:1000]
    source_url = entry.get("link", "")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 极简到不能再极简的字段
    data = {
        "parent": { "database_id": DATABASE_ID },
        "properties": {
            "Title": {
                "title": [{ "text": { "content": title } }]
            },
            "Abstract": {
                "rich_text": [{ "text": { "content": abstract } }]
            },
            "Source_URL": { "url": source_url },
            "Status": { "select": { "name": "Ingested" } },
            "Scanned": { "checkbox": False }
        }
    }

    try:
        print("📤 正在发送...")
        r = SESSION.post(url, headers=headers, json=data)
        print(f"✅ NOTION 状态码: {r.status_code}")
        if r.status_code in (200,201):
            print("🎉 成功！去 Notion 看！")
        else:
            print("❌ 错误：", r.text[:500])
        return r.status_code in (200,201)
    except Exception as e:
        print("💥 发送失败：", str(e))
        return False

# ==========================================

def main():
    print("🚀 启动")
    print("🔑 API KEY:", "存在" if NOTION_API_KEY else "缺失")
    print("🆔 DB ID:", "存在" if DATABASE_ID else "缺失")

    if not NOTION_API_KEY or not DATABASE_ID:
        print("❌ 密钥缺失")
        return

    feed = feedparser.parse(RSS_FEEDS[0])
    if not feed.entries:
        print("❌ 无文章")
        return

    first = feed.entries[0]
    print("✅ 取第一条文章，直接发送")
    send_to_notion(first)

if __name__ == "__main__":
    main()
