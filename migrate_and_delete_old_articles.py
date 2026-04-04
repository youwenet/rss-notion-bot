import os
import requests
import time

# =========================
# 配置
# =========================
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

# 旧字段 -> 新字段映射
FIELD_MAP = {
    "Name": "Title",
    "Source": "Journal",
    "Link": "Source_URL",
    "Published Date": "Published_Date",
    "Field": "Academic_Field"
}

MIN_ABSTRACT_LENGTH = 180  # 摘要字数下限

# =========================
# 辅助函数
# =========================

def get_all_pages(database_id, page_size=50):
    """分页获取数据库所有页面"""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    has_more = True
    start_cursor = None
    all_pages = []

    while has_more:
        payload = {"page_size": page_size}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"⚠️ 查询失败: {resp.status_code}, {resp.text}")
            break
        data = resp.json()
        all_pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
        time.sleep(0.2)  # 避免请求太快
    return all_pages

def get_property_text(prop, old_field=None):
    """读取文本内容，兼容旧字段"""
    if not prop:
        return ""
    # title
    if "title" in prop and prop["title"]:
        return "".join([t["text"]["content"] for t in prop["title"]])
    # rich_text
    if "rich_text" in prop and prop["rich_text"]:
        return "".join([t["text"]["content"] for t in prop["rich_text"]])
    # url
    if "url" in prop and prop["url"]:
        return prop["url"]
    # date
    if "date" in prop and prop["date"]:
        return prop["date"].get("start", "")
    # select / multi_select
    if "select" in prop and prop["select"]:
        return prop["select"].get("name", "")
    if "multi_select" in prop and prop["multi_select"]:
        return ", ".join([s["name"] for s in prop["multi_select"]])
    # 兼容旧字段名称
    if old_field and old_field in FIELD_MAP:
        return get_property_text(prop)
    return ""

def migrate_and_delete(page):
    """迁移字段 + 判断摘要长度 <180 自动删除"""
    page_id = page["id"]
    properties = page.get("properties", {})
    updates = {}
    
    # --------- 迁移旧字段 ---------
    for old_field, new_field in FIELD_MAP.items():
        old_prop = properties.get(old_field)
        if not old_prop:
            continue
        text_content = get_property_text(old_prop)
        if not text_content:
            continue
        # 判断属性类型
        if "title" in old_prop:
            updates[new_field] = {"title": [{"text": {"content": text_content}}]}
        elif "rich_text" in old_prop:
            updates[new_field] = {"rich_text": [{"text": {"content": text_content}}]}
        elif "url" in old_prop:
            updates[new_field] = {"url": text_content}
        elif "date" in old_prop:
            updates[new_field] = {"date": {"start": text_content}}
        elif "select" in old_prop:
            updates[new_field] = {"select": {"name": text_content}}
        elif "multi_select" in old_prop:
            updates[new_field] = {"multi_select": [{"name": n.strip()} for n in text_content.split(",")]}
        # 清空旧字段
        updates[old_field] = {}
    
    if updates:
        resp = requests.patch(f"{NOTION_BASE_URL}/{page_id}", headers=HEADERS, json={"properties": updates})
        if resp.status_code == 200:
            print(f"✅ 字段迁移成功: {page_id}")
        else:
            print(f"❌ 字段迁移失败: {page_id}, {resp.status_code}, {resp.text}")

    # --------- 删除摘要 < 180 字 ---------
    abstract_prop = properties.get("Abstract") or properties.get("abstract")  # 兼容大小写
    abstract_text = get_property_text(abstract_prop)
    if len(abstract_text) < MIN_ABSTRACT_LENGTH:
        del_resp = requests.delete(f"{NOTION_BASE_URL}/{page_id}", headers=HEADERS)
        if del_resp.status_code == 200:
            print(f"🗑️ 删除摘要不足180字的文章: {page_id}")
        else:
            print(f"❌ 删除失败: {page_id}, {del_resp.status_code}, {del_resp.text}")

# =========================
# 主程序
# =========================

all_pages = get_all_pages(DATABASE_ID)
print(f"📌 共获取 {len(all_pages)} 条页面，开始迁移字段 + 删除摘要 <180字文章...")

for page in all_pages:
    migrate_and_delete(page)
    time.sleep(0.2)  # 避免请求过快

print("🎯 迁移与删除操作完成。")
