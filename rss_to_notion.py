import os
import feedparser
import requests
from datetime import datetime

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]

NOTION_URL = "https://api.notion.com/v1/pages"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

############################################################
# 53 RSS SOURCES
############################################################

RSS_FEEDS = [

# arXiv Cognitive / AI
"https://rss.arxiv.org/rss/cs.AI",
"https://rss.arxiv.org/rss/cs.CY",
"https://rss.arxiv.org/rss/cs.HC",
"https://rss.arxiv.org/rss/cs.CL",
"https://rss.arxiv.org/rss/cs.SI",

# Complexity
"https://rss.arxiv.org/rss/nlin.AO",
"https://rss.arxiv.org/rss/nlin.CD",
"https://rss.arxiv.org/rss/physics.soc-ph",

# Quantitative biology
"https://rss.arxiv.org/rss/q-bio.NC",
"https://rss.arxiv.org/rss/q-bio.PE",

# Statistics / ML
"https://rss.arxiv.org/rss/stat.ML",

# Nature
"https://www.nature.com/subjects/psychology.rss",
"https://www.nature.com/subjects/complex-systems.rss",
"https://www.nature.com/subjects/behavioural-sciences.rss",

# Science
"https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",

# PNAS
"https://www.pnas.org/rss/current.xml",

# ScienceDaily
"https://www.sciencedaily.com/rss/mind_brain/cognition.xml",
"https://www.sciencedaily.com/rss/mind_brain/psychology.xml",
"https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml",
"https://www.sciencedaily.com/rss/mind_brain/learning.xml",

# Frontiers
"https://www.frontiersin.org/journals/psychology/rss",
"https://www.frontiersin.org/journals/neuroscience/rss",

# Behavioral Econ
"https://rss.ssrn.com/Behavioral-Economics.xml",

# Economics
"https://rss.ssrn.com/Economics.xml",

# Management
"https://rss.ssrn.com/Management.xml",

# MIT Tech Review
"https://www.technologyreview.com/feed/",

# PsyPost
"https://www.psypost.org/feed",

# Aeon Essays
"https://aeon.co/feed.rss",

# Quanta
"https://www.quantamagazine.org/feed/",

# BigThink
"https://bigthink.com/feed/",

# Harvard Business Review
"https://hbr.org/feed",

# Stanford Social Innovation
"https://ssir.org/site/rss",

# Behavioral Scientist
"https://behavioralscientist.org/feed/",

# Nautilus
"https://nautil.us/feed/",

# Edge
"https://www.edge.org/feed",

# Brookings
"https://www.brookings.edu/feed/",

# RAND
"https://www.rand.org/topics/behavioral-science.rss",

# NBER
"https://www.nber.org/rss/new.xml",

# Additional academic
"https://rss.arxiv.org/rss/econ.EM",
"https://rss.arxiv.org/rss/econ.TH",

]

############################################################
# CORE KEYWORDS
############################################################

CORE_KEYWORDS = [

# Cognitive Science
"cognitive bias","mental model","heuristic","cognitive load",
"decision making","dual process","metacognition","working memory",
"attention","perception","executive function","cognitive flexibility",
"framing effect","anchoring bias","confirmation bias","sunk cost",
"cognitive dissonance",

# Extensions
"reasoning","judgment","inference","belief updating",
"mental representation","schema","prototype theory",
"category learning","concept formation",

# Systems Thinking
"systems thinking","feedback loop","emergence",
"complex adaptive system","nonlinear dynamics",
"network effects","tipping point","self organization",
"chaos theory","cascading failure","resilience",
"agent based model","second order effect",
"complexity","interdependence","system dynamics",
"leverage point","bottleneck","reinforcing loop","balancing loop",

# Learning Science
"learning","memory consolidation","spaced repetition",
"retrieval practice","desirable difficulty","interleaving",
"sleep and memory","neuroplasticity","skill acquisition",
"expertise","forgetting curve","transfer learning",
"growth mindset","deliberate practice",

# Learning extensions
"encoding","recall","recognition","long term memory",
"episodic memory","semantic memory","attention and learning",

# Behavioral Science
"behavioral economics","nudge","social norm",
"conformity","social influence","cooperation",
"trust","reciprocity","status seeking","group behavior",
"collective intelligence","social contagion",
"polarization","moral psychology","prosocial behavior",
"incentive",

# Neuroscience
"dopamine","reward system","stress response",
"cortisol","default mode network","prefrontal cortex",
"amygdala","habit formation","sleep","prediction error",
"emotional regulation","brain plasticity",

# Entrepreneurship
"entrepreneurship","innovation","startup",
"organizational learning","leadership","team dynamics",
"creativity","risk perception","overconfidence",
"failure","network","grit","self efficacy",

# Wealth
"financial decision","wealth","loss aversion",
"present bias","scarcity mindset","mental accounting",
"inequality","saving behavior","investment behavior",
"status","time preference",

# AI cognition
"human AI interaction","AI decision making",
"automation bias","cognitive offloading",
"algorithm aversion","AI literacy",
"large language model","intelligence augmentation"
]

############################################################
# SIGNAL KEYWORDS
############################################################

SIGNAL_KEYWORDS = [
"paradox","counterintuitive","surprising","unexpected",
"illusion","myth","irrational","hidden","invisible",
"why people","how humans","what predicts","when people",
"despite","more likely","worse than"
]

############################################################
# BLOCK KEYWORDS
############################################################

BLOCK_KEYWORDS = [
"clinical trial","patient","diagnosis","treatment",
"drug","medication","dosage","placebo",
"cancer","tumor","disease","syndrome",
"gene expression","protein","genome","cell",
"algorithm performance","benchmark","GPU",
"dataset","compiler","hardware"
]

############################################################

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

############################################################

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
            "Source_URL": {"url": url},
            "Score": {"number": score},
            "Status":{"select":{"name":"New"}},
            "Published_Date":{
                "date":{"start":datetime.utcnow().isoformat()}
            }
        }
    }

    requests.post(NOTION_URL, headers=HEADERS, json=data)

############################################################

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

############################################################

def main():

    for feed in RSS_FEEDS:
        process_feed(feed)

############################################################

if __name__ == "__main__":
    main()
