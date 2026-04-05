# ======================================
# 自动化内容系统 | 配置文件
# 以后所有参数、RSS、规则都在这里修改
# ======================================


# ======================================
# 关键字筛选系统 | TIER 1/2/3
# ======================================

# ----------------------
# TIER 1：必须命中（核心词）
# ----------------------
CORE_KEYWORDS = [
    # Cognitive Science
    "cognitive bias", "mental model", "heuristic", "cognitive load", "decision making",
    "dual process", "metacognition", "working memory", "attention", "perception",
    "executive function", "cognitive flexibility", "framing effect", "anchoring bias",
    "confirmation bias", "sunk cost", "cognitive dissonance",
    "reasoning", "judgment", "inference", "belief updating", "mental representation",
    "schema", "prototype theory", "category learning", "concept formation",

    # Systems Thinking
    "systems thinking", "feedback loop", "emergence", "complex adaptive system",
    "nonlinear dynamics", "network effects", "tipping point", "self-organization",
    "chaos theory", "cascading failure", "resilience", "agent-based model",
    "second-order effect", "complexity", "interdependence", "system dynamics",
    "leverage point", "bottleneck", "reinforcing loop", "balancing loop",

    # Learning Science
    "learning", "memory consolidation", "spaced repetition", "retrieval practice",
    "desirable difficulty", "interleaving", "sleep and memory", "neuroplasticity",
    "skill acquisition", "expertise", "forgetting curve", "transfer learning",
    "growth mindset", "deliberate practice",
    "encoding", "recall", "recognition", "long-term memory", "episodic memory",
    "semantic memory", "attention and learning", "motivation and learning",

    # Behavioral Science
    "behavioral economics", "nudge", "social norm", "conformity", "social influence",
    "cooperation", "trust", "reciprocity", "status seeking", "group behavior",
    "collective intelligence", "social contagion", "polarization", "moral psychology",
    "prosocial behavior", "incentive",
    "altruism", "in-group bias", "out-group", "social identity", "impression management",
    "bystander effect", "diffusion of responsibility",

    # Neuroscience
    "dopamine", "reward system", "stress response", "cortisol", "default mode network",
    "prefrontal cortex", "amygdala", "habit formation", "sleep", "prediction error",
    "emotional regulation", "brain plasticity",

    # Entrepreneurship
    "entrepreneurship", "innovation", "startup", "organizational learning", "leadership",
    "team dynamics", "creativity", "risk perception", "overconfidence", "failure",
    "network", "grit", "self-efficacy",
    "psychological safety", "organizational culture", "pivot", "product market fit",
    "scaling", "founder mindset",

    # Wealth & Finance
    "financial decision", "wealth", "loss aversion", "present bias", "scarcity mindset",
    "mental accounting", "inequality", "saving behavior", "investment behavior",
    "status", "time preference",

    # AI × Cognition
    "human-AI interaction", "AI decision making", "automation bias", "cognitive offloading",
    "algorithm aversion", "AI literacy", "large language model", "human oversight",
    "intelligence augmentation"
]

# ----------------------
# TIER 2：高传播信号词
# ----------------------
SIGNAL_KEYWORDS = [
    "paradox", "counterintuitive", "surprising", "unexpected", "illusion", "myth",
    "irrational", "hidden", "invisible", "why people", "how humans", "what predicts",
    "when people", "despite", "more likely", "worse than"
]

# ----------------------
# TIER 3：排除词（命中≥2个直接拒绝）
# ----------------------
EXCLUDE_KEYWORDS = [
    # 临床医学
    "clinical trial", "patient", "diagnosis", "treatment", "drug", "medication",
    "dosage", "placebo", "randomized controlled", "cancer", "tumor", "disease",
    "syndrome", "symptom", "hospital", "therapy", "therapeutic", "rehabilitation",

    # 纯工程/技术
    "algorithm performance", "benchmark", "GPU", "training loss", "backpropagation",
    "dataset", "compiler", "optimization algorithm", "hardware",

    # 纯数学/统计
    "regression analysis", "statistical method", "meta-regression",

    # 生物
    "gene expression", "protein", "genome", "cell", "cortical thickness", "EEG artifact",

    # 地域政策过强
    "policy implementation", "government program", "public health intervention"
]

# 基础配置
MIN_ABSTRACT_WORDS = 150
NOTION_VERSION = "2022-06-28"
TIMEOUT = 15

# RSS 源不变
RSS_FEEDS = [
    "https://neurosciencenews.com/feed/",
    "news.mit.edu/feed/rss.xml",
    # 你原来的全部 RSS
]

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
