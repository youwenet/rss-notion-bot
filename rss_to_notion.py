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

# 你的完整RSS列表（已清理干净）
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
    """彻底清理HTML标签，返回纯文本"""
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except:
        return html_text

def count_words(text):
    """统计英文单词数，用于后续150词筛选"""
    if not text:
        return 0
    return len([w for w in text.split() if w.strip()])

def get_rss_feed_tag(feed_url):
    """自动匹配RSS源标签（对应Notion Select字段）"""
    if "arxiv.org" in feed_url.lower():
        return "arXiv"
    elif "nature.com" in feed_url.lower():
        return "Nature"
    elif "pubmed.ncbi.nlm.nih.gov" in feed_url.lower():
        return "PubMed"
    elif "ssrn.com" in feed_url.lower():
        return "SSRN"
    elif "mit.edu" in feed_url.lower():
        return "MIT"
    elif "cell.com" in feed_url.lower():
        return "Cell"
    elif "sciencenews.org" in feed_url.lower():
        return "ScienceNews"
    else:
        return "Custom"

def extract_doi(link, summary):
    """尝试从链接或摘要提取DOI"""
    if link and "doi.org/" in link:
        return link.split("doi.org/")[-1].strip()
    if "doi:" in summary.lower():
        s = summary.lower().split("doi:")[-1]
        return s.split()[0].strip()
    return ""

def extract_journal(feed_url, feed_title):
    """提取期刊名"""
    if "nature.com" in feed_url:
        return "Nature"
    elif "arxiv.org" in feed_url:
        return "arXiv"
    elif "pubmed.ncbi.nlm.nih.gov" in feed_url:
        return "PubMed"
    elif "cell.com" in feed_url:
        return "Cell"
    elif "pnas.org" in feed_url:
        return "PNAS"
    else:
        return feed_title or "Unknown Journal"

# ==========================================
# 核心：发送到Notion（严格匹配你的INPUT层字段）
# ==========================================
def send_to_notion(entry, feed_tag, journal):
    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    # 提取文章信息
    title = entry.get("title", "No Title")[:200].strip()
    abstract_raw = entry.get("summary", "")
    abstract = clean_text(abstract_raw)[:2000].strip()
    source_url = entry.get("link", "").strip()
    doi = extract_doi(source_url, abstract_raw)
    published = entry.get("published", "").strip()

    # 生成UTC时间戳（Notion要求）
    ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    print("\n📤 准备发送到Notion的内容：")
    print(f"标题: {title}")
    print(f"摘要词数: {count_words(abstract)}")
    print(f"链接: {source_url}")

    # ===================== 严格匹配你的INPUT层字段 =====================
    properties = {
        # High优先级字段
        "Title": {
            "title": [{"text": {"content": title}}]
        },
        "Abstract": {
            "rich_text": [{"text": {"content": abstract}}]
        },
        "Source_URL": {
            "url": source_url if source_url else None
        },
        "Journal": {
            "rich_text": [{"text": {"content": journal}}]
        },
        "Scanned": {
            "checkbox": False  # ✅ 严格按照你的设计：默认false，Claude扫描后设为true
        },
        "Status": {
            "select": {"name": "Ingested"}  # ✅ 流水线初始状态
        },

        # Medium优先级字段
        "DOI": {
            "rich_text": [{"text": {"content": doi}}]
        },
        "RSS_Feed_Tag": {
            "select": {"name": feed_tag}
        },

        # Low优先级字段
        "Ingested_At": {
            "date": {"start": ingested_at}
        }
    }

    # 日期字段非空才添加，避免Notion报错
    if published and len(published) >= 10:
        properties["Published_Date"] = {"date": {"start": published[:10]}}

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }

    try:
        print("\n🔗 正在调用Notion API...")
        response = SESSION.post(url, headers=headers, json=data)
        print(f"✅ Notion API 状态码: {response.status_code}")

        if response.status_code in (200, 201):
            print("🎉 文章成功写入Notion数据库！")
            return True
        else:
            print("❌ Notion API 错误详情：")
            print(response.text[:1000])
            return False
    except requests.exceptions.Timeout:
        print("💥 错误：Notion API 请求超时！")
        return False
    except requests.exceptions.ConnectionError:
        print("💥 错误：网络连接失败！")
        return False
    except Exception as e:
        print(f"💥 未知错误：{str(e)}")
        return False

# ==========================================
# 主逻辑
# ==========================================
def main():
    print("=" * 60)
    print("🚀 RSS → Notion 自动化系统（INPUT层）启动")
    print(f"⏰ 运行时间: {datetime.now(timezone.utc).isoformat()}")
    print(f"🔑 NOTION_API_KEY 状态: {'✅ 已读取' if NOTION_API_KEY else '❌ 未读取'}")
    print(f"🆔 DATABASE_ID 状态: {'✅ 已读取' if DATABASE_ID else '❌ 未读取'}")
    print("=" * 60)

    # 第一步：检查环境变量
    if not NOTION_API_KEY or not DATABASE_ID:
        print("\n❌ 致命错误：GitHub Secrets 未正确配置！")
        return

    # 第二步：遍历RSS源，筛选摘要>150词的文章（先测试用低门槛）
    MIN_WORD_COUNT = 50  # 测试用，后续改回150
    SEND_ONLY_ONE = True
    sent = False

    for feed_url in RSS_FEEDS:
        if sent:
            break
        print(f"\n🔍 正在解析RSS源: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo != 0:
                print(f"❌ RSS解析错误: {feed.bozo_exception}")
                continue
            print(f"✅ RSS解析成功，共 {len(feed.entries)} 篇文章")
        except Exception as e:
            print(f"❌ RSS读取失败: {str(e)}")
            continue

        feed_tag = get_rss_feed_tag(feed_url)
        journal = extract_journal(feed_url, feed.feed.get("title", ""))

        # 第三步：遍历文章，筛选符合条件的
        for entry in feed.entries[:10]:
            abstract = clean_text(entry.get("summary", ""))
            word_count = count_words(abstract)

            print(f"\n📝 文章: {entry.get('title', 'No Title')[:60]}")
            print(f"   摘要词数: {word_count}")

            if word_count >= MIN_WORD_COUNT:
                print(f"✅ 词数达标（≥{MIN_WORD_COUNT}），准备发送...")
                if send_to_notion(entry, feed_tag, journal):
                    sent = True
                    if SEND_ONLY_ONE:
                        print("\n✅ 任务完成：成功发送1篇文章到Notion！")
                        return
            else:
                print(f"⏭️ 词数不足（<{MIN_WORD_COUNT}），跳过")

    # 第四步：最终结果
    print("\n" + "=" * 60)
    if sent:
        print("✅ 任务完成：成功发送文章到Notion！")
    else:
        print("ℹ️ 任务结束：未找到符合条件的文章，或发送失败")
    print("=" * 60)

if __name__ == "__main__":
    main()
