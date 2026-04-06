import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import config

# ------------------------------------------------------------------------------
# 固定日期区间（你只改这里！）
# ------------------------------------------------------------------------------
START_DATE = "2025-12-01"
END_DATE = "2026-12-31"

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
# 严格筛选规则
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
# 工具类
# ------------------------------------------------------------------------------
class DOIExtractor:
    @staticmethod
    def extract(entry):
        if hasattr(entry, "doi"):
            d = str(entry.doi).strip()
            if d.startswith("10."):
                return d
        if hasattr(entry, "link"):
            link = entry.link
            doi_match = re.search(r"10\.\d{4,9}[^\s]*", link)
            if doi_match:
                return doi_match.group(0).strip()
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
        return None

    @staticmethod
    def parse_entry_date(entry):
        for key in ["published", "updated", "pubDate", "date"]:
            s = entry.get(key, "")
            if not s:
                continue
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00"))
            except:
                pass
            try:
                return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")
            except:
                continue
        return None

    @staticmethod
    def in_range(entry):
        start = datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(END_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        dt = PublishDateExtractor.parse_entry_date(entry)
        if not dt:
            return False
        return start <= dt <= end

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
        return "Academic Source"

# ------------------------------------------------------------------------------
# RSS 抓取：固定日期区间
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
                    if not PublishDateExtractor.in_range(entry):
                        continue
                    title = entry.get("title", "")
                    raw_abs = entry.get("summary", "")
                    abstract = BeautifulSoup(raw_abs, "html.parser").get_text(strip=True)
                    ok, sig = ContentFilter.check(title, abstract)
                    if ok:
                        results.append((entry, feed_url, sig))
            except:
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
        print(f" ModelCraft｜固定日期扫描：{START_DATE} → {END_DATE}")
        print("=" * 70)

        articles = self.fetcher.fetch_all_qualified()
        total_found = len(articles)
        print(f"✅ 该区间符合条件文章：{total_found}")

        if total_found == 0:
            print("ℹ️ 无合格文章")
            return

        success = 0
        skipped = 0

        for idx, (entry, feed_url, signal_flag) in enumerate(articles, 1):
            title = entry.get("title", "No Title")[:180]
            raw_abs = entry.get("summary", "")
            abstract = BeautifulSoup(raw_abs, "html.parser").get_text(strip=True)[:1919]
            source_url = entry.get("link", "")
            doi = DOIExtractor.extract(entry)
            published = PublishDateExtractor.extract(entry)
            journal = JournalExtractor.extract(feed_url, entry)
            ingested = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            feed_lower = feed_url.lower()
            if "arxiv.org" in feed_lower:
                rss_tag = "arXiv"
            elif "ssrn" in feed_lower:
                rss_tag = "SSRN"
            elif "pubmed" in feed_lower:
                rss_tag = "PubMed"
            elif "nature" in feed_lower:
                rss_tag = "Nature"
            else:
                rss_tag = "Custom"

            if self.notion.is_duplicate(doi=doi, url=source_url):
                print(f"⏭️ [{idx}/{total_found}] 已存在: {title[:50]}...")
                skipped += 1
                continue

            published_date_prop = {"date": {"start": published}} if published else None

            payload = {
                "parent": {"database_id": self.notion.database_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": title}}]},
                    "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
                    "Source_URL": {"url": source_url},
                    "Status": {"select": {"name": "Ingested"}},
                    "Scanned": {"checkbox": False},
                    "RSS_Feed_Tag": {"select": {"name": rss_tag}},
                    "Ingested_At": {"date": {"start": ingested}},
                    "Signal_Flag": {"select": {"name": signal_flag}},
                    "DOI": {"rich_text": [{"text": {"content": doi if doi else ""}}]},
                    "Published_Date": published_date_prop,
                    "Journal": {"rich_text": [{"text": {"content": journal}}]}
                }
            }

            if self.notion.create_page(payload):
                print(f"✅ [{idx}/{total_found}] [{rss_tag}] {signal_flag}: {title[:50]}...")
                success += 1
            else:
                print(f"❌ [{idx}/{total_found}] 失败: {title[:50]}...")

        print("=" * 70)
        print(f"📊 结果：成功写入={success} | 已重复跳过={skipped}")
        print("=" * 70)

if __name__ == "__main__":
    system = ModelCraftSystem()
    system.run()
