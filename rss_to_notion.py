import os
import feedparser
import requests
from datetime import datetime
import json

# =========================
# 配置
# =========================

RSS_FEEDS = [
    "https://arxiv.org/rss/cogsci",
    "https://arxiv.org/rss/q-fin.EC",
    "https://arxiv.org/rss/econ.EM",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000000/?limit=20",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000001/?limit=20",
    "https://www.google.com/alerts/feeds/12345678901234567890/abcdefg"
]

KEYWORDS = [
    "cognition","decision making","behavior","learning","memory",
    "attention","perception","emotion","neuroscience","neural",
    "brain","social network","culture","organization","economics",
    "finance","game theory","clinical psychology","computational modeling","neuroimaging"
]

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_BASE_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

# =========================
# 辅助函数
# =========================

def get_existing_links():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    existing_links = set()
    body = {"page_size":50}
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        for page in results:
            link_val = page.get("properties", {}).get("Link", {}).get("url")
            if link_val:
                existing_links.add(link_val)
    else:
        print(f"⚠️ 获取已有文章失败: {resp.status_code}, {resp.text}")
    print(f"🔹 已有文章数量: {len(existing_links)}")
    return existing_links

def match_keywords(text):
    text = text.lower()
    matched = [kw for kw in KEYWORDS if kw.lower() in text]
    return matched

def add_to_notion(title, link, abstract, published, categories):
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    published_date = None
    if published:
        try:
            published_date = datetime(*published[:6]).isoformat()
        except:
            pass

    category_text = ", ".join(categories) if categories else "Uncategorized"

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title":[{"text":{"content":title}}]},
            "Link":{"url":link},
            "Abstract":{"rich_text":[{"text":{"content":abstract}}]},
            "Category":{"rich_text":[{"text":{"content":category_text}}]}
        }
    }
    if published_date:
        data["properties"]["Published Date"] = {"date":{"start":published_date}}

    print("\n🔹 JSON Payload 要推送到 Notion：")
    print(json.dumps(data, indent=2))  # 打印完整 payload

    response = requests.post(NOTION_BASE_URL, headers=headers, json=data)
    print(f"HTTP 状态码: {response.status_code}, 返回: {response.text}")

# =========================
# 主程序
# =========================

print("📌 获取已有文章...")
existing_links = get_existing_links()

for feed_url in RSS_FEEDS:
    print(f"\n📡 抓取 RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    print(f"🔹 RSS 共抓取 {len(feed.entries)} 条文章")

    for entry in feed.entries:
        title = entry.get("title","No Title")
        link = entry.get("link","")
        summary = entry.get("summary","")
        published = entry.get("published_parsed")

        print(f"\n📝 标题: {title}")
        print(f"🔗 链接: {link}")
        print(f"摘要长度: {len(summary)}")

        matched = match_keywords(title + " " + summary)
        print(f"匹配关键词: {matched}")

        if not matched:
            matched = ["Uncategorized"]

        if link in existing_links:
            print("⚠️ 已存在，跳过")
            continue

        add_to_notion(title, link, summary, published, matched)
