import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

RSS_FEEDS = [
    "https://arxiv.org/rss/cs.AI",
    "https://www.nature.com/nature.rss",
]

MIN_WORD_COUNT = 100  # 先调低方便测试
SEND_ONLY_ONE = True


def clean_text(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(strip=True)


def count_words(text):
    return len(text.split())


def get_rss_feed_tag(feed_url):
    if "nature.com" in feed_url:
        return "Nature"
    elif "arxiv.org" in feed_url:
        return "arXiv"
    elif "pubmed.ncbi.nlm.nih.gov" in feed_url:
        return "PubMed"
    elif "ssrn.com" in feed_url:
        return "SSRN"
    else:
        return "Custom"


def extract_doi(link, summary):
    if link and "doi.org/" in link:
        return link.split("doi.org/")[-1].strip()
    if "doi:" in summary.lower():
        s = summary.lower().split("doi:")[-1]
        return s.split()[0].strip()
    return ""


def send_to_notion(entry, feed_tag):
    url = "https://api.notion.com/v1/pages"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "No Title")
    abstract_raw = entry.get("summary", "")
    abstract = clean_text(abstract_raw)
    source_url = entry.get("link", "")
    doi = extract_doi(source_url, abstract_raw)
    published = entry.get("published", "")

    ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 核心：只保留最稳定的字段，避免字段名/类型错误导致整条失败
    properties = {
        "Title": {
            "title": [{"text": {"content": title[:200]}}]
        },
        "Abstract": {
            "rich_text": [{"text": {"content": abstract[:2000]}}]
        },
        "Source_URL": {
            "url": source_url if source_url else None
        },
        "DOI": {
            "rich_text": [{"text": {"content": doi}}]
        },
        "RSS_Feed_Tag": {
            "select": {"name": feed_tag}
        },
        "Ingested_At": {
            "date": {"start": ingested_at}
        },
        "Scanned": {
            "checkbox": False
        },
        "Status": {
            "select": {"name": "Ingested"}
        }
    }

    # 日期字段如果为空就删掉，避免 Notion 报错
    if published and len(published) >= 10:
        properties["Published_Date"] = {"date": {"start": published[:10]}}

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }

    print("📤 发送到 Notion 数据预览：")
    print(f"Title: {title}")
    print(f"URL: {source_url}")

    r = requests.post(url, headers=headers, json=data)
    print(f"🔍 Notion 返回状态码: {r.status_code}")
    if r.status_code not in (200, 201):
        print("❌ Notion 错误信息：")
        print(r.text)
    return r.status_code in (200, 201)


def main():
    print("🚀 开始运行 RSS 抓取...")
    print(f"NOTION_API_KEY 存在: {bool(NOTION_API_KEY)}")
    print(f"DATABASE_ID 存在: {bool(DATABASE_ID)}")

    if not NOTION_API_KEY or not DATABASE_ID:
        print("❌ 密钥或数据库ID未读取到，请检查 GitHub Secrets")
        return

    sent = False
    for feed_url in RSS_FEEDS:
        if sent:
            break
        print(f"\n抓取: {feed_url}")
        feed = feedparser.parse(feed_url)
        if feed.bozo != 0:
            print("❌ RSS 解析错误")
            continue

        feed_tag = get_rss_feed_tag(feed_url)
        for entry in feed.entries[:10]:
            abstract = clean_text(entry.get("summary", ""))
            wc = count_words(abstract)
            print(f"词数: {wc} | {entry.get('title', '')[:60]}")

            if wc >= MIN_WORD_COUNT:
                ok = send_to_notion(entry, feed_tag)
                if ok:
                    print("✅ 成功发送到 Notion！")
                    sent = True
                    break
    if not sent:
        print("ℹ️ 未找到符合条件的文章或发送失败")


if __name__ == "__main__":
    main()
