import os
import feedparser
import requests
from datetime import datetime

# =========================
# 1️⃣ 配置
# =========================

# RSS Feed 地址列表（整合原有 + PubMed + Google Alerts 示例）
RSS_FEEDS = [
    # === Psychology 子领域 ===
    "https://nimh.nih.gov/news/science-updates/rss.xml",
    "https://positivepsychologynews.com/feed",
    "https://psychologicalscience.org/feed",
    "https://psychreg.org/feed",
    "https://spring.org.uk/feed",

    # === Cognitive Science / Neuroscience ===
    "https://cogneurosociety.org/feed",
    "https://learningandthebrain.com/blog/feed",
    "https://neurocritic.blogspot.com/feeds/posts/default",
    "https://neurosciencenews.com/feed",
    "https://news.mit.edu/rss/topic/neuroscience",
    "https://knowingneurons.com/feed",

    # === Social Science / Sociology ===
    "https://socialsciencespace.com/feed",
    "https://blogs.lse.ac.uk/impactofsocialsciences/feed",
    "https://phys.org/rss-feed/science-news/social-sciences",
    "https://news.mit.edu/rss/topic/social-sciences",

    # === Behavioral Science / Behavioral Economics ===
    "https://behavioralscientist.org/feed",
    "https://behavioraleconomics.com/feed",
    "https://economicspsychologypolicy.blogspot.com/feeds/posts/default",

    # === General Science ===
    "https://www.sciencenews.org/feed",
    "https://rss.sciam.com/ScientificAmer",
    "https://newscientist.com/feed/home",

    # === arXiv 子分类论文 RSS ===
    "https://arxiv.org/rss/cogsci",     # Cognitive Science
    "https://arxiv.org/rss/q-fin.EC",   # Quantitative Finance & Economics
    "https://arxiv.org/rss/econ.EM",    # Econometrics
    "https://arxiv.org/rss/q-bio.NC",   # Quantitative Biology — Neural & Cognitive
    "https://arxiv.org/rss/stat.ML",    # Statistics — Machine Learning

    # === PubMed RSS 示例（关键词搜索生成 RSS） ===
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000000/?limit=20&utm_campaign=pubmed-2&utm_content=cog-neuro-rss",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/23000001/?limit=20&utm_campaign=pubmed-2&utm_content=behavioral-econ-rss",

    # === Google Alerts RSS 示例（关键词生成的 RSS） ===
    "https://www.google.com/alerts/feeds/12345678901234567890/abcdefg",
    "https://www.google.com/alerts/feeds/12345678901234567890/hijklmn"
]

# 分类关键词，用于过滤文章（英文）
KEYWORDS = {
    "Psychology": ["cognition", "behavioral", "cognitive", "decision making", "learning", "emotion", "psychology", "mental", "clinical", "developmental"],
    "Economics": ["behavioral economics", "macro", "microeconomics", "market", "finance", "monetary", "game theory", "economic", "econometrics"],
    "Social Science": ["social behavior", "social network", "social structure", "group", "culture", "organization", "institution", "policy", "society"],
    "Cognitive Science": ["cognition", "memory", "attention", "language", "perception", "neuroscience", "brain", "decision", "modeling"],
    "Neuroscience": ["neuron", "brain", "neural", "synapse", "cortex", "hippocampus", "prefrontal", "dopamine", "neuroimaging", "functional MRI"]
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

def match_keywords(title, summary):
    """
    检查文章是否匹配关键词，返回匹配到的类别
    """
    matched_categories = []
    title_lower = title.lower()
    summary_lower = summary.lower()
    for category, words in KEYWORDS.items():
        for word in words:
            if word.lower() in title_lower or word.lower() in summary_lower:
                matched_categories.append(category)
                break  # 每类匹配到一个词即可
    return matched_categories

def add_to_notion(title, link, abstract, published, categories):
    """将文章添加到 Notion 数据库，并自动分类"""
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }
    if published:
        try:
            published_date = datetime(*published[:6]).isoformat()
        except Exception:
            published_date = None
    else:
        published_date = None

    # 将分类列表拼成逗号分隔字符串
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
    print(f"📡 抓取 RSS: {feed_url}")
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        title = entry.get("title", "No Title")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        published = entry.get("published_parsed")  # time.struct_time

        # 关键词过滤并自动分类
        matched = match_keywords(title, summary)
        if not matched:
            print(f"⚠️ 不匹配关键词，跳过: {title}")
            continue

        # 去重
        if link in existing_links:
            print(f"⚠️ 已存在，跳过: {title}")
            continue

        # 推送到 Notion
        add_to_notion(title, link, summary, published, matched)
