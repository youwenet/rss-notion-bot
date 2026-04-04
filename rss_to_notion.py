import os
import requests

# =========================
# 配置
# =========================

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_VERSION = "2022-06-28"
MIN_ABSTRACT_LENGTH = 180  # 小于180字的摘要将被删除

NOTION_BASE_URL = "https://api.notion.com/v1"

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

# =========================
# 获取数据库所有页面（支持分页）
# =========================

def get_all_pages(database_id):
    all_pages = []
    has_more = True
    next_cursor = None

    while has_more:
        query = {"page_size": 100}
        if next_cursor:
            query["start_cursor"] = next_cursor

        resp = requests.post(f"{NOTION_BASE_URL}/databases/{database_id}/query", headers=headers, json=query)
        if resp.status_code != 200:
            print(f"⚠️ 查询数据库失败: {resp.status_code}, {resp.text}")
            break

        data = resp.json()
        results = data.get("results", [])
        all_pages.extend(results)

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    print(f"📌 获取到总文章数: {len(all_pages)}")
    return all_pages

# =========================
# 删除页面
# =========================

def delete_page(page_id, title):
    resp = requests.patch(f"{NOTION_BASE_URL}/pages/{page_id}", headers=headers, json={"archived": True})
    if resp.status_code == 200:
        print(f"✅ 删除文章成功: {title}")
    else:
        print(f"❌ 删除文章失败: {title}, {resp.status_code}, {resp.text}")

# =========================
# 主程序
# =========================

pages = get_all_pages(DATABASE_ID)

for page in pages:
    page_id = page.get("id")
    props = page.get("properties", {})
    title_prop = props.get("Title", {}).get("title", [])
    title_text = "".join([t.get("plain_text", "") for t in title_prop]).strip() or "No Title"

    abstract_prop = props.get("Abstract", {}).get("rich_text", [])
    abstract_text = "".join([t.get("plain_text", "") for t in abstract_prop]).strip()

    if len(abstract_text) < MIN_ABSTRACT_LENGTH:
        delete_page(page_id, title_text)
