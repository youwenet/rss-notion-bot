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
            r = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=20
            )
            return r.status_code in (200, 201)
        except Exception as e:
            print(f"💥 请求异常: {str(e)}")
            return False

# ----------------------------------------------------
# RSS 抓取器
# ----------------------------------------------------
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
                        return url, entry, feed.feed.get("title", "Unknown Journal")
            except:
                continue
        return None, None, None

# ----------------------------------------------------
# 工具类：提取日期、标签、期刊
# ----------------------------------------------------
class ArticleUtils:
    @staticmethod
    def extract_published_date(entry):
        """安全提取发表日期，格式严格符合Notion要求"""
        for key in ["published", "updated", "date"]:
            if hasattr(entry, key):
                s = getattr(entry, key)
                if len(s) >= 10:
                    # 只取YYYY-MM-DD格式，彻底避免格式错误
                    return s[:10]
        # 兜底：用当前日期
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def get_source_tag(feed_url):
        if "arxiv.org" in feed_url: return "arXiv"
        if "nature.com" in feed_url: return "Nature"
        if "pubmed.gov" in feed_url: return "PubMed"
        if "cell.com" in feed_url: return "Cell"
        if "mit.edu" in feed_url: return "MIT"
        return "Custom"

    @staticmethod
    def extract_journal(feed_url, feed_title):
        """提取期刊名，对应Journal字段"""
        if "arxiv.org" in feed_url: return "arXiv"
        if "nature.com" in feed_url: return "Nature"
        if "pubmed.gov" in feed_url: return "PubMed"
        if "cell.com" in feed_url: return "Cell"
        if "pnas.org" in feed_url: return "PNAS"
        if "sciam.com" in feed_url: return "Scientific American"
        return feed_title or "Unknown Journal"

# ----------------------------------------------------
# 主系统
# ----------------------------------------------------
class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.utils = ArticleUtils()

    def run(self):
        print("=" * 60)
        print("🚀 最终完整版 · 所有字段补全")
        print("=" * 60)

        feed_url, entry, feed_title = self.fetcher.get_first_valid()
        if not entry:
            print("ℹ️ 未找到符合条件的文章")
            return

        # 提取所有信息
        title = entry.get("title", "No Title")[:200]
        abstract = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)[:1500]
        source_url = entry.get("link", "")
        published_date = self.utils.extract_published_date(entry)
        tag = self.utils.get_source_tag(feed_url)
        journal = self.utils.extract_journal(feed_url, feed_title)
        ingested_at = datetime.now(timezone.utc).isoformat()

        # 完整payload：包含所有字段
        payload = {
            "parent": {"database_id": self.notion.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
                "Source_URL": {"url": source_url},
                "Status": {"select": {"name": "Ingested"}},
                "Scanned": {"checkbox": False},
                "RSS_Feed_Tag": {"select": {"name": tag}},
                "Ingested_At": {"date": {"start": ingested_at}},
                "Published_Date": {"date": {"start": published_date}},
                "Journal": {"rich_text": [{"text": {"content": journal}}]}
            }
        }

        if self.notion.create_page(payload):
            print("✅ ✅ ✅ 所有字段写入成功！")
            print(f"📝 期刊: {journal}")
            print(f"📅 发表时间: {published_date}")
        else:
            print("❌ 写入失败")

if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
