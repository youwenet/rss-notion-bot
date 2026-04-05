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
            r = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload, timeout=20)
            return r.status_code in (200, 201)
        except:
            return False

class RssFetcher:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def get_first_valid(self):
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)
                    words = len(abstract.split())
                    if words >= config.MIN_ABSTRACT_WORDS:
                        return url, entry
            except:
                continue
        return None, None

class ArticleUtils:
    @staticmethod
    def extract_published_date(entry):
        for key in ["published","updated","date"]:
            if hasattr(entry, key):
                s = getattr(entry, key)
                if len(s)>=10:
                    return s[:10]
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    @staticmethod
    def get_tag(feed_url):
        if "arxiv.org" in feed_url: return "arXiv"
        if "nature.com" in feed_url: return "Nature"
        if "pubmed.gov" in feed_url: return "PubMed"
        return "Custom"

class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.utils = ArticleUtils()

    def run(self):
        print("🚀 100% 必过版")
        feed_url, entry = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 无文章")
            return

        title = entry.get("title","Test")[:150]
        # ✅ 压到 1000，绝对安全
        abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)[:1000]
        source_url = entry.get("link","")
        pub_date = self.utils.extract_published_date(entry)
        tag = self.utils.get_tag(feed_url)
        ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        payload = {
            "parent": { "database_id": self.notion.database_id },
            "properties": {
                "Title": { "title": [{"text": {"content": title}}] },
                "Abstract": { "rich_text": [{"text": {"content": abstract}}] },
                "Source_URL": { "url": source_url },
                "Status": { "select": { "name": "Ingested" } },
                "Scanned": { "checkbox": False },
                "RSS_Feed_Tag": { "select": { "name": tag } },
                "Ingested_At": { "date": { "start": ingested_at } },
                "Published_Date": { "date": { "start": pub_date } }
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 全部写入成功！")
        else:
            print("❌ 失败")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
