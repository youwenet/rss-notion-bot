
import os
import requests

# =========================
# 配置
# =========================
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_VERSION = "2022-06-28"
MIN_ABSTRACT_LEN = 180  # 摘要长度阈值

# =========================
# 删除函数
# =========================
def delete_page_notion(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION
    }
    resp = requests.patch(url, headers=headers, json={"archived": True})
    if resp.status_code == 200:
        return True
    else:
        print(f"❌ 删除失败: {page_id}, {resp.status_code}, {resp.text}")
        return False

# =========================
# 主程序
# =========================
def clean_short_abstract_articles():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    body = {"page_size": 100}  # 可循环分页
    has_more = True
    start_cursor = None

    while has_more:
        if start_cursor:
            body["start_cursor"] = start_cursor
        resp = requests.post(url, headers=headers, json=body)
        if resp.status_code != 200:
            print(f"⚠️ 获取文章失败: {resp.status_code}, {resp.text}")
            break

        data = resp.json()
        for page in data.get("results", []):
            props = page.get("properties", {})
            abstract_text = ""
            abstract_prop = props.get("Abstract", {}).get("rich_text", [])
            if abstract_prop:
                abstract_text = abstract_prop[0].get("text", {}).get("content", "")

            if len(abstract_text) < MIN_ABSTRACT_LEN:
                page_title = props.get("Title", {}).get("title", [{}])[0].get("text", {}).get("content", "No Title")
                if delete_page_notion(page.get("id")):
                    print(f"🗑️ 已删除摘要过短文章: {page_title}")

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor", None)

# 执行清理
clean_short_abstract_articles()
print("✅ 摘要短文章清理完成")
