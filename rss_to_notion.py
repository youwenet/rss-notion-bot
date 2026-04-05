import os
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ===================== 配置项 =====================
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
NOTION_VERSION = "2022-06-28"

# 你要监听的 RSS 源（可自行添加多个）
RSS_FEEDS = [
    "https://www.nature.com/nature.rss",
    "https://arxiv.org/rss/cs.AI",
    # "https://pubmed.ncbi.nlm.nih.gov/rss/latest.xml",
    # "https://ssrn.com/rss/journals/1",
]

# 最小摘要词数
MIN_WORD_COUNT = 150

# 只发 1 条（满足条件就停止）
SEND_ONLY_ONE = True
# ===================================================

def clean_text(html_text):
    """清理 HTML，返回纯文本"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(strip=True)

def count_words(text):
    """统计英文单词数"""
    return len(text.split())

def get_rss_feed_tag(feed_url):
    """自动识别 RSS 来源标签（对应 Notion Select）"""
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
    """尝试从链接或摘要提取 DOI"""
    if "doi.org" in link:
        return link.split("doi.org/")[-1]
    if "doi:" in summary:
        parts = summary.split("doi:")[-1].split()
        return parts[0].strip()
    return ""

def extract_journal(feed_title, source_tag):
    """提取期刊名"""
    if source_tag == "Nature":
        return "Nature"
    if source_tag == "arXiv":
        return "arXiv"
    if source_tag == "PubMed":
        return "PubMed"
    return feed_title or "Unknown Journal"

def send_to_notion(entry, feed_tag, journal):
    """把单篇文章写入 Notion 数据库"""
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    title = entry.get("title", "No Title")
    raw_abstract = entry.get("summary", "")
    abstract = clean_text(raw_abstract)
    source_url = entry.get("link", "")
    doi = extract_doi(source_url, abstract)
    
    published = entry.get("published", "")
    ingested_at = datetime.utcnow().isoformat() + "Z"

    # Notion 字段严格匹配你的表结构
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Title": {
                "title": [{"text": {"content": title}}]
            },
            "Abstract": {
                "rich_text": [{"text": {"content": abstract[:2000]}}]  # Notion 限制长度
            },
            "Source_URL": {
                "url": source_url
            },
            "DOI": {
                "rich_text": [{"text": {"content": doi}}]
            },
            "Journal": {
                "rich_text": [{"text": {"content": journal}}]
            },
            "Published_Date": {
                "date": {"start": published[:10]} if published else None
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
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code in (200, 201):
        print(f"✅ 已发送到 Notion：{title}")
        return True
    else:
        print(f"❌ 发送失败：{response.status_code}")
        print(response.text)
        return False

# ===================== 主逻辑 =====================
def main():
    sent = False
    for feed_url in RSS_FEEDS:
        if sent:
            break
        print(f"\n🔍 正在解析 RSS：{feed_url}")
        feed = feedparser.parse(feed_url)
        feed_tag = get_rss_feed_tag(feed_url)
        journal = extract_journal(feed.feed.get("title"), feed_tag)

        for entry in feed.entries:
            abstract = clean_text(entry.get("summary", ""))
            word_count = count_words(abstract)

            print(f"📝 标题：{entry.get('title')[:80]}... | 词数：{word_count}")

            if word_count >= MIN_WORD_COUNT:
                success = send_to_notion(entry, feed_tag, journal)
                if success:
                    sent = True
                    if SEND_ONLY_ONE:
                        return

    if not sent:
        print("ℹ️ 没有找到符合条件的文章（摘要>150词）")

if __name__ == "__main__":
    main()
