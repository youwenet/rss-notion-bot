import os
import feedparser
import requests
from datetime import datetime

# =========================
# 1️⃣ 配置
# =========================

# RSS Feed 地址列表
RSS_FEEDS = [
    "https://arxiv.org/rss/cs",        # CS 类论文
    "https://arxiv.org/rss/math"       # 数学类论文
    # 可以继续添加其他 RSS 链接，比如 Feedy 的 RSS
]

# 分类关键词，用于过滤文章
KEYWORDS = {
    "心理学": ["认知", "神经心理学", "行为心理学", "情绪", "决策", "学习"],
    "经济学": ["行为经济学", "宏观经济", "微观经济", "市场", "金融", "货币", "博弈论"],
    "社会学": ["社会行为", "社会网络", "社会结构", "群体", "文化", "组织", "制度"]
}

# Notion 配置
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("DATABASE_ID")
NOTION_BASE_URL = "https://api.notion.com/v1/pages"
NOTION_VERSION = "2022-06-28"

# =========================
# 2️⃣ 辅助函数
# =========================

def get_existing_links():
    """
    获取数据库已有文章链接，避免重复插入
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    existing_links = set()
    body = {"page_size": 50}  # 获取最新50条，可按需增加
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        for page in results:
            props = page.get("properties", {})
            link_prop = props.get("Link", {})
            link_val = link_prop.get("url")
            if link_val:
                existing_links.add(link_val)
    else:
        print(f"⚠️ 获取已有文章失败: {resp.status_code}, {resp.text}")
    return existing_links

def add_to_notion(title, link, abstract, published):
    """将文章添加到 Notion 数据库"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    # 格式化日期
    if published:
        try:
            published_date = datetime(*published[:6]).isoformat()
        except Exception:
            published_date = None
    else:
        published_date = None

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Link": {"url": link},
            "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
        }
    }
    if published_date:
        data["properties"]["Published Date"] = {"date": {"start": published_date}}

    response = requests.post(NOTION_BASE_URL, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 添加成功: {title}")
    else:
        print(f"❌ 添加失败: {title}, {response.status_code}, {response.text}")

def match_keywords(title, summary):
    """
    检查文章是否匹配关键词，返回匹配到的类别
    """
    matched_categories = []
    for category, words in KEYWORDS.items():
        for word in words:
            if word in title or word in summary:
                matched_categories.append(category)
                break  # 每类匹配到一个词即可
    return matched_categories

# =========================
# 3️⃣ 主程序
# =========================

print("📌 获取已有文章...")
existing_links = get_existing_links()

for feed_url in RSS_FEEDS:
    print(f"📡 抓取 RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        title = entry.get("title", "无标题")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        published = entry.get("published_parsed")  # time.struct_time

        # 关键词过滤
        matched = match_keywords(title, summary)
        if not matched:
            print(f"⚠️ 不匹配关键词，跳过: {title}")
            continue

        # 去重
        if link in existing_links:
            print(f"⚠️ 已存在，跳过: {title}")
            continue

        # 推送到 Notion
        add_to_notion(title, link, summary, published)
