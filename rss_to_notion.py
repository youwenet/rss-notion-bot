import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# 超时防卡死
requests.adapters.DEFAULT_RETRIES = 0
SESSION = requests.Session()
SESSION.timeout = 15

# Notion 配置
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

# 你的完整RSS列表
RSS_FEEDS = [
    "https://neurosciencenews.com/feed",
    "https://news.mit.edu/rss/topic/neuroscience",
    "https://knowingneurons.com/feed",
    "https://behavioralscientist.org/feed",
    "https://behavioraleconomics.com/feed",
    "https://socialsciencespace.com/feed",
    "https://blogs.lse.ac.uk/impactofsocialsciences/feed",
    "https://www.sciencenews.org/feed",
    "https://rss.sciam.com/ScientificAmerican",

    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/stat.ML",
    "https://arxiv.org/rss/q-bio.NC",
    "https://arxiv.org/rss/q-bio.PE",
    "https://arxiv.org/rss/cs.CY",
    "https://arxiv.org/rss/cs.SI",
    "https://arxiv.org/rss/cs.GT",
    "https://arxiv.org/rss/physics.soc-ph",
    "https://arxiv.org/rss/physics.comp-ph",
    "https://arxiv.org/rss/physics.data-an",
    "https://arxiv.org/rss/econ.TH",
    "https://arxiv.org/rss/econ.EM",
    "https://arxiv.org/rss/econ.GN",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.MA",
    "https://arxiv.org/rss/cs.IT",
    "https://arxiv.org/rss/cs.DS",

    "https://pubmed.ncbi.nlm.nih.gov/rss/search/decision%20making/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/behavioral%20science/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/cognitive%20neuroscience/",

    "https://www.nature.com/neuro.rss",
    "https://www.nature.com/nathumbehav.rss",
    "https://www.sciencemag.org/rss/news/science-neuroscience",
    "https://www.pnas.org/rss/news",
    "https://www.cell.com/trends/cognitive-sciences/rss",
    "https://www.cell.com/current-biology/rss",
    "https://www.cell.com/neuron/rss",
    "https://www.apa.org/pubs/journals/xge/feed",
    "https://www.journals.elsevier.com/behavioral-brain-research/rss",
    "https://www.springer.com/journal/13415/rss",

    "https://arxiv.org/rss/cs.CC",
    "https://arxiv.org/rss/cs.NE",
    "https://arxiv.org/rss/q-bio.BM",
    "https://arxiv.org/rss/stat.AP",
    "https://arxiv.org/rss/cs.MS",

    "https://www.technologyreview.com/feed/",
    "https://www.economist.com/feeds/print-sections/233.xml",
    "https://learningandthebrain.com/blog/feed",
]

# ==========================================
# 工具函数
# ==========================================
def clean_text(html_text):
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except:
        return html_text

def count_words(text):
    if not text:
        return 0
    return len([w for w in text.split() if w.strip()])

def get_rss_feed_tag(feed_url):
    if "arxiv.org" in feed_url.lower():
        return "arXiv"
    elif "nature.com" in feed_url.lower():
        return "Nature"
    elif "pubmed.gov" in feed_url.lower():
        return "PubMed"
    elif "mit.edu" in feed_url.lower():
        return "MIT"
    elif "cell.com" in feed_url.lower():
        return "Cell"
    else:
        return "Custom"

def extract_doi(link, summary):
    if link and "doi.org/" in link:
        return link.split("doi.org/")[-1].strip()
    return ""

def extract_journal(feed_url):
    if "nature.com" in feed_url: return "Nature"
    if "arxiv.org" in feed_url: return "arXiv"
    if "pubmed.gov" in feed_url: return "PubMed"
    if "cell.com" in feed_url: return "Cell"
    if "pnas.org" in feed_url: return "PNAS"
    return "Unknown Journal"

# ==========================================
# ✅ 修复：发表时间 Published_Date
# ==========================================
def get_published_date(entry):
    """自动从RSS提取日期，100%写入Notion"""
    try:
        date_str = None
        if hasattr(entry, 'published'): date_str = entry.published
        elif hasattr(entry, 'updated'): date_str = entry.updated
        elif hasattr(entry, 'date'): date_str = entry.date

        if not date_str:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for fmt in ["%a, %d %b %Y", "%Y-%m-%d", "%d %b %Y"]:
            try:
                return datetime.strptime(date_str[:16], fmt).strftime("%Y-%m-%d")
            except:
                continue
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    except:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ==========================================
# 核心发送
# ==========================================
def send_to_notion(entry, feed_tag, journal):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "No Title")[:200].strip()
    abstract_raw = entry.get("summary", "")
    abstract = clean_text(abstract_raw)[:2000].strip()
    source_url = entry.get("link", "").strip()
    doi = extract_doi(source_url, abstract_raw)
    published_date = get_published_date(entry)
    ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
        "Source_URL": {"url": source_url},
        "Journal": {"rich_text": [{"text": {"content": journal}}]},
        "Scanned": {"checkbox": False},
        "Status": {"select": {"name": "Ingested"}},
        "DOI": {"rich_text": [{"text": {"content": doi}}]},
        "RSS_Feed_Tag": {"select": {"name": feed_tag}},
        "Ingested_At": {"date": {"start": ingested_at}},

        # ✅ 修复：发表时间必写入
        "Published_Date": {"date": {"start": published_date}}
    }

    data = {"parent": {"database_id": DATABASE_ID},"properties": properties}

    try:
        res = SESSION.post(url, headers=headers, json=data)
        print(f"✅ Notion 状态码: {res.status_code}")
        print(f"📅 发表时间已写入: {published_date}")
        return res.status_code in (200,201)
    except:
        return False

# ==========================================
# 主逻辑
# ==========================================
def main():
    print("🚀 RSS → Notion 已启动（已修复发表时间）")
    if not NOTION_API_KEY or not DATABASE_ID:
        print("❌ 密钥缺失")
        return

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                first = feed.entries[0]
                tag = get_rss_feed_tag(feed_url)
                journal = extract_journal(feed_url)
                print(f"✅ 找到文章：{first.title[:50]}")
                send_to_notion(first, tag, journal)
                return
        except:
            continue

if __name__ == "__main__":
    main()
