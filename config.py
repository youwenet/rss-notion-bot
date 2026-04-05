# ======================================
# 自动化内容系统 | 配置文件
# 以后所有参数、RSS、规则都在这里修改
# ======================================

# Notion API
NOTION_VERSION = "2022-06-28"
TIMEOUT = 15

# 筛选规则
MIN_ABSTRACT_WORDS = 150  # 正式：150词
SEND_ONLY_ONE = True      # 只发1条

# RSS 订阅源（你全部的高质量源）
RSS_FEEDS = [
    "https://neurosciencenews.com/feed",
    "https://news.mit.edu/rss/topic/neuroscience",
    "https://knowingneurons.com/feed",
    "https://behavioralscientist.org/feed",
    "https://behavioraleconomics.com/feed",
    "https://socialsciencespace.com/feed",
    "https://blogs.lse.ac.uk/impactofsocialsciences/feed",
    "https://www.sciencenews.org/feed",
    "https://rss.sciam.com/ScientificAmerican",

    "https://arxiv.org/rss/cs.AI",
    "https://arxiv.org/rss/cs.LG",
    "https://arxiv.org/rss/stat.ML",
    "https://arxiv.org/rss/q-bio.NC",
    "https://arxiv.org/rss/q-bio.PE",
    "https://arxiv.org/rss/cs.CY",
    "https://arxiv.org/rss/cs.SI",
    "https://arxiv.org/rss/cs.GT",
    "https://arxiv.org/rss/physics.soc-ph",
    "https://arxiv.org/rss/physics.comp-ph",
    "https://arxiv.org/rss/physics.data-an",
    "https://arxiv.org/rss/econ.TH",
    "https://arxiv.org/rss/econ.EM",
    "https://arxiv.org/rss/econ.GN",
    "https://arxiv.org/rss/cs.CL",
    "https://arxiv.org/rss/cs.MA",
    "https://arxiv.org/rss/cs.IT",
    "https://arxiv.org/rss/cs.DS",

    "https://pubmed.ncbi.nlm.nih.gov/rss/search/decision%20making/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/behavioral%20science/",
    "https://pubmed.ncbi.nlm.nih.gov/rss/search/cognitive%20neuroscience/",

    "https://www.nature.com/neuro.rss",
    "https://www.nature.com/nathumbehav.rss",
    "https://www.sciencemag.org/rss/news/science-neuroscience",
    "https://www.pnas.org/rss/news",
    "https://www.cell.com/trends/cognitive-sciences/rss",
    "https://www.cell.com/current-biology/rss",
    "https://www.cell.com/neuron/rss",
    "https://www.apa.org/pubs/journals/xge/feed",
    "https://www.journals.elsevier.com/behavioral-brain-research/rss",
    "https://www.springer.com/journal/13415/rss",

    "https://arxiv.org/rss/cs.CC",
    "https://arxiv.org/rss/cs.NE",
    "https://arxiv.org/rss/q-bio.BM",
    "https://arxiv.org/rss/stat.AP",
    "https://arxiv.org/rss/cs.MS",

    "https://www.technologyreview.com/feed/",
    "https://www.economist.com/feeds/print-sections/233.xml",
    "https://learningandthebrain.com/blog/feed",
]
