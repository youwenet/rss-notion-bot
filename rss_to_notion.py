import os
import feedparser
import requests
from datetime import datetime

# ------------------ 配置 ------------------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_URL = "https://api.notion.com/v1/pages"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 53 个 RSS 源（示例，替换为实际全部53条）
RSS_FEEDS = [
    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.LG",
    # ... 其余50条 RSS 链接
]

# ------------------ 函数 ------------------
def fetch_articles():
    """
    获取每个 RSS 的最新文章，摘要 >=150 词，返回一条测试文章
    """
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            summary_words = len(entry.get("summary", "").split())
            if summary_words >= 150:
                return {
                    "title": entry.get("title", "No Title"),
                    "abstract": entry.get("summary", "No Abstract"),
                    "link": entry.get("link", ""),
                    "feed_tag": feed_url.split("/")[2]  # 用域名简单标记源
                }
    return None

def push_to_notion(article):
    """
    推送单篇文章到 Notion
    """
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": article["title"]}}]},
            "Abstract": {"rich_text": [{"text": {"content": article["abstract"]}}]},
            "Source_URL": {"url": article["link"]},
            "RSS_Feed_Tag": {"select": {"name": article["feed_tag"]}},
            "Status": {"select": {"name": "New"}},
            "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}}
        }
    }
    try:
        resp = requests.post(NOTION_URL, headers=HEADERS, json=data)
        resp.raise_for_status()
        print("✅ 推送成功！Notion 返回：")
        print(resp.json())
    except requests.exceptions.HTTPError as e:
        print("❌ HTTPError:", e.response.status_code, e.response.text)
    except Exception as e:
        print("❌ Exception:", str(e))

# ------------------ 主流程 ------------------
if __name__ == "__main__":
    article = fetch_articles()
    if article:
        print("找到符合条件的文章，开始推送...")
        push_to_notion(article)
    else:
        print("没有找到摘要 >=150 词的文章，等待下一次运行。")
