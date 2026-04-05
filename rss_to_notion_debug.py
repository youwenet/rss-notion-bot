import os
import feedparser
import requests
import json
from datetime import datetime

# ----------------- 配置 -----------------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 测试 RSS，只抓第一条
TEST_RSS = "https://rss.arxiv.org/rss/cs.AI"

# 核心关键词（先少量测试）
CORE_KEYWORDS = [
    "cognitive bias", "mental model", "heuristic", "decision making"
]

# ----------------- 工具函数 -----------------
def word_count(text):
    return len(text.split())

def contains_keyword(text, keywords):
    text = text.lower()
    return any(k.lower() in text for k in keywords)

# ----------------- 推送到 Notion -----------------
def push_to_notion(title, abstract, url):
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Abstract": {"rich_text": [{"text": {"content": abstract[:2000]}}]},
            "Source_URL": {"url": url},
            "Status": {"select": {"name": "📥 Ingested"}},
            "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}}
        }
    }

    print("==== 准备推送到 Notion 的数据 ====")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    response = requests.post(NOTION_URL, headers=HEADERS, json=data)
    print("==== Notion API 返回 ====")
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

# ----------------- RSS 处理 -----------------
def process_feed(feed_url):
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print("⚠️ 没抓到文章:", feed_url)
        return

    entry = feed.entries[0]  # 只抓第一条文章
    title = entry.title
    abstract = getattr(entry, "summary", "")
    url = entry.link

    print("==== 测试文章信息 ====")
    print("标题:", title)
    print("摘要字数:", word_count(abstract))
    print("摘要预览:", abstract[:200])
    print("链接:", url)

    text = (title + " " + abstract).lower()
    if not contains_keyword(text, CORE_KEYWORDS):
        print("⚠️ 不包含核心关键词，仍然推送测试")
    else:
        print("✅ 包含核心关键词")

    push_to_notion(title, abstract, url)

# ----------------- 主函数 -----------------
def main():
    process_feed(TEST_RSS)

if __name__ == "__main__":
    main()
