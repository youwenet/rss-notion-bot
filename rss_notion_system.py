import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import config

# ----------------------------------------------------
# Notion 客户端
# ----------------------------------------------------
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
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=20
            )
            return response.status_code in (200, 201), response
        except Exception as e:
            print("💥 请求异常:", str(e))
            return False, None

# ----------------------------------------------------
# RSS 抓取
# ----------------------------------------------------
class RssFetcher:
    def __init__(self):
        self.feed_urls = config.RSS_FEEDS

    def fetch(self):
        entries = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    entries.append((url, entry))
            except:
                continue
        return entries

# ----------------------------------------------------
# 文章处理
# ----------------------------------------------------
class ArticleProcessor:
    @staticmethod
    def clean(html):
        if not html:
            return ""
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

    @staticmethod
    def word_count(text):
        return len([w for w in text.split() if w.strip()])

    @staticmethod
    def extract_date(entry):
        for k in ["published", "updated", "date"]:
            if hasattr(entry, k):
                s = getattr(entry, k)
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

# ----------------------------------------------------
# 主系统
# ----------------------------------------------------
class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.proc = ArticleProcessor()

    def run(self):
        print("=" * 60)
        print("🚀 自动化内容系统 | 类+配置架构")
        print("=" * 60)

        entries = self.fetcher.fetch()

        for feed_url, entry in entries:
            title = entry.get("title", "No Title")
            abstract_raw = entry.get("summary", "")
            abstract_clean = self.proc.clean(abstract_raw)
            wc = self.proc.word_count(abstract_clean)

            print(f"📝 {wc} 词 | {title[:60]}")

            if wc >= config.MIN_ABSTRACT_WORDS:
                print(f"✅ 达标，写入 Notion...")
                self.send_entry(feed_url, entry)
                return

        print("ℹ️ 未找到符合条件文章")

    def send_entry(self, feed_url, entry):
        title = entry.get("title", "No Title")[:190]
        abstract = self.proc.clean(entry.get("summary", ""))[:1900]
        source_url = entry.get("link", "")
        pub_date = self.proc.extract_date(entry)
        tag = self.proc.get_tag(feed_url)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        payload = {
            "parent": {"database_id": self.notion.database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Abstract": {
                    "rich_text": [{"text": {"content": abstract}}]
                },
                "Source_URL": {
                    "url": source_url
                },
                "Published_Date": {
                    "date": {"start": pub_date}
                },
                "RSS_Feed_Tag": {
                    "select": {"name": tag}
                },
                "Ingested_At": {
                    "date": {"start": now}
                },
                "Scanned": {
                    "checkbox": False
                },
                "Status": {
                    "select": {"name": "Ingested"}
                }
            }
        }

        ok, res = self.notion.create_page(payload)
        if ok:
            print("✅ 成功写入 Notion！")
        else:
            if res:
                print("❌ 状态码:", res.status_code)
                print("📛 返回:", res.text[:1000])

# ----------------------------------------------------
# 入口
# ----------------------------------------------------
if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
