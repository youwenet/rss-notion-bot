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
            print(f"💥 请求异常: {str(e)}")
            return False, None

# ----------------------------------------------------
# RSS 抓取器
# ----------------------------------------------------
class RssFetcher:
    def __init__(self):
        self.feed_urls = config.RSS_FEEDS

    def fetch(self):
        entries = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                entries.extend((url, entry) for entry in feed.entries)
            except:
                continue
        return entries

# ----------------------------------------------------
# 文章处理器（核心：强制截断摘要）
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
        print("🚀 自动化内容系统 | 类+配置架构（已修复长度限制）")
        print("=" * 60)

        entries = self.fetcher.fetch()

        for feed_url, entry in entries:
            title = entry.get("title", "No Title")
            raw_abstract = entry.get("summary", "")
            abstract = self.proc.clean(raw_abstract)
            wc = self.proc.word_count(abstract)

            print(f"📝 {wc} 词 | {title[:60]}")

            if wc >= config.MIN_ABSTRACT_WORDS:
                print(f"✅ 达标（≥{config.MIN_ABSTRACT_WORDS} 词），开始写入 Notion...")
                self.send_entry(feed_url, entry)
                if config.SEND_ONLY_ONE:
                    print("\n🎉 任务完成：已发送 1 篇")
                    return

        print("\nℹ️ 未找到符合条件的文章")

    def send_entry(self, feed_url, entry):
        # ✅ 核心修复：强制截断，永远不超 Notion 限制
        title = entry.get("title", "No Title")[:200]  # 标题限200字符
        abstract = self.proc.clean(entry.get("summary", ""))[:1900]  # 摘要限1900字符（留冗余）
        source_url = entry.get("link", "")
        pub_date = self.proc.extract_date(entry)
        tag = self.proc.get_tag(feed_url)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        payload = {
            "parent": {"database_id": self.notion.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Abstract": {"rich_text": [{"text": {"content": abstract}}]},
                "Source_URL": {"url": source_url},
                "Published_Date": {"date": {"start": pub_date}},
                "RSS_Feed_Tag": {"select": {"name": tag}},
                "Ingested_At": {"date": {"start": now}},
                "Scanned": {"checkbox": False},
                "Status": {"select": {"name": "Ingested"}}
            }
        }

        ok, res = self.notion.create_page(payload)
        if ok:
            print("✅ 成功写入 Notion 数据库！")
        else:
            if res:
                print(f"❌ 错误码: {res.status_code}")
                print(f"📛 错误信息: {res.text[:800]}")

# ----------------------------------------------------
# 运行
# ----------------------------------------------------
if __name__ == "__main__":
    system = RssToNotionSystem()
    system.run()
