import os
import time
import re
import feedparser
import requests
from datetime import datetime

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]

NOTION_URL = "https://api.notion.com/v1/pages"
QUERY_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

############################################################
# RSS SOURCES
############################################################

RSS_FEEDS = [

"https://rss.arxiv.org/rss/cs.AI",
"https://rss.arxiv.org/rss/cs.CY",
"https://rss.arxiv.org/rss/cs.HC",
"https://rss.arxiv.org/rss/cs.CL",
"https://rss.arxiv.org/rss/cs.SI",

"https://rss.arxiv.org/rss/nlin.AO",
"https://rss.arxiv.org/rss/nlin.CD",
"https://rss.arxiv.org/rss/physics.soc-ph",

"https://rss.arxiv.org/rss/q-bio.NC",
"https://rss.arxiv.org/rss/q-bio.PE",

"https://rss.arxiv.org/rss/stat.ML",

"https://www.nature.com/subjects/psychology.rss",
"https://www.nature.com/subjects/complex-systems.rss",
"https://www.nature.com/subjects/behavioural-sciences.rss",

"https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
"https://www.pnas.org/rss/current.xml",

"https://www.sciencedaily.com/rss/mind_brain/cognition.xml",
"https://www.sciencedaily.com/rss/mind_brain/psychology.xml",
"https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml",

"https://www.frontiersin.org/journals/psychology/rss",
"https://www.frontiersin.org/journals/neuroscience/rss",

"https://rss.ssrn.com/Behavioral-Economics.xml",
"https://rss.ssrn.com/Economics.xml",
"https://rss.ssrn.com/Management.xml",

"https://www.technologyreview.com/feed/",
"https://www.psypost.org/feed",
"https://aeon.co/feed.rss",
"https://www.quantamagazine.org/feed/",
"https://bigthink.com/feed/",
"https://hbr.org/feed",
"https://ssir.org/site/rss",
"https://behavioralscientist.org/feed/",
"https://nautil.us/feed/",
"https://www.edge.org/feed",
"https://www.brookings.edu/feed/",
"https://www.rand.org/topics/behavioral-science.rss",
"https://www.nber.org/rss/new.xml",

]

############################################################
# KEYWORDS
############################################################

CORE_KEYWORDS = [
"cognitive","decision","bias","mental model",
"system","complexity","learning","memory",
"behavior","psychology","social","neuroscience",
"innovation","entrepreneur","leadership",
"attention","habit","motivation","skill",
"AI","human AI","automation"
]

BLOCK_KEYWORDS = [
"cancer","tumor","gene","protein",
"clinical","patient","treatment",
"GPU","benchmark","dataset"
]

############################################################

def word_count(text):
    return len(text.split())

def contains_keyword(text):
    text = text.lower()
    return any(k in text for k in CORE_KEYWORDS)

def block_keyword(text):
    text = text.lower()
    return any(k in text for k in BLOCK_KEYWORDS)

############################################################
# GET EXISTING URLS (dedup)
############################################################

def get_existing_urls():

    urls = set()
    has_more = True
    start_cursor = None

    while has_more:

        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        r = requests.post(QUERY_URL, headers=HEADERS, json=payload)
        data = r.json()

        for page in data["results"]:

            props = page["properties"]

            if "Source_URL" in props and props["Source_URL"]["url"]:
                urls.add(props["Source_URL"]["url"])

        has_more = data["has_more"]
        start_cursor = data.get("next_cursor")

    return urls

############################################################
# DOI extraction
############################################################

def extract_doi(text):

    match = re.search(r'10.\d{4,9}/[-._;()/:A-Z0-9]+', text, re.I)

    if match:
        return match.group(0)

    return ""

############################################################
# PUSH TO NOTION
############################################################

def push_to_notion(title, abstract, url, journal, doi, rss_tag):

    data = {

        "parent": {"database_id": DATABASE_ID},

        "properties": {

            "Title": {
                "title": [
                    {"text": {"content": title}}
                ]
            },

            "Abstract": {
                "rich_text": [
                    {"text": {"content": abstract[:2000]}}
                ]
            },

            "Source_URL": {
                "url": url
            },

            "Journal": {
                "rich_text":[
                    {"text":{"content": journal}}
                ]
            },

            "DOI": {
                "rich_text":[
                    {"text":{"content": doi}}
                ]
            },

            "RSS_Feed_Tag":{
                "select":{
                    "name": rss_tag
                }
            },

            "Status":{
                "select":{
                    "name":"Ingested"
                }
            },

            "Published_Date":{
                "date":{
                    "start":datetime.utcnow().isoformat()+"Z"
                }
            },

            "Ingested_At":{
                "date":{
                    "start":datetime.utcnow().isoformat()+"Z"
                }
            },

            "Scanned":{
                "checkbox":False
            }

        }
    }

    r = requests.post(NOTION_URL, headers=HEADERS, json=data)

    if r.status_code != 200:
        print("ERROR:", r.text)

    time.sleep(0.35)

############################################################
# PROCESS RSS
############################################################

def process_feed(feed_url, existing_urls):

    pushed = 0

    feed = feedparser.parse(feed_url)

    rss_tag = feed.feed.get("title","RSS")

    for entry in feed.entries:

        title = entry.get("title","")
        abstract = entry.get("summary","")
        url = entry.get("link","")

        if not url or url in existing_urls:
            continue

        text = (title + " " + abstract)

        if word_count(abstract) < 150:
            continue

        if not contains_keyword(text):
            continue

        if block_keyword(text):
            continue

        doi = extract_doi(text)

        journal = entry.get("source",{}).get("title","Unknown")

        push_to_notion(title, abstract, url, journal, doi, rss_tag)

        pushed += 1

    return pushed

############################################################
# MAIN
############################################################

def main():

    print("Loading existing URLs...")

    existing_urls = get_existing_urls()

    print("Existing:", len(existing_urls))

    total_pushed = 0

    for feed in RSS_FEEDS:

        try:

            pushed = process_feed(feed, existing_urls)

            print("Feed done:", pushed)

            total_pushed += pushed

        except Exception as e:

            print("Feed error:", e)

    print("Total pushed:", total_pushed)

############################################################

if __name__ == "__main__":
    main()
