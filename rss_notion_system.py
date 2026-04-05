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
        print("🚀 加回 Ingested_At")
        feed_url, entry = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 无文章")
            return

        title = entry.get("title", "Test")[:100]
        abstract = BeautifulSoup(entry.get("summary",""), "html.parser").get_text(strip=True)[:1500]
        source = entry.get("link", "")
        
        # 时间格式（Notion 标准）
        now = datetime.now(timezone.utc).isoformat()

        payload = {
            "parent": { "database_id": self.notion.database_id },
            "properties": {
                "Title": { "title": [{"text": {"content": title}}] },
                "Abstract": { "rich_text": [{"text": {"content": abstract}}] },
                "Source_URL": { "url": source },
                "Status": { "select": { "name": "Ingested" } },
                "Scanned": { "checkbox": False },
                "RSS_Feed_Tag": { "select": { "name": "Custom" } },
                
                # 加回最后一个
                "Ingested_At": { "date": { "start": now } }
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 全部字段都成功！")
        else:
            print("❌ 失败 → 问题在 Ingested_At")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
