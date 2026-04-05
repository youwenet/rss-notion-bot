import os
import requests
from datetime import datetime

# 从 GitHub Secrets 获取环境变量
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")

NOTION_URL = "https://api.notion.com/v1/pages"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ---------- 测试文章 ----------
test_article = {
    "title": "测试文章标题",
    "abstract": "这是一条用于测试的摘要，确保Notion可以写入数据。文字长度超过50字，以满足条件要求。",
    "source_url": "https://example.com/test-article",
    "status": "New"
}

# ---------- 判断摘要长度 ----------
if len(test_article["abstract"]) < 50:
    print("❌ 摘要不足50字，跳过写入")
else:
    # 构造 Notion 推送数据
    notion_payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": test_article["title"]}}]},
            "Abstract": {"rich_text": [{"text": {"content": test_article["abstract"]}}]},
            "Source_URL": {"url": test_article["source_url"]},
            "Status": {"select": {"name": test_article["status"]}},
            "Ingested_At": {"date": {"start": datetime.utcnow().isoformat()}}
        }
    }

    # ---------- 推送到 Notion ----------
    try:
        response = requests.post(NOTION_URL, headers=HEADERS, json=notion_payload)
        response.raise_for_status()
        print("✅ 推送成功！Notion 返回：")
        print(response.json())
    except requests.exceptions.HTTPError as e:
        print("❌ HTTPError:", e.response.status_code, e.response.text)
    except Exception as e:
        print("❌ Exception:", str(e))
