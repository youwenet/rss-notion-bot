import os
import feedparser
import requests
from datetime import datetime, timedelta

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]

NOTION_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# RSS源
RSS_FEEDS = [
"https://rss.arxiv.org/rss/cs.AI",
"https://rss.arxiv.org/rss/cs.CY",
"https://rss.arxiv.org/rss/cs.HC",
"https://rss.arxiv.org/rss/cs.CL",
"https://www.sciencedaily.com/rss/mind_brain/psychology.xml",
"https://www.sciencedaily.com/rss/mind_brain/cognition.xml",
"https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml",
"https://www.sciencedaily.com/rss/mind_brain/learning.xml",
"https://rss.arxiv.org/rss/nlin.AO",
"https://rss.arxiv.org/rss/nlin.CD",
"https://rss.arxiv.org/rss/physics.soc-ph",
"https://www.nature.com/subjects/psychology.rss",
"https://www.nature.com/subjects/complex-systems.rss",
"https://www.pnas.org/rss/current.xml",
"https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science"
]

CORE_KEYWORDS = [
"cognitive bias","mental model","heuristic","decision making",
"dual process","metacognition","working memory","attention",
"feedback loop","emergence","systems thinking","complexity",
"learning","memory","spaced repetition","retrieval practice",
"behavioral economics","nudge","social norm","dopamine",
"reward system","habit formation","entrepreneurship",
"innovation","creativity","loss aversion"
]

SIGNAL_KEYWORDS = [
"paradox","counterintuitive","surprising","unexpected",
"illusion","myth","irrational","hidden","invisible",
"why people","how humans"
]

BLOCK_KEYWORDS = [
"clinical trial","patient","diagnosis","treatment",
"drug","cancer","tumor","disease","gene","protein",
"algorithm performance","benchmark","GPU"
]


def word_count(text):
    return len(text.split())


def contains_keyword(text, keywords):
    text = text.lower()
    return any(k in text for k in keywords)


def block_keyword_count(text):
    text = text.lower()
    return sum(1 for k in BLOCK_KEYWORDS if k in text)


def signal_score(text):
    text = text.lower()
    return sum(0.5 for k in SIGNAL_KEYWORDS if k in text)


def push_to_notion(title, abstract, url, score):

    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Abstract": {
                "rich_text": [{"text": {"content": abstract[:2000]}}]
            },
            "Source_URL": {
                "url": url
            },
            "Score": {
                "number": score
            },
            "Status":{
                "select":{"name":"New"}
            },
            "Published_Date":{
                "date":{"start":datetime.utcnow().isoformat()}
            }
        }
    }

    requests.post(NOTION_URL, headers=HEADERS, json=data)


def process_feed(feed_url):

    feed = feedparser.parse(feed_url)

    for entry in feed.entries:

        title = entry.title
        abstract = entry.summary
        url = entry.link

        text = (title + " " + abstract).lower()

        if word_count(abstract) < 180:
            continue

        if not contains_keyword(text, CORE_KEYWORDS):
            continue

        if block_keyword_count(text) >= 2:
            continue

        score = 5 + signal_score(text)

        push_to_notion(title, abstract, url, score)


def main():

    for feed in RSS_FEEDS:
        process_feed(feed)


if __name__ == "__main__":
    main()
