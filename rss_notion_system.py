import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import config

# ----------------------------------------------------
# 类 1：Notion 客户端（负责写入数据库）
# ----------------------------------------------------
class NotionClient:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("DATABASE_ID")
        self.session = requests.Session()
        self.session.timeout = config.TIMEOUT

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": config.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def create_page(self, payload):
        url = "https://api.notion.com/v1/pages"
        try:
            response = self.session.post(
                url, headers=self.headers, json=payload, timeout=config.TIMEOUT
            )
            return response.status_code in (200, 201), response
        except Exception as e:
            return False, None

# ----------------------------------------------------
# 类 2：RSS 抓取器
# ----------------------------------------------------
class RssFetcher:
    def __init__(self):
        self.feed_urls = config.RSS_FEEDS

    def fetch(self):
        all_entries = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    all_entries.append((url, entry))
            except:
                continue
        return all_entries

# ----------------------------------------------------
# 类 3：文章处理器（清洗、分词、日期、标签）
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
        for key in ["published", "updated", "date"]:
            if hasattr(entry, key):
                val = getattr(entry, key)
                if len(val) >= 10:
                    return val[:10]
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def get_source_tag(feed_url):
        if "arxiv.org" in feed_url:
            return "arXiv"
        elif "nature.com" in feed_url:
            return "Nature"
        elif "pubmed.gov" in feed_url:
            return "PubMed"
        elif "cell.com" in feed_url:
            return "Cell"
        elif "mit.edu" in feed_url:
            return "MIT"
        else:
            return "Custom"

# ----------------------------------------------------
# 主系统：串联所有功能
# ----------------------------------------------------
class RssToNotionSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.fetcher = RssFetcher()
        self.processor = ArticleProcessor()

    def run(self):
        print("=" * 60)
        print("🚀 自动化内容系统 | 类+配置架构 已启动")
        print("=" * 60)

        entries = self.fetcher.fetch()

        for feed_url, entry in entries:
            title = entry.get("title", "No Title")
            raw_abstract = entry.get("summary", "")
            abstract = self.processor.clean(raw_abstract)
            word_count = self.processor.word_count(abstract)

            print(f"📝 {word_count} 词 | {title[:60]}")

            if word_count >= config.MIN_ABSTRACT_WORDS:
                print(f"✅ 达标（≥{config.MIN_ABSTRACT_WORDS} 词），开始写入 Notion...")
                self._send_entry(feed_url, entry)
                if config.SEND_ONLY_ONE:
                    print("\n🎉 任务完成：已发送 1 篇")
                    return

        print("\nℹ️ 未找到符合条件的文章")

def _send_entry(self, feed_url, entry):
    title = entry.get("title", "No Title")[:200]
    abstract = self.processor.clean(entry.get("summary", ""))[:2000]
    source_url = entry.get("link", "")
    published = self.processor.extract_date(entry)
    tag = self.processor.get_source_tag(feed_url)
    ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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
            "Status": {
                "select": {"name": "Ingested"}
            }
        }
    }

    success, res = self.notion.create_page(payload)
    if success:
        print("✅ 成功写入 Notion 数据库！")
    else:
        # 打印真实错误
        if res is not None:
            print("❌ Notion 返回错误：", res.status_code)
            print("📛 错误信息：", res.text[:1000])
        else:
            print("❌ 网络或连接异常")

# ----------------------------------------------------
# 运行
# ----------------------------------------------------
if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
