import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# 强制发送第一条，绝不卡、绝不筛选
FORCE_SEND_FIRST = True

# 超时保护
requests.adapters.DEFAULT_RETRIES = 0
SESSION = requests.Session()
SESSION.timeout = 15

# Notion 配置
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

# ===================== 你给的全部 RSS（已清理干净，无尖括号！）=====================
RSS_FEEDS = [
    # 1. 科研媒体
    "https://neurosciencenews.com/feed",
    "https://news.mit.edu/rss/topic/neuroscience",
    "https://knowingneurons.com/feed",
    "https://behavioralscientist.org/feed",
    "https://behavioraleconomics.com/feed",
    "https://socialsciencespace.com/feed",
    "https://blogs.lse.ac.uk/impactofsocialsciences/feed",
    "https://www.sciencenews.org/feed",
    "https://rss.sciam.com/ScientificAmerican",

    # 2. arXiv
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

    # 3. PubMed
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/decision%20making/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/behavioral%20science/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/cognitive%20neuroscience/",

    # 4. 顶级期刊
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

    # 5. 补充
    "https://arxiv.org/rss/cs.CC",
    "https://arxiv.org/rss/cs.NE",
    "https://arxiv.org/rss/q-bio.BM",
    "https://arxiv.org/rss/stat.AP",
    "https://arxiv.org/rss/cs.MS",

    # 6. 科技媒体
    "https://www.technologyreview.com/feed/",
    "https://www.economist.com/feeds/print-sections/233.xml",
    "https://learningandthebrain.com/blog/feed",
]

# ============================================================================

def clean_text(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(strip=True)

def send_to_notion(entry, source_tag="Custom"):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "TEST 自动发送")[:150]
    abstract = clean_text(entry.get("summary", "无摘要"))[:1500]
    source_url = entry.get("link", "")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
            "Source_URL": {"url": source_url},
            "RSS_Feed_Tag": {"select": {"name": source_tag}},
            "Status": {"select": {"name": "Ingested"}},
            "Scanned": {"checkbox": False},
            "Ingested_At": {"date": {"start": now}}
        }
    }

    try:
        print("📤 正在发送到 Notion...")
        r = SESSION.post(url, headers=headers, json=data)
        print(f"✅ Notion 返回状态码: {r.status_code}")
        if r.status_code in (200, 201):
            print("🎉 100% 成功！去 Notion 数据库查看！")
        else:
            print("❌ 错误信息：", r.text[:500])
        return r.status_code in (200, 201)
    except Exception as e:
        print("💥 发送失败：", str(e))
        return False

def get_source_tag(url):
    if "arxiv.org" in url:
        return "arXiv"
    elif "nature.com" in url:
        return "Nature"
    elif "pubmed.gov" in url:
        return "PubMed"
    elif "mit.edu" in url:
        return "MIT"
    elif "cell.com" in url:
        return "Cell"
    elif "sciencenews.org" in url:
        return "ScienceNews"
    else:
        return "Custom"

# ==================== 主逻辑：遍历所有 RSS，找到第一条就发送 ====================
def main():
    print("=" * 60)
    print("🚀 RSS → Notion 自动化系统启动")
    print(f"🔑 API 密钥：{'正常' if NOTION_API_KEY else '缺失'}")
    print(f"🆔 数据库ID：{'正常' if DATABASE_ID else '缺失'}")
    print("=" * 60)

    if not NOTION_API_KEY or not DATABASE_ID:
        print("❌ 请配置 GitHub Secrets")
        return

    for feed_url in RSS_FEEDS:
        try:
            print(f"\n🔍 正在读取：{feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.entries:
                first_entry = feed.entries[0]
                tag = get_source_tag(feed_url)
                print(f"✅ 找到文章：{first_entry.get('title', '无标题')[:60]}")
                send_to_notion(first_entry, tag)
                return
        except:
            continue

    print("❌ 所有 RSS 均无内容")

if __name__ == "__main__":
    main()
