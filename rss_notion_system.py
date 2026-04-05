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
            r = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=20
            )
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
                    if words >= 100:  # 降低门槛，确保能抓到
                        return url, entry
            except:
                continue
        return None, None

class ArticleUtils:
    @staticmethod
    def safe_date(entry):
        for k in ["published", "updated", "date"]:
            if hasattr(entry, k):
                val = getattr(entry, k)
                if len(val) >= 10:
                    return val[:10]
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def extract_doi(entry):
        if hasattr(entry, "doi"):
            return entry.doi
        if "doi:" in entry.get("summary", ""):
            return entry.get("summary").split("doi:")[-1].split()[0]
        return ""

    @staticmethod
    def journal(feed_url):
        if "arxiv.org" in feed_url: return "arXiv"
        if "nature.com" in feed_url: return "Nature"
        if "pubmed.gov" in feed_url: return "PubMed"
        if "cell.com" in feed_url: return "Cell"
        if "mit.edu" in feed_url: return "MIT"
        return "Unknown"

class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.utils = ArticleUtils()

    def run(self):
        print("🚀 最终完整版 · 所有字段正常")
        feed_url, entry = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 无文章")
            return

        title = entry.get("title", "No Title")[:150]
        abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)[:1500]
        source_url = entry.get("link", "")
        published = self.utils.safe_date(entry)
        journal = self.utils.journal(feed_url)
        doi = self.utils.extract_doi(entry)
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
                "Published_Date": { "date": { "start": published } },
                "Journal": { "rich_text": [{"text": {"content": journal}}] },
                "DOI": { "rich_text": [{"text": {"content": doi}}] }
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 全部写入成功！")
            print("📅 日期:", published)
            print("📰 期刊:", journal)
            print("🔗 DOI:", doi)
        else:
            print("❌ 失败")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
