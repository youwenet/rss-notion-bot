import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
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
            print(f"⚠️ Notion 请求异常: {e}")
            return False

    def query_existing(self, doi=None, url=None):
        """智能去重：优先查DOI，没有再查URL"""
        filters = []
        
        if doi and doi.strip():
            filters.append({
                "property": "DOI",
                "rich_text": {"contains": doi.strip()}
            })
        
        if url and url.strip():
            filters.append({
                "property": "Source_URL",
                "url": {"equals": url.strip()}
            })

        if not filters:
            return False

        payload = {
            "filter": {
                "or": filters
            }
        }

        try:
            res = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            data = res.json()
            return len(data.get("results", [])) > 0
        except:
            return False

# ------------------------------------------------------------------------------
# 三层关键词筛选引擎
# ------------------------------------------------------------------------------
class ContentFilter:
    @staticmethod
    def clean_text(s):
        return re.sub(r'\s+', ' ', str(s)).strip().lower()

    @classmethod
    def should_ingest(cls, title, abstract):
        title_clean = cls.clean_text(title)
        abs_clean = cls.clean_text(abstract)
        full_text = title_clean + " " + abs_clean
        word_count = len(abstract.split())

        if word_count < config.MIN_ABSTRACT_WORDS:
            return False, f"字数不足 ({word_count})"

        exclude_hits = sum(1 for kw in config.EXCLUDE_KEYWORDS if kw in full_text)
        if exclude_hits >= 2:
            return False, f"排除词命中 {exclude_hits} 个"

        core_hits = sum(1 for kw in config.CORE_KEYWORDS if kw in full_text)
        if core_hits == 0:
            return False, "无核心关键词"

        signal_hits = sum(1 for kw in config.SIGNAL_KEYWORDS if kw in full_text)
        if signal_hits >= 2:
            signal_flag = "High Signal"
        elif signal_hits == 1:
            signal_flag = "Medium Signal"
        else:
            signal_flag = "Standard"

        return True, signal_flag

# ------------------------------------------------------------------------------
# DOI 提取工具
# ------------------------------------------------------------------------------
class DOIExtractor:
    @staticmethod
    def extract(entry):
        # 从 entry 字段取
        if hasattr(entry, "doi") and entry.doi:
            return entry.doi.strip()

        # 从摘要提取
        text = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True).lower()
        match = re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", text)
        if match:
            return match.group(0).strip()

        # 从链接提取
        link = entry.get("link", "")
        match = re.search(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", link.lower())
        if match:
            return match.group(0).strip()

        return ""

# ------------------------------------------------------------------------------
# RSS 抓取
# ------------------------------------------------------------------------------
class RSSCollector:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def fetch_best_article(self):
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    abstract = BeautifulSoup(summary, "html.parser").get_text(strip=True)

                    ok, reason = ContentFilter.should_ingest(title, abstract)
                    if ok:
                        return entry, reason
            except:
                continue
        return None, None

# ------------------------------------------------------------------------------
# 主系统
# ------------------------------------------------------------------------------
class ModelCraftContentSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.collector = RSSCollector()

    def run(self):
        print("=" * 70)
        print(" ModelCraft 自动化内容筛选 + 智能去重系统 v1.0 ")
        print("=" * 70)

        entry, signal_flag = self.collector.fetch_best_article()
        if not entry:
            print("ℹ️ 未找到符合条件的文章")
            return

        title = entry.get("title", "No Title")[:180]
        raw_abstract = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)
        abstract = raw_abstract[:1500]
        source_url = entry.get("link", "")
        doi = DOIExtractor.extract(entry)
        ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 去重判断
        if self.notion.query_existing(doi=doi, url=source_url):
            print("✅ 已存在，跳过重复文章")
            return

        # 写入 Notion
        payload = {
            "parent": {"database_id": self.notion.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
                "Source_URL": {"url": source_url},
                "Status": {"select": {"name": "Ingested"}},
                "Scanned": {"checkbox": False},
                "RSS_Feed_Tag": {"select": {"name": "Custom"}},
                "Ingested_At": {"date": {"start": ingested_at}},
                "Signal_Flag": {"select": {"name": signal_flag}},
                "DOI": {"rich_text": [{"text": {"content": doi if doi else ""}}]}
            }
        }

        if self.notion.create_page(payload):
            print(f"✅ 写入成功 | {signal_flag}")
            print(f"标题: {title[:70]}...")
            print(f"DOI: {doi if doi else '无'}")
        else:
            print("❌ 写入 Notion 失败")

if __name__ == "__main__":
    system = ModelCraftContentSystem()
    system.run()
