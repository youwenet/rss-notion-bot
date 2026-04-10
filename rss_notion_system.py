import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import config

# ------------------------------------------------------------------------------
# 【双模式切换：自动 / 手动】
# ------------------------------------------------------------------------------
MODE = "manual"          # 每日自动任务用：auto
# MODE = "manual"      # 你手动测试用：manual

# 仅手动模式下生效：
MANUAL_START_DATE = "2026-04-01"
MANUAL_END_DATE   = "2026-04-11"

# 自动模式下抓取最近 N 天（默认2天，覆盖昨日+今日，永不漏文）
AUTO_RECENT_DAYS = 2

# ------------------------------------------------------------------------------
# Notion API 客户端
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Notion API 客户端（已开启错误详情，直接告诉你哪里错）
# ------------------------------------------------------------------------------
class NotionClient:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("DATABASE_ID_PAPER")
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
            # --------------------------
            # 🔥 这里会打印真实错误！
            # --------------------------
            if r.status_code not in (200, 201):
                print(f"\n❌ API 错误详情: {r.json()}")  # 直接显示真实原因
            return r.status_code in (200, 201)
        except Exception as e:
            print(f"\n⚠️ 网络/配置异常: {e}")
            return False

    def is_duplicate(self, doi=None, url=None):
        filters = []
        if doi and doi.strip():
            filters.append({"property": "doi", "rich_text": {"equals": doi.strip()}})
        if url and url.strip():
            filters.append({"property": "source_url", "url": {"equals": url.strip()}})
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
        except Exception as e:
            print(f"\n⚠️ 去重检查失败: {e}")
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

        link = entry.get("link", "")
        if "arxiv.org/abs/" in link or "arxiv.org/pdf/" in link:
            arxiv_id = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9\.]+)", link)
            if arxiv_id:
                return f"10.48550/arXiv.{arxiv_id.group(1)}"

        txt = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()
        match = re.search(r"10\.\d{4,9}/[-._;/:a-z0-9]+", txt + " " + link, re.I)
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
        if MODE == "auto":
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=AUTO_RECENT_DAYS)
            dt = PublishDateExtractor.parse_entry_date(entry)
            return dt is not None and dt >= cutoff
        else:
            start = datetime.strptime(MANUAL_START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end = datetime.strptime(MANUAL_END_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            dt = PublishDateExtractor.parse_entry_date(entry)
            return dt is not None and start <= dt <= end

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
# RSS 抓取
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
        if MODE == "auto":
            print(f" ModelCraft｜自动模式：最近 {AUTO_RECENT_DAYS} 天")
        else:
            print(f" ModelCraft｜手动模式：{MANUAL_START_DATE} → {MANUAL_END_DATE}")
        print("=" * 70)

        articles = self.fetcher.fetch_all_qualified()
        total_found = len(articles)
        print(f"✅ 符合条件文章：{total_found}")

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

            # RSS 来源标签
            feed_lower = feed_url.lower()
            if "arxiv.org" in feed_lower:
                rss_tag = "arXiv"
            elif "pubmed" in feed_lower:
                rss_tag = "PubMed"
            elif "nature" in feed_lower:
                rss_tag = "Nature"
            elif "ssrn" in feed_lower:
                rss_tag = "SSRN"
            else:
                rss_tag = "Custom"

            # 抓取质量（完全匹配你数据库：Complete 完整 / Partial 缺字段 / Error 失败）
            if title and abstract and source_url and published:
                ingestion_quality = "Complete 完整"
            else:
                ingestion_quality = "Partial 缺字段"

            # 去重
            if self.notion.is_duplicate(doi=doi, url=source_url):
                print(f"⏭️ [{idx}/{total_found}] 已存在: {title[:50]}...")
                skipped += 1
                continue

            # 日期处理
            published_date_prop = {"date": {"start": published}} if published else None

            # ==============================
            # 🔥 100% 匹配你最新 DB1 46 字段
            # ==============================
            payload = {
                "parent": {"database_id": self.notion.database_id},
                "properties": {
                    # Layer 1 — INPUT 层（Python 写入 10 个）
                    "title": {"title": [{"text": {"content": title}}]},
                    "abstract": {"rich_text": [{"text": {"content": abstract}}]},
                    "source_url": {"url": source_url},
                    "doi": {"rich_text": [{"text": {"content": doi if doi else ""}}]},
                    "journal": {"rich_text": [{"text": {"content": journal}}]},
                    "published_date": published_date_prop,
                    "rss_feed_tag": {"select": {"name": rss_tag}},
                    "ingested_at": {"date": {"start": ingested}},
                    "ingestion_quality": {"select": {"name": ingestion_quality}},
                    "scanned": {"checkbox": False},

                    # Layer 2C — signal_flag
                    "signal_flag": {"select": {"name": signal_flag}},

                    # Layer 3 — 状态（完全匹配你数据库）
                    "status": {"select": {"name": "Ingested 采集"}},

                    # 2 个关联字段（无需写入，留空即可）
                    # associated model → 自动双向关联
                    # script_library → 自动双向关联
                }
            }

            # 写入
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
