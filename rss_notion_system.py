import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import config

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
            r = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload, timeout=15)
            return r.status_code in (200, 201)
        except:
            return False

class ArticleFilter:
    @staticmethod
    def should_ingest(title, abstract):
        text = (title + " " + abstract).lower()
        word_count = len(abstract.split())

        # 字数太少
        if word_count < config.MIN_ABSTRACT_WORDS:
            return False, "too short"

        # TIER 3：排除（≥2 个直接拒绝）
        exclude_count = sum(1 for kw in config.EXCLUDE_KEYWORDS if kw in text)
        if exclude_count >= 2:
            return False, f"excluded ({exclude_count})"

        # TIER 1：必须命中核心词
        core_count = sum(1 for kw in config.CORE_KEYWORDS if kw in text)
        if core_count == 0:
            return False, "no core keyword"

        # TIER 2：信号标记
        signal_count = sum(1 for kw in config.SIGNAL_KEYWORDS if kw in text)
        if signal_count >= 2:
            flag = "High Signal"
        elif signal_count == 1:
            flag = "Medium Signal"
        else:
            flag = "Standard"

        return True, flag

class RssFetcher:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def get_qualified_article(self):
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    raw_abs = entry.get("summary", "")
                    abstract = BeautifulSoup(raw_abs, "html.parser").get_text(strip=True)
                    ok, reason = ArticleFilter.should_ingest(title, abstract)
                    if ok:
                        return entry, reason
            except:
                continue
        return None, None

class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()

    def run(self):
        print("🚀 ModelCraft Content Filter + Notion Writer")
        entry, signal_flag = self.fetcher.get_qualified_article()
        if not entry:
            print("ℹ️ no qualified article")
            return

        title = entry.get("title")[:150]
        abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)[:1500]
        source_url = entry.get("link", "")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        payload = {
            "parent": { "database_id": self.notion.database_id },
            "properties": {
                "Title": { "title": [{"text": {"content": title}}] },
                "Abstract": { "rich_text": [{"text": {"content": abstract}}] },
                "Source_URL": { "url": source_url },
                "Status": { "select": { "name": "Ingested" } },
                "Scanned": { "checkbox": False },
                "RSS_Feed_Tag": { "select": { "name": "Custom" } },
                "Ingested_At": { "date": { "start": now } },
                "Signal_Flag": { "select": { "name": signal_flag } }
            }
        }

        if self.notion.create_page(payload):
            print(f"✅ success | {signal_flag}")
        else:
            print("❌ failed")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
