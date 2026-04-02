import os
import feedparser
import requests
from datetime import datetime

# =========================
# 1️⃣ 配置
# =========================

RSS_FEEDS = [
    # arXiv 示例
    "https://arxiv.org/rss/cogsci",
    "https://arxiv.org/rss/q-fin.EC",
    "https://arxiv.org/rss/econ.EM",

    # PubMed 示例 RSS（关键词搜索生成）
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000000/?limit=20",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000001/?limit=20",

    # Google Alerts RSS 示例
    "https://www.google.com/alerts/feeds/12345678901234567890/abcdefg"
]

# 优化关键词列表（英文）
KEYWORDS = {
    "Psychology": [
        "cognition", "cognitive", "behavioral", "behavior", "decision making",
        "emotion", "learning", "memory", "mental", "clinical", "developmental",
        "attention", "perception", "psychology"
    ],
    "Economics": [
        "behavioral economics", "macro", "microeconomics", "market", "finance",
        "monetary", "game theory", "economic", "econometrics", "financial"
    ],
    "Social Science": [
        "social behavior", "social network", "social structure", "group",
        "culture", "organization", "institution", "policy", "society", "social"
    ],
    "Cognitive Science": [
        "cognition", "memory", "attention", "language", "perception",
        "neuroscience", "brain", "decision", "modeling", "computational",
        "cognitive modeling"
    ],
    "Neuroscience": [
        "neuron", "brain", "neural", "synapse", "cortex", "hippocampus",
        "prefrontal", "dopamine", "neuroimaging", "functional MRI", "EEG",
        "fMRI", "neuroplasticity"
    ]
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
    """获取已有文章链接，避免重复推送"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    existing_links = set()
    body = {"page_size": 50}  # 最新 50 条
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        for page in results:
            props = page.get("properties", {})
            link_val = props.get("Link", {}).get("url")
            if link_val:
                existing_links.add(link_val)
    else:
        print(f"⚠️ 获取已有文章失败: {resp.status_code}, {resp.text}")
    print(f"🔹 已有文章数量: {len(existing_links)}")
    return existing_links

def match_keywords(title, summary):
    """匹配关键词，返回匹配的类别"""
    matched_categories = []
    text = f"{title} {summary}".lower()
    for category, words in KEYWORDS.items():
        for word in words:
            if word.lower() in text:
                matched_categories.append(category)
                break
    return matched_categories

def add_to_notion(title, link, abstract, published, categories):
    """推送文章到 Notion"""
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
            "Name": {"title": [{"text": {"content": title}}]},
            "Link": {"url": link},
            "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
            "Category": {"rich_text": [{"text": {"content": category_text}}]},
        }
    }
    if published_date:
        data["properties"]["Published Date"] = {"date": {"start": published_date}}

    response = requests.post(NOTION_BASE_URL, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 添加成功: {title} | Category: {category_text}")
    else:
        print(f"❌ 添加失败: {title}, {response.status_code}, {response.text}")

# =========================
# 3️⃣ 主程序
# =========================

print("📌 获取已有文章...")
existing_links = get_existing_links()

for feed_url in RSS_FEEDS:
    print(f"\n📡 抓取 RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    print(f"🔹 RSS 共抓取 {len(feed.entries)} 条文章")

    for entry in feed.entries:
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        published = entry.get("published_parsed")

        print(f"\n📝 标题: {title}")
        print(f"🔗 链接: {link}")
        print(f"🖊 摘要长度: {len(summary)}")

        matched = match_keywords(title, summary)
        print(f"🎯 匹配类别: {matched}")

        if not matched:
            print("⚠️ 无匹配关键词，仍推送为 Uncategorized")
            matched = ["Uncategorized"]

        if link in existing_links:
            print("⚠️ 已存在，跳过")
            continue

        add_to_notion(title, link, summary, published, matched)
