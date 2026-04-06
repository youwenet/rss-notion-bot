import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import config

# ------------------------------------------------------------------------------
# Notion API 客户端
# ------------------------------------------------------------------------------
class NotionClient:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("DATABASE_ID")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": config.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def create_page(self, payload):
        try:
            r = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=config.TIMEOUT
            )
            return r.status_code in (200, 201)
        except Exception as e:
            print(f"⚠️ Notion 异常: {e}")
            return False

    def is_duplicate(self, doi=None, url=None):
        filters = []
        if doi and doi.strip():
            filters.append({"property": "DOI", "rich_text": {"equals": doi.strip()}})
        if url and url.strip():
            filters.append({"property": "Source_URL", "url": {"equals": url.strip()}})
        if not filters:
            return False

        try:
            res = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.headers,
                json={"filter": {"or": filters}},
                timeout=10
            )
            return len(res.json().get("results", [])) > 0
        except:
            return False

# ------------------------------------------------------------------------------
# 关键词筛选引擎（完全不动！）
# ------------------------------------------------------------------------------
class ContentFilter:
    @staticmethod
    def clean(text):
        return re.sub(r"\s+", " ", str(text)).strip().lower()

    @classmethod
    def check(cls, title, abstract):
        t = cls.clean(title)
        a = cls.clean(abstract)
        full = t + " " + a
        words = len(abstract.split())

        if words < config.MIN_ABSTRACT_WORDS:
            return False, "too short"

        exclude = sum(1 for kw in config.EXCLUDE_KEYWORDS if kw in full)
        if exclude >= 2:
            return False, f"exclude {exclude}"

        core = sum(1 for kw in config.CORE_KEYWORDS if kw in full)
        if core == 0:
            return False, "no core"

        signal = sum(1 for kw in config.SIGNAL_KEYWORDS if kw in full)
        if signal >= 2:
            sig = "High Signal"
        elif signal == 1:
            sig = "Medium Signal"
        else:
            sig = "Standard"
        return True, sig

# ------------------------------------------------------------------------------
# 工具：DOI / 发布时间 / 期刊名
# ------------------------------------------------------------------------------
class DOIExtractor:
    @staticmethod
    def extract(entry):
        if hasattr(entry, "doi"):
            d = str(entry.doi).strip()
            if d.startswith("10."):
                return d
        txt = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()
        match = re.search(r"10\.\d{4,9}/[-._;/:a-z0-9]+", txt, re.I)
        if match:
            return match.group(0).strip()
        return ""

class PublishDateExtractor:
    @staticmethod
    def extract(entry):
        for key in ["published", "updated", "pubDate", "date"]:
            s = entry.get(key, "")
            if not s:
                continue
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            except:
                pass
            try:
                dt = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")
                return dt.strftime("%Y-%m-%d")
            except:
                continue
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def is_recent(entry, days=7):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        for key in ["published", "updated", "pubDate", "date"]:
            s = entry.get(key, "")
            if not s:
                continue
            try:
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                return dt >= cutoff
            except:
                pass
            try:
                dt = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")
                return dt >= cutoff
            except:
                continue
        return False

class JournalExtractor:
    @staticmethod
    def extract(feed_url, entry):
        url = feed_url.lower()
        if "nature.com" in url: return "Nature"
        if "cell.com" in url: return "Cell Press"
        if "science.org" in url or "sciencemag.org" in url: return "Science"
        if "pnas.org" in url: return "PNAS"
        if "arxiv.org" in url: return "arXiv"
        if "pubmed.ncbi.nlm.nih.gov" in url: return "PubMed"
        if "trends/cognitive-sciences" in url: return "Trends in Cognitive Sciences"
        if "neuron" in url: return "Neuron"
        if "current-biology" in url: return "Current Biology"
        if "behavioral-brain-research" in url: return "Behavioral Brain Research"
        if "sciencenews.org" in url: return "Science News"
        if "nature.com/nathumbehav" in url: return "Nature Human Behaviour"
        if "nature.com/neuro" in url: return "Nature Neuroscience"
        if "mit.edu" in url: return "MIT News"
        if "technologyreview.com" in url: return "MIT Technology Review"
        if "economist.com" in url: return "The Economist"
        if "scientificamerican.com" in url or "sciam.com" in url: return "Scientific American"
        if "behavioralscientist.org" in url: return "Behavioral Scientist"
        if "socialsciencespace.com" in url: return "Social Science Space"
        if "lse.ac.uk" in url: return "London School of Economics"
        if "apa.org" in url: return "APA"
        if "springer.com" in url: return "Springer"
        if "elsevier.com" in url: return "Elsevier"
        if "neurosciencenews.com" in url: return "Neuroscience News"
        if "knowingneurons.com" in url: return "Knowing Neurons"
        if "learningandthebrain.com" in url: return "Learning & the Brain"
        return "Academic Source"

# ------------------------------------------------------------------------------
# RSS 抓取：最近 7 天 + 全量遍历
# ------------------------------------------------------------------------------
class RSSFetcher:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def fetch_all_qualified(self):
        results = []
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    # 只保留最近 7 天的文章
                    if not PublishDateExtractor.is_recent(entry, days=7):
                        continue

                    title = entry.get("title", "")
                    raw_abs = entry.get("summary", "")
                    abstract = BeautifulSoup(raw_abs, "html.parser").get_text(strip=True)
                    ok, sig = ContentFilter.check(title, abstract)
                    if ok:
                        results.append((entry, feed_url, sig))
            except Exception as e:
                continue
        return results

# ------------------------------------------------------------------------------
# 主系统
# ------------------------------------------------------------------------------
class ModelCraftSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RSSFetcher()

    def run(self):
        print("=" * 70)
        print(" ModelCraft 最近 7 天全量扫描｜严格筛选不动 ")
        print("=" * 70)

        articles = self.fetcher.fetch_all_qualified()
        total_found = len(articles)
        print(f"✅ 最近 7 天符合条件文章总数：{total_found}")

        if total_found == 0:
            print("ℹ️ 无合格文章")
            return

        success = 0
        skipped = 0

        for entry, feed_url, signal_flag in articles:
            title = entry.get("title", "No Title")[:180]
            raw_abs = entry.get("summary", "")
            abstract = BeautifulSoup(raw_abs, "html.parser").get_text(strip=True)[:1919]
            source_url = entry.get("link", "")
            doi = DOIExtractor.extract(entry)
            published = PublishDateExtractor.extract(entry)
            journal = JournalExtractor.extract(feed_url, entry)
            ingested = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            if self.notion.is_duplicate(doi=doi, url=source_url):
                print(f"⏭️  已存在: {title[:50]}...")
                skipped += 1
                continue

            payload = {
                "parent": {"database_id": self.notion.database_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": title}}]},
                    "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
                    "Source_URL": {"url": source_url},
                    "Status": {"select": {"name": "Ingested"}},
                    "Scanned": {"checkbox": False},
                    "RSS_Feed_Tag": {"select": {"name": "Custom"}},
                    "Ingested_At": {"date": {"start": ingested}},
                    "Signal_Flag": {"select": {"name": signal_flag}},
                    "DOI": {"rich_text": [{"text": {"content": doi if doi else ""}}]},
                    "Published_Date": {"date": {"start": published}},
                    "Journal": {"rich_text": [{"text": {"content": journal}}]}
                }
            }

            if self.notion.create_page(payload):
                print(f"✅ [{journal}] {signal_flag}: {title[:50]}...")
                success += 1
            else:
                print(f"❌ 失败: {title[:50]}...")

        print("=" * 70)
        print(f"📊 结果：成功={success} | 跳过重复={skipped}")
        print("=" * 70)

if __name__ == "__main__":
    system = ModelCraftSystem()
    system.run()
