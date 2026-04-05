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
        except Exception as e:
            print("错误:", e)
            return False

class RssFetcher:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def get_first_valid(self):
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    abstract = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)
                    words = len(abstract.split())
                    if words >= config.MIN_ABSTRACT_WORDS:
                        return url, entry
            except:
                continue
        return None, None

class ArticleUtils:
    @staticmethod
    def extract_published_date(entry):
        for key in ["published", "updated", "date"]:
            if hasattr(entry, key):
                s = getattr(entry, key)
                if len(s) >= 10:
                    return s[:10]
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def get_tag(feed_url):
        if "arxiv.org" in feed_url: return "arXiv"
        if "nature.com" in feed_url: return "Nature"
        if "pubmed.gov" in feed_url: return "PubMed"
        if "cell.com" in feed_url: return "Cell"
        return "Custom"

class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.utils = ArticleUtils()

    def run(self):
        print("🚀 最终完整版 · 所有字段正常")
        feed_url, entry = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 未找到符合条件文章")
            return

        title = entry.get("title", "No Title")[:200]
        # 放大摘要到 1900 字符，足够打分
        abstract = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)[:1900]
        source_url = entry.get("link", "")
        published_date = self.utils.extract_published_date(entry)
        tag = self.utils.get_tag(feed_url)
        ingested_at = datetime.now(timezone.utc).isoformat()

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
                "Published_Date": { "date": { "start": published_date } }
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 全部字段写入成功！")
        else:
            print("❌ 写入失败")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
