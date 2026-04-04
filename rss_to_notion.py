import os
import requests

# =========================
# 配置
# =========================
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

MIN_ABSTRACT_LENGTH = 180  # 摘要少于180字符将被删除

# =========================
# 获取数据库文章（处理分页）
# =========================
def get_all_pages():
    pages = []
    start_cursor = None
    while True:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor
        resp = requests.post(f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query", headers=HEADERS, json=body)
        if resp.status_code != 200:
            print(f"⚠️ 获取页面失败: {resp.status_code} {resp.text}")
            break
        data = resp.json()
        pages.extend(data.get("results", []))
        if data.get("has_more"):
            start_cursor = data.get("next_cursor")
        else:
            break
    return pages

# =========================
# 删除页面
# =========================
def delete_page(page_id):
    resp = requests.patch(f"{NOTION_BASE_URL}/pages/{page_id}", headers=HEADERS, json={"archived": True})
    if resp.status_code == 200:
        print(f"✅ 已删除页面: {page_id}")
    else:
        print(f"❌ 删除失败: {page_id}, {resp.status_code}, {resp.text}")

# =========================
# 主逻辑
# =========================
def main():
    print("📌 获取所有文章...")
    pages = get_all_pages()
    print(f"总共获取到 {len(pages)} 条文章")

    count_deleted = 0
    for page in pages:
        page_id = page.get("id")
        props = page.get("properties", {})
        abstract_prop = props.get("Abstract", {}).get("rich_text", [])
        # 拼接所有段落文本
        abstract_text = "".join([t.get("text", {}).get("content", "") for t in abstract_prop]).strip()
        abstract_length = len(abstract_text)

        print(f"📝 页面ID: {page_id} | 摘要长度: {abstract_length}")

        if abstract_length < MIN_ABSTRACT_LENGTH:
            delete_page(page_id)
            count_deleted += 1

    print(f"🎯 总共删除 {count_deleted} 条摘要长度小于 {MIN_ABSTRACT_LENGTH} 的文章")

if __name__ == "__main__":
    main()
