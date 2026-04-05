import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import config

# ------------------------------------------------------------------------------
# Notion API 客户端
# ------------------------------------------------------------------------------
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
                timeout=config.TIMEOUT
            )
            return r.status_code in (200, 201)
        except Exception as e:
            print(f"⚠️ Notion 请求异常: {e}")
            return False

# ------------------------------------------------------------------------------
# 三层关键词筛选引擎
# ------------------------------------------------------------------------------
class ContentFilter:
    @staticmethod
    def clean_text(s):
        return re.sub(r'\s+', ' ', str(s)).strip().lower()

    @classmethod
    def should_ingest(cls, title, abstract):
        title_clean = cls.clean_text(title)
        abs_clean = cls.clean_text(abstract)
        full_text = title_clean + " " + abs_clean
        word_count = len(abstract.split())

        # 基础字数过滤
        if word_count < config.MIN_ABSTRACT_WORDS:
            return False, f"字数不足 ({word_count})"

        # Tier3：排除词 ≥2 直接拒绝
        exclude_hits = sum(1 for kw in config.EXCLUDE_KEYWORDS if kw in full_text)
        if exclude_hits >= 2:
            return False, f"排除词命中 {exclude_hits} 个"

        # Tier1：必须命中至少一个核心词
        core_hits = sum(1 for kw in config.CORE_KEYWORDS if kw in full_text)
        if core_hits == 0:
            return False, "无核心关键词"

        # Tier2：信号分级
        signal_hits = sum(1 for kw in config.SIGNAL_KEYWORDS if kw in full_text)
        if signal_hits >= 2:
            signal_flag = "High Signal"
        elif signal_hits == 1:
            signal_flag = "Medium Signal"
        else:
            signal_flag = "Standard"

        return True, signal_flag

# ------------------------------------------------------------------------------
# RSS 抓取 + 按规则筛选
# ------------------------------------------------------------------------------
class RSSCollector:
    def __init__(self):
        self.feeds = config.RSS_FEEDS

    def fetch_best_article(self):
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    abstract = BeautifulSoup(summary, "html.parser").get_text(strip=True)

                    ok, reason = ContentFilter.should_ingest(title, abstract)
                    if ok:
                        return entry, reason
            except Exception as e:
                continue
        return None, None

# ------------------------------------------------------------------------------
# 主系统入口
# ------------------------------------------------------------------------------
class ModelCraftContentSystem:
    def __init__(self):
        self.notion = NotionClient()
        self.collector = RSSCollector()

    def run(self):
        print("=" * 70)
        print(" ModelCraft 自动化内容筛选系统 v1.0 ")
        print("=" * 70)

        entry, signal_flag = self.collector.fetch_best_article()
        if not entry:
            print("ℹ️ 未找到符合条件的文章")
            return

        title = entry.get("title", "No Title")[:180]
        raw_abstract = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(strip=True)
        abstract = raw_abstract[:1500]
        source_url = entry.get("link", "")
        ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

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
                },
                "Scanned": {
                    "checkbox": False
                },
                "RSS_Feed_Tag": {
                    "select": {"name": "Custom"}
                },
                "Ingested_At": {
                    "date": {"start": ingested_at}
                },
                "Signal_Flag": {
                    "select": {"name": signal_flag}
                }
            }
        }

        if self.notion.create_page(payload):
            print(f"✅ 写入成功 | {signal_flag}")
            print(f"标题: {title[:80]}...")
        else:
            print("❌ 写入 Notion 失败")

if __name__ == "__main__":
    system = ModelCraftContentSystem()
    system.run()
