import os
import requests
from datetime import datetime

# ---------- 配置 Notion Key 和数据库 ----------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "你的本地测试 Notion API Key")
DATABASE_ID = os.environ.get("DATABASE_ID", "你的本地测试数据库ID")

NOTION_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ---------- 测试文章 ----------
test_article = {
    "parent": {"database_id": DATABASE_ID},
    "properties": {
        "Title": {
            "title": [{"text": {"content": "🚀 测试文章 - Notion 推送成功验证"}}]
        },
        "Abstract": {
            "rich_text": [{"text": {"content": "这是一条测试摘要，用于验证 RSS 自动推送到 Notion 是否成功。摘要长度超过50个字保证通过条件。"}}]
        },
        "Source_URL": {"url": "https://example.com/test-article"},
        "Status": {"select": {"name": "New"}},
        "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}}
    }
}

# ---------- 推送函数 ----------
def push_to_notion(article):
    try:
        response = requests.post(NOTION_URL, headers=HEADERS, json=article)
        response.raise_for_status()
        print("✅ 推送成功，Notion 返回：")
        print(response.json())
    except requests.exceptions.HTTPError as e:
        print("❌ HTTPError:", e.response.status_code, e.response.text)
    except Exception as e:
        print("❌ Exception:", str(e))

# ---------- 主程序 ----------
if __name__ == "__main__":
    push_to_notion(test_article)
