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
                    if words >= 150:
                        return url, entry
            except:
                continue
        return None, None

class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()

    def run(self):
        print("🚀 系统启动（极简必成功版）")
        feed_url, entry = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 无符合条件文章")
            return

        title = entry.get("title", "Test")[:100]
        abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)[:1500]
        source = entry.get("link", "")

        payload = {
            "parent": { "database_id": self.notion.database_id },
            "properties": {
                "Title": { "title": [{"text": {"content": title}}] },
                "Abstract": { "rich_text": [{"text": {"content": abstract}}] },
                "Source_URL": { "url": source },
                "Status": { "select": { "name": "Ingested" } }
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 成功写入 NOTION！！！")
        else:
            print("❌ 写入失败")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
