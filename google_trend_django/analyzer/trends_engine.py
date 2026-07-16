"""
trends_engine.py
────────────────
All data logic for TrendPulse.
Works in two modes:
  DEMO MODE  — realistic simulated data (no API key needed)
  REAL MODE  — live Google Trends via RapidAPI / ScaleSerp / ValueSerp

To enable real data:
  1. Get a free key from rapidapi.com  (google-trends8 API, 500/month free)
  2. Set ACTIVE_API = "rapidapi"
  3. Paste your key in RAPIDAPI_KEY
"""

import random, math, time, re
import urllib.request, urllib.parse, json as _json

# ── CONFIG ────────────────────────────────────────────────────────────
ACTIVE_API   = "demo"   # "demo" | "rapidapi" | "scaleserp" | "valueserp"
RAPIDAPI_KEY  = ""      # from rapidapi.com   (google-trends8 API)
SCALESERP_KEY = ""      # from scaleserp.com
VALUESERP_KEY = ""      # from valueserp.com


def is_real_mode():
    if ACTIVE_API == "rapidapi"  and RAPIDAPI_KEY:  return True
    if ACTIVE_API == "scaleserp" and SCALESERP_KEY: return True
    if ACTIVE_API == "valueserp" and VALUESERP_KEY: return True
    return False


# ── IN-MEMORY CACHE (10 min TTL) ─────────────────────────────────────
_cache = {}
CACHE_TTL = 600

def cache_get(key):
    e = _cache.get(key)
    return e["d"] if e and time.time() - e["t"] < CACHE_TTL else None

def cache_set(key, data):
    _cache[key] = {"d": data, "t": time.time()}


# ════════════════════════════════════════════════════════════════════
#  REAL API CALLS
# ════════════════════════════════════════════════════════════════════
try:
    import requests as _req
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


def _rapidapi_get(endpoint, params):
    if not REQUESTS_OK:
        raise RuntimeError("requests library not installed")
    headers = {
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
        "X-RapidAPI-Host": "google-trends8.p.rapidapi.com"
    }
    r = _req.get(f"https://google-trends8.p.rapidapi.com/{endpoint}",
                 headers=headers, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _scaleserp_get(data_type, keyword, timeframe):
    if not REQUESTS_OK:
        raise RuntimeError("requests library not installed")
    r = _req.get("https://api.scaleserp.com/search", timeout=15, params={
        "api_key": SCALESERP_KEY, "search_type": "google_trends",
        "q": keyword, "trends_date": timeframe, "trends_data_type": data_type,
    })
    r.raise_for_status()
    return r.json()


def _valueserp_get(data_type, keyword, timeframe):
    if not REQUESTS_OK:
        raise RuntimeError("requests library not installed")
    r = _req.get("https://api.valueserp.com/search", timeout=15, params={
        "api_key": VALUESERP_KEY, "search_type": "google_trends",
        "q": keyword, "trends_date": timeframe, "trends_data_type": data_type,
    })
    r.raise_for_status()
    return r.json()


def fetch_real_trends(keyword, timeframe):
    """Returns (labels, values) from real Google Trends API."""
    if ACTIVE_API == "rapidapi":
        d        = _rapidapi_get("interest_over_time", {"keyword": keyword, "date": timeframe, "geo": "", "hl": "en"})
        timeline = d.get("default", {}).get("timelineData", [])
        labels   = [t.get("formattedTime", "") for t in timeline]
        values   = [t.get("value", [0])[0] for t in timeline]
        return labels, values

    if ACTIVE_API in ("scaleserp", "valueserp"):
        fn       = _scaleserp_get if ACTIVE_API == "scaleserp" else _valueserp_get
        d        = fn("interest_over_time", keyword, timeframe)
        timeline = d.get("interest_over_time", {}).get("timeline", [])
        return [t.get("date","") for t in timeline], [t.get("value",0) for t in timeline]

    raise RuntimeError("No valid API configured")


def fetch_real_regions(keyword, timeframe):
    """Returns (countries, values) from real Google Trends API."""
    if ACTIVE_API == "rapidapi":
        d       = _rapidapi_get("interest_by_region", {"keyword": keyword, "date": timeframe, "geo": "", "hl": "en", "resolution": "COUNTRY"})
        regions = d.get("default", {}).get("geoMapData", [])
        return [x.get("geoName","") for x in regions[:10]], [x.get("value",[0])[0] for x in regions[:10]]

    if ACTIVE_API in ("scaleserp", "valueserp"):
        fn      = _scaleserp_get if ACTIVE_API == "scaleserp" else _valueserp_get
        d       = fn("geo_map", keyword, timeframe)
        regions = d.get("geo_map", [])
        return [x.get("location","") for x in regions[:10]], [x.get("value",0) for x in regions[:10]]

    raise RuntimeError("No valid API configured")


def fetch_real_related(keyword, timeframe):
    """Returns (queries, values) from real Google Trends API."""
    if ACTIVE_API == "rapidapi":
        d   = _rapidapi_get("related_queries", {"keyword": keyword, "date": timeframe, "geo": "", "hl": "en"})
        top = d.get("default", {}).get("rankedList", [{}])[0].get("rankedKeyword", [])
        return [x.get("query","") for x in top[:8]], [x.get("value",0) for x in top[:8]]

    if ACTIVE_API in ("scaleserp", "valueserp"):
        fn  = _scaleserp_get if ACTIVE_API == "scaleserp" else _valueserp_get
        d   = fn("related_queries", keyword, timeframe)
        top = d.get("related_queries", {}).get("top", [])
        return [x.get("query","") for x in top[:8]], [x.get("value",0) for x in top[:8]]

    raise RuntimeError("No valid API configured")


def fetch_real_compare(kw1, kw2, timeframe):
    """Returns (labels, v1, v2) from real Google Trends API."""
    if ACTIVE_API == "rapidapi":
        d        = _rapidapi_get("interest_over_time", {"keyword": f"{kw1},{kw2}", "date": timeframe, "geo": "", "hl": "en"})
        timeline = d.get("default", {}).get("timelineData", [])
        labels   = [t.get("formattedTime","") for t in timeline]
        v1       = [t.get("value",[0,0])[0] for t in timeline]
        v2       = [t.get("value",[0,0])[1] if len(t.get("value",[]))>1 else 0 for t in timeline]
        return labels, v1, v2

    raise RuntimeError("Compare not supported for this API provider")


# ════════════════════════════════════════════════════════════════════
#  WIKIPEDIA GEO LOOKUP (for demo country detection)
# ════════════════════════════════════════════════════════════════════
def wikipedia_lookup(keyword):
    try:
        url  = ("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch="
                + urllib.parse.quote(keyword) + "&srlimit=1&format=json")
        req  = urllib.request.Request(url, headers={"User-Agent": "TrendPulse/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            results = _json.loads(r.read()).get("query",{}).get("search",[])
        if not results: return {}

        title = results[0]["title"]
        url2  = ("https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
                 "&exintro=1&explaintext=1&redirects=1&titles="
                 + urllib.parse.quote(title) + "&format=json")
        req2  = urllib.request.Request(url2, headers={"User-Agent": "TrendPulse/1.0"})
        with urllib.request.urlopen(req2, timeout=8) as r2:
            extract = next(iter(_json.loads(r2.read()).get("query",{}).get("pages",{}).values())).get("extract","")

        info = {}
        for pat in [r'\b(India|United States|United Kingdom|China|Pakistan|Bangladesh|Australia|Germany|France|Brazil|Japan|Russia|Canada|Sri Lanka|Nepal|Indonesia|Malaysia|Singapore|South Korea)\b']:
            m = re.search(pat, extract)
            if m: info["country"] = m.group(1); break
        for pat in [r'\b(Telangana|Andhra Pradesh|Maharashtra|Karnataka|Tamil Nadu|Kerala|Gujarat|Rajasthan|Uttar Pradesh|Bihar|West Bengal|Punjab|Haryana|Odisha|Assam|Goa)\b']:
            m = re.search(pat, extract)
            if m: info["state"] = m.group(1); break
        return info
    except:
        return {}


# ════════════════════════════════════════════════════════════════════
#  DEMO DATA ENGINE
# ════════════════════════════════════════════════════════════════════
KEYWORD_SEEDS = {
    "python":           {"base":72,"trend":+0.8,"peak_month":8},
    "javascript":       {"base":68,"trend":+0.3,"peak_month":3},
    "ai":               {"base":55,"trend":+3.5,"peak_month":11},
    "cricket":          {"base":40,"trend":+0.1,"peak_month":3},
    "ipl":              {"base":20,"trend":+1.2,"peak_month":4},
    "chatgpt":          {"base":60,"trend":+4.0,"peak_month":1},
    "java":             {"base":65,"trend":-0.5,"peak_month":6},
    "react":            {"base":58,"trend":+1.1,"peak_month":9},
    "machine learning": {"base":63,"trend":+2.0,"peak_month":10},
    "data science":     {"base":60,"trend":+1.8,"peak_month":9},
}

CATEGORY_MAP = {
    "programming_language": ["python","java","javascript","typescript","golang","rust","kotlin","swift","php","ruby","scala","c++","c#","dart","matlab"],
    "framework":    ["react","angular","vue","django","flask","spring","laravel","rails","express","nextjs","nuxt","fastapi","svelte","flutter","tensorflow","pytorch"],
    "game":         ["pubg","fortnite","minecraft","roblox","gta","valorant","chess","ludo","cod","fifa","pokemon","zelda","mario","free fire","bgmi"],
    "sport":        ["cricket","football","soccer","tennis","basketball","kabaddi","hockey","badminton","ipl","nba","nfl","f1","wrestling","boxing"],
    "movie_show":   ["netflix","amazon prime","hotstar","disney","movie","film","series","anime","bollywood","hollywood","ott","marvel","avengers"],
    "food":         ["biryani","pizza","burger","sushi","pasta","noodles","recipe","cooking","swiggy","zomato"],
    "place":        ["village","city","town","district","nagar","puram","pally","pet","guda","peta","mumbai","delhi","chennai","kolkata","bangalore","hyderabad","pune","siddipet","warangal","nizamabad","karimnagar"],
    "person":       ["virat","kohli","rohit","sharma","modi","rahul","sachin","dhoni","messi","ronaldo","trump","elon","musk","zuckerberg"],
    "technology":   ["ai","artificial intelligence","machine learning","deep learning","blockchain","cloud","cybersecurity","iot","5g","quantum","robotics","chatgpt","llm"],
    "education":    ["neet","jee","upsc","gate","cat","ssc","bank exam","college","university","degree","cbse","icse"],
    "finance":      ["stock","bitcoin","crypto","investment","mutual fund","sip","sensex","nifty","gold","rupee","dollar","trading","ipo"],
    "health":       ["covid","diabetes","cancer","blood pressure","yoga","gym","fitness","weight loss","medicine","doctor","hospital","ayurveda"],
    "weather":      ["rain","flood","cyclone","temperature","weather","climate","monsoon","drought","earthquake","tsunami","storm"],
    "job":          ["job","career","salary","resume","interview","linkedin","naukri","fresher","internship","remote"],
    "social_media": ["instagram","facebook","twitter","youtube","tiktok","snapchat","whatsapp","telegram","reddit","discord"],
}
PLACE_SUFFIXES = ["pally","peta","puram","nagar","guda","pet","kunta","varam","padu","abad","pur","garh","wadi","ganj","halli","palya","palli","patnam","dih","gaon","gram"]

def detect_category(kw):
    kl = kw.lower()
    for cat, kws in CATEGORY_MAP.items():
        for k in kws:
            if k in kl or kl == k: return cat
    for s in PLACE_SUFFIXES:
        if kl.endswith(s): return "place"
    return "unknown"

RELATED_FRAGMENTS = [
    # General interest patterns
    lambda kw: f"what is {kw}",
    lambda kw: f"{kw} meaning",
    lambda kw: f"{kw} definition",
    lambda kw: f"{kw} explained",
    lambda kw: f"{kw} overview",
    # News & trending
    lambda kw: f"{kw} news today",
    lambda kw: f"{kw} latest news 2025",
    lambda kw: f"{kw} trending now",
    lambda kw: f"{kw} update today",
    lambda kw: f"{kw} breaking news",
    # Learning & education
    lambda kw: f"learn about {kw}",
    lambda kw: f"{kw} tutorial",
    lambda kw: f"{kw} guide for beginners",
    lambda kw: f"{kw} complete guide",
    lambda kw: f"{kw} course online",
    lambda kw: f"how to learn {kw}",
    lambda kw: f"{kw} for dummies",
    # Comparison & alternatives
    lambda kw: f"{kw} vs alternatives",
    lambda kw: f"{kw} pros and cons",
    lambda kw: f"is {kw} good",
    lambda kw: f"{kw} review",
    lambda kw: f"best {kw} 2025",
    lambda kw: f"{kw} comparison",
    # India-specific
    lambda kw: f"{kw} in India",
    lambda kw: f"{kw} price in India",
    lambda kw: f"{kw} near me",
    lambda kw: f"{kw} in Hindi",
    lambda kw: f"{kw} in Telugu",
    # Social & media
    lambda kw: f"{kw} youtube",
    lambda kw: f"{kw} instagram",
    lambda kw: f"{kw} video",
    lambda kw: f"{kw} images",
    lambda kw: f"{kw} photos",
    # Knowledge
    lambda kw: f"{kw} wikipedia",
    lambda kw: f"{kw} history",
    lambda kw: f"{kw} facts",
    lambda kw: f"{kw} origin",
    lambda kw: f"{kw} examples",
    lambda kw: f"types of {kw}",
    lambda kw: f"{kw} categories",
    # Practical
    lambda kw: f"how to use {kw}",
    lambda kw: f"{kw} tips and tricks",
    lambda kw: f"{kw} online free",
    lambda kw: f"{kw} download",
    lambda kw: f"{kw} app",
    lambda kw: f"{kw} website",
    lambda kw: f"buy {kw} online",
    # Future / predictions
    lambda kw: f"{kw} future scope",
    lambda kw: f"{kw} prediction 2025",
    lambda kw: f"{kw} upcoming",
    lambda kw: f"{kw} trends 2025",
    lambda kw: f"future of {kw}",
    # Career / jobs
    lambda kw: f"{kw} jobs",
    lambda kw: f"{kw} salary",
    lambda kw: f"{kw} career",
    lambda kw: f"{kw} opportunities",
    # Questions
    lambda kw: f"why is {kw} popular",
    lambda kw: f"how does {kw} work",
    lambda kw: f"where to find {kw}",
    lambda kw: f"when was {kw} started",
    lambda kw: f"who created {kw}",
    lambda kw: f"{kw} benefits",
    lambda kw: f"{kw} advantages",
    lambda kw: f"{kw} problems",
]

RELATED_TEMPLATES = {
    "programming_language": [
        lambda kw: [(f"{kw} tutorial for beginners",100),(f"{kw} project ideas",92),(f"{kw} vs java",85),(f"best {kw} course 2025",80),(f"{kw} interview questions",76),(f"{kw} libraries",70),(f"{kw} salary india",65),(f"learn {kw} free",60)],
        lambda kw: [(f"{kw} documentation",100),(f"{kw} frameworks",93),(f"{kw} web development",86),(f"{kw} data science",80),(f"{kw} automation",74),(f"{kw} certification",68),(f"{kw} roadmap 2025",62),(f"{kw} github projects",56)],
        lambda kw: [(f"{kw} crash course",100),(f"{kw} cheat sheet",91),(f"{kw} for machine learning",84),(f"{kw} jobs remote",78),(f"{kw} vs python",72),(f"{kw} best IDE",66),(f"{kw} open source",60),(f"{kw} community",54)],
    ],
    "framework":    [
        lambda kw: [(f"{kw} tutorial",100),(f"{kw} vs alternatives",90),(f"{kw} documentation",85),(f"{kw} project example",80),(f"{kw} interview questions",74),(f"{kw} best practices",68),(f"{kw} latest version",62),(f"learn {kw} 2025",56)],
        lambda kw: [(f"{kw} getting started",100),(f"{kw} deployment",92),(f"{kw} performance",85),(f"{kw} authentication",78),(f"{kw} REST API",72),(f"{kw} testing",66),(f"{kw} vs competitors",60),(f"{kw} community",54)],
    ],
    "game":         [
        lambda kw: [(f"{kw} tips and tricks",100),(f"{kw} best settings",93),(f"{kw} update 2025",87),(f"{kw} characters guide",82),(f"{kw} download pc",76),(f"{kw} mobile version",70),(f"{kw} esports",64),(f"{kw} beginner guide",58)],
        lambda kw: [(f"{kw} gameplay",100),(f"{kw} walkthrough",93),(f"{kw} new season",86),(f"{kw} secret codes",80),(f"{kw} system requirements",74),(f"{kw} multiplayer",68),(f"{kw} ranking system",62),(f"{kw} mods",56)],
    ],
    "sport":        [
        lambda kw: [(f"{kw} live score",100),(f"{kw} schedule 2025",93),(f"{kw} world cup",87),(f"{kw} news today",82),(f"{kw} highlights",76),(f"{kw} india team",70),(f"best {kw} player",65),(f"{kw} rules",58)],
        lambda kw: [(f"{kw} results today",100),(f"{kw} upcoming matches",92),(f"{kw} rankings 2025",85),(f"{kw} records",78),(f"{kw} tickets online",72),(f"{kw} stadium",66),(f"{kw} history",60),(f"{kw} legend players",54)],
    ],
    "movie_show":   [lambda kw: [(f"{kw} new releases 2025",100),(f"{kw} best movies",92),(f"{kw} subscription price",86),(f"{kw} vs others",80),(f"{kw} download app",74),(f"{kw} free trial",68),(f"{kw} web series list",62),(f"{kw} login problem",55)]],
    "food":         [lambda kw: [(f"{kw} recipe",100),(f"best {kw} near me",93),(f"{kw} calories",86),(f"how to make {kw}",80),(f"{kw} ingredients",74),(f"{kw} restaurant",68),(f"homemade {kw}",62),(f"{kw} health benefits",55)]],
    "place":        [lambda kw: [(f"{kw} history",100),(f"{kw} population",93),(f"{kw} pincode",87),(f"{kw} district",82),(f"{kw} news",76),(f"{kw} map location",70),(f"{kw} gram panchayat",64),(f"{kw} tourist places",58)]],
    "person":       [lambda kw: [(f"{kw} biography",100),(f"{kw} net worth 2025",93),(f"{kw} latest news",87),(f"{kw} age",82),(f"{kw} family",76),(f"{kw} achievements",70),(f"{kw} interview",64),(f"{kw} social media",58)]],
    "technology":   [
        lambda kw: [(f"{kw} explained simply",100),(f"{kw} use cases 2025",92),(f"{kw} future trends",85),(f"{kw} top companies",78),(f"{kw} tools free",72),(f"{kw} jobs salary",66),(f"learn {kw} free",60),(f"{kw} vs traditional",54)],
        lambda kw: [(f"{kw} certification",100),(f"{kw} for beginners",92),(f"{kw} real world examples",85),(f"{kw} online course",78),(f"{kw} research papers",72),(f"{kw} startups 2025",66),(f"{kw} open source",60),(f"{kw} challenges",54)],
    ],
    "education":    [lambda kw: [(f"{kw} syllabus 2025",100),(f"{kw} preparation tips",93),(f"{kw} cut off marks",87),(f"{kw} eligibility",82),(f"{kw} application form",76),(f"{kw} result date",70),(f"{kw} best coaching",64),(f"{kw} previous papers",58)]],
    "finance":      [lambda kw: [(f"{kw} price today",100),(f"{kw} prediction 2025",92),(f"how to invest in {kw}",86),(f"{kw} risk",80),(f"{kw} returns",74),(f"{kw} vs gold",68),(f"{kw} news",62),(f"best {kw} to buy",56)]],
    "health":       [lambda kw: [(f"{kw} symptoms",100),(f"{kw} treatment",93),(f"{kw} causes",87),(f"{kw} prevention",82),(f"{kw} diet plan",76),(f"{kw} medicine",70),(f"{kw} home remedies",64),(f"{kw} doctor near me",58)]],
    "weather":      [lambda kw: [(f"{kw} forecast today",100),(f"{kw} warning",93),(f"{kw} affected areas",87),(f"{kw} live update",82),(f"{kw} relief",76),(f"{kw} news",70),(f"{kw} 2025",64),(f"{kw} safety tips",58)]],
    "job":          [lambda kw: [(f"{kw} vacancies 2025",100),(f"{kw} salary",93),(f"{kw} requirements",87),(f"{kw} apply online",82),(f"{kw} interview tips",76),(f"{kw} work from home",70),(f"{kw} fresher",64),(f"best {kw} sites",58)]],
    "social_media": [lambda kw: [(f"{kw} followers tips",100),(f"{kw} download",93),(f"{kw} new features 2025",87),(f"{kw} login problem",82),(f"{kw} vs others",76),(f"{kw} monetization",70),(f"{kw} privacy settings",64),(f"{kw} web version",58)]],
}


def demo_related(keyword):
    """Generate varied related queries. For known categories, rotates among
    multiple template pools. For unknown keywords, builds a unique set from
    a large pool of 60+ query fragments hashed by the keyword."""
    kl  = keyword.lower()
    cat = detect_category(kl)
    rng = random.Random(sum(ord(c) for c in kl))

    if cat in RELATED_TEMPLATES:
        # Pick one of multiple template variants based on keyword hash
        templates = RELATED_TEMPLATES[cat]
        variant   = rng.randint(0, len(templates) - 1)
        pool      = templates[variant](keyword)
        data = sorted([(q, max(10, s + rng.randint(-8, 5))) for q, s in pool], key=lambda x: -x[1])
        return [q for q, _ in data[:8]], [s for _, s in data[:8]]

    # Unknown category: build unique related queries from the large fragment pool
    shuffled = list(range(len(RELATED_FRAGMENTS)))
    rng.shuffle(shuffled)
    selected = shuffled[:12]  # pick 12, then score and keep top 8

    queries = []
    for idx in selected:
        q = RELATED_FRAGMENTS[idx](keyword)
        score = rng.randint(45, 100)
        queries.append((q, score))

    queries.sort(key=lambda x: -x[1])
    queries = queries[:8]

    # Normalize: top query gets ~100
    if queries:
        top = queries[0][1]
        queries = [(q, min(100, int(s * 100 / top))) for q, s in queries]

    return [q for q, _ in queries], [s for _, s in queries]


COUNTRY_POOLS = {
    "programming_language": [("India",95),("United States",93),("China",78),("Germany",72),("United Kingdom",68),("Russia",65),("Brazil",60),("France",55),("Canada",52),("Australia",48)],
    "game":       [("United States",100),("China",95),("South Korea",90),("India",82),("Brazil",76),("Germany",70),("Russia",65),("Japan",60),("United Kingdom",55),("France",50)],
    "sport":      [("India",100),("Pakistan",90),("Australia",80),("England",75),("South Africa",70),("Sri Lanka",65),("Bangladesh",62),("New Zealand",55),("West Indies",50),("Zimbabwe",44)],
    "technology": [("United States",100),("China",95),("India",82),("United Kingdom",75),("Germany",70),("South Korea",68),("Israel",65),("Singapore",60),("Canada",58),("Japan",55)],
    "education":  [("India",100),("United States",75),("United Kingdom",68),("Australia",62),("Canada",58),("Germany",54),("Singapore",50),("Malaysia",46),("New Zealand",42),("South Africa",38)],
    "finance":    [("United States",100),("United Kingdom",88),("India",75),("Germany",68),("China",65),("Japan",62),("Singapore",58),("Australia",54),("Canada",50),("France",46)],
    "place":      [("India",100),("Pakistan",45),("United Kingdom",35),("United States",30),("Canada",28),("Australia",25),("UAE",22),("Malaysia",18),("Singapore",15),("Germany",12)],
    "default":    [("India",90),("United States",75),("United Kingdom",60),("Australia",55),("Canada",50),("Germany",45),("France",40),("Brazil",35),("Japan",30),("South Korea",28)],
}

def _get_seed(kw):
    kl = kw.lower()
    for k, v in KEYWORD_SEEDS.items():
        if k in kl: return v
    h = sum(ord(c) for c in kl)
    return {"base":45+(h%40),"trend":(h%10)*0.3-1.5,"peak_month":h%12+1}

def demo_trends(keyword, timeframe):
    from datetime import datetime, timedelta
    seed = _get_seed(keyword)
    pts  = {"now 1-H":60,"now 7-d":168,"today 1-m":30,"today 12-m":52,"today 5-y":260}
    n    = pts.get(timeframe, 52)
    rng  = random.Random(sum(ord(c) for c in keyword.lower()))
    now  = datetime.now()
    labels, values = [], []
    for i in range(n):
        if   timeframe=="now 1-H":   dt=now-timedelta(minutes=n-i); lbl=dt.strftime("%H:%M")
        elif timeframe=="now 7-d":   dt=now-timedelta(hours=n-i);   lbl=dt.strftime("%b %d %H:00")
        elif timeframe=="today 1-m": dt=now-timedelta(days=n-i);    lbl=dt.strftime("%b %d")
        elif timeframe=="today 5-y": dt=now-timedelta(weeks=n-i);   lbl=dt.strftime("%Y-%m-%d")
        else:                         dt=now-timedelta(weeks=n-i);   lbl=dt.strftime("%b %d, %Y")
        val = int(max(1,min(100, seed["base"]+seed["trend"]*(i/n)*15+12*math.sin(2*math.pi*(i/n-seed["peak_month"]/12))+rng.gauss(0,5))))
        labels.append(lbl); values.append(val)
    return labels, values

def demo_regions(keyword):
    cat  = detect_category(keyword)
    info = wikipedia_lookup(keyword) if cat in ("place","unknown","person","sport","food","education") else {}
    pool = COUNTRY_POOLS.get(cat, COUNTRY_POOLS["default"])
    rng  = random.Random(sum(ord(c) for c in keyword.lower()))
    fc   = info.get("country",""); fs = info.get("state","")
    if fc:
        filtered = [(c,s) for c,s in pool if c!=fc]
        result   = [(fc,100)] + [(c,max(8,s-45+rng.randint(-5,5))) for c,s in filtered[:9]]
        result.sort(key=lambda x:-x[1])
        result   = [(fc,100)] + [(c,s) for c,s in result if c!=fc][:9]
        label    = f"📍 {fc}" + (f" ({fs})" if fs else "")
        result[0]= (label, 100)
        return [c for c,_ in result], [s for _,s in result]
    data = sorted([(c,max(8,s+rng.randint(-10,10))) for c,s in pool], key=lambda x:-x[1])
    return [c for c,_ in data[:10]], [s for _,s in data[:10]]




# ════════════════════════════════════════════════════════════════════
#  TREND PREDICTION (simple linear regression on tail data)
# ════════════════════════════════════════════════════════════════════

def predict_trend(values, n_predict=8):
    """Simple linear regression on the last 30% of data to forecast n_predict points."""
    if len(values) < 4:
        return [], []
    tail = values[-(len(values) // 3):]
    n = len(tail)
    x_mean = (n - 1) / 2
    y_mean = sum(tail) / n
    num = sum((i - x_mean) * (tail[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den != 0 else 0
    intercept = y_mean - slope * x_mean

    predicted = []
    for i in range(n_predict):
        val = intercept + slope * (n + i)
        val = max(0, min(100, round(val, 1)))
        predicted.append(val)
    return predicted


# ════════════════════════════════════════════════════════════════════
#  AI TREND SUMMARY (rule-based natural-language analysis)
# ════════════════════════════════════════════════════════════════════

def generate_summary(keyword, trends_data, regions_data, related_data):
    """Generate a natural-language AI summary from the analysis data."""
    values   = trends_data.get("values", [])
    avg      = trends_data.get("average", 0)
    peak     = trends_data.get("peak", 0)
    labels   = trends_data.get("labels", [])
    countries = regions_data.get("countries", [])
    c_values  = regions_data.get("values", [])
    queries   = related_data.get("queries", [])

    if not values:
        return {"summary": "No data available for analysis.", "insights": []}

    # ── Trend direction ─────────────────────
    first_q = values[:len(values)//4] if len(values) >= 4 else values[:1]
    last_q  = values[-(len(values)//4):] if len(values) >= 4 else values[-1:]
    first_avg = sum(first_q) / len(first_q) if first_q else 0
    last_avg  = sum(last_q) / len(last_q) if last_q else 0
    change = last_avg - first_avg

    if change > 10:
        direction = "strong upward"
        emoji = "📈"
        outlook = "This keyword shows significant growing interest and is likely to continue trending upward."
    elif change > 3:
        direction = "moderate upward"
        emoji = "📈"
        outlook = "Interest is gradually increasing, suggesting sustained relevance."
    elif change > -3:
        direction = "stable"
        emoji = "➡️"
        outlook = "Interest remains consistent, indicating a mature and established topic."
    elif change > -10:
        direction = "slight downward"
        emoji = "📉"
        outlook = "There's a minor decline in interest, which could be seasonal or cyclical."
    else:
        direction = "significant downward"
        emoji = "📉"
        outlook = "Interest is declining notably. This may indicate a shift in user attention."

    # ── Volatility ──────────────────────────
    if len(values) > 2:
        diffs = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        volatility = sum(diffs) / len(diffs)
    else:
        volatility = 0

    if volatility > 15:
        vol_text = "highly volatile with sharp spikes and drops"
    elif volatility > 8:
        vol_text = "moderately volatile with noticeable fluctuations"
    else:
        vol_text = "relatively stable with consistent interest levels"

    # ── Peak detection ──────────────────────
    peak_idx = values.index(peak) if peak in values else 0
    peak_label = labels[peak_idx] if peak_idx < len(labels) else "unknown"

    # ── Build insights list ─────────────────
    insights = []

    # 1. Overall trend
    insights.append({
        "icon": emoji,
        "title": "Trend Direction",
        "text": f'"{keyword}" shows a {direction} trend over the selected period with an average interest score of {avg}/100.'
    })

    # 2. Peak insight
    insights.append({
        "icon": "🎯",
        "title": "Peak Interest",
        "text": f"Peak interest of {peak}/100 was reached around {peak_label}. The trend pattern is {vol_text}."
    })

    # 3. Geographic insight
    if countries and c_values:
        top3 = list(zip(countries[:3], c_values[:3]))
        geo_text = ", ".join(f"{c} ({v})" for c, v in top3)
        insights.append({
            "icon": "🌍",
            "title": "Geographic Distribution",
            "text": f"Highest interest comes from {geo_text}. {'This shows strong concentration in a few key markets.' if c_values[0] > 80 else 'Interest is well-distributed globally.'}"
        })

    # 4. Related context
    if queries:
        top_q = queries[:3]
        insights.append({
            "icon": "🔗",
            "title": "Search Context",
            "text": f'People searching for "{keyword}" also frequently search for: {", ".join(top_q)}. This reveals user intent patterns.'
        })

    # 5. Outlook
    insights.append({
        "icon": "🔮",
        "title": "Forecast & Outlook",
        "text": outlook
    })

    # Build summary paragraph
    summary = (
        f'Analysis of "{keyword}": The search interest shows a {direction} trend '
        f'with an average score of {avg} and peak of {peak} (around {peak_label}). '
        f'The pattern is {vol_text}. '
    )
    if countries:
        summary += f'Top interest comes from {countries[0]}. '
    summary += outlook

    return {"summary": summary, "insights": insights}


# ════════════════════════════════════════════════════════════════════
#  COUNTRY ISO CODES (for heatmap)
# ════════════════════════════════════════════════════════════════════

COUNTRY_ISO = {
    "India": "IN", "United States": "US", "United Kingdom": "GB",
    "China": "CN", "Germany": "DE", "France": "FR", "Brazil": "BR",
    "Japan": "JP", "Russia": "RU", "Canada": "CA", "Australia": "AU",
    "South Korea": "KR", "Pakistan": "PK", "Bangladesh": "BD",
    "Indonesia": "ID", "Malaysia": "MY", "Singapore": "SG",
    "Sri Lanka": "LK", "Nepal": "NP", "South Africa": "ZA",
    "England": "GB", "New Zealand": "NZ", "West Indies": "JM",
    "Zimbabwe": "ZW", "Israel": "IL", "UAE": "AE",
    "Mexico": "MX", "Italy": "IT", "Spain": "ES", "Netherlands": "NL",
    "Turkey": "TR", "Thailand": "TH", "Vietnam": "VN",
    "Nigeria": "NG", "Egypt": "EG", "Kenya": "KE",
    "Argentina": "AR", "Colombia": "CO", "Chile": "CL", "Peru": "PE",
    "Philippines": "PH", "Taiwan": "TW", "Ireland": "IE",
    "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI",
    "Poland": "PL", "Switzerland": "CH", "Austria": "AT",
    "Belgium": "BE", "Portugal": "PT", "Czech Republic": "CZ",
    "Romania": "RO", "Hungary": "HU", "Greece": "GR",
    "Ukraine": "UA", "Saudi Arabia": "SA", "Iran": "IR", "Iraq": "IQ",
}


# ════════════════════════════════════════════════════════════════════
#  PUBLIC API — called by Django views
# ════════════════════════════════════════════════════════════════════

def get_trends(keyword, timeframe):
    ck = f"trends:{keyword}:{timeframe}"
    if (hit := cache_get(ck)): return hit
    try:
        if is_real_mode():
            labels, values = fetch_real_trends(keyword, timeframe)
        else:
            labels, values = demo_trends(keyword, timeframe)

        # Prediction
        predicted = predict_trend(values)
        pred_labels = [f"Forecast +{i+1}" for i in range(len(predicted))]

        result = {
            "keyword":          keyword,
            "labels":           labels,
            "values":           values,
            "average":          round(sum(values)/len(values), 1) if values else 0,
            "peak":             max(values) if values else 0,
            "predicted_labels": pred_labels,
            "predicted_values": predicted,
            "demo_mode":        not is_real_mode(),
        }
        cache_set(ck, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_regions(keyword, timeframe):
    ck = f"regions:{keyword}:{timeframe}"
    if (hit := cache_get(ck)): return hit
    try:
        if is_real_mode():
            countries, values = fetch_real_regions(keyword, timeframe)
        else:
            countries, values = demo_regions(keyword)
        # Add ISO codes for heatmap
        iso_codes = [COUNTRY_ISO.get(c.replace("📍 ", "").split(" (")[0], "") for c in countries]
        result = {"countries": countries, "values": values, "iso_codes": iso_codes}
        cache_set(ck, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_related(keyword, timeframe):
    ck = f"related:{keyword}:{timeframe}"
    if (hit := cache_get(ck)): return hit
    try:
        if is_real_mode():
            queries, values = fetch_real_related(keyword, timeframe)
        else:
            queries, values = demo_related(keyword)
        result = {"queries": queries, "values": values}
        cache_set(ck, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_compare(kw1, kw2, timeframe):
    ck = f"compare:{kw1}:{kw2}:{timeframe}"
    if (hit := cache_get(ck)): return hit
    try:
        if is_real_mode():
            labels, v1, v2 = fetch_real_compare(kw1, kw2, timeframe)
        else:
            l1,v1 = demo_trends(kw1, timeframe)
            l2,v2 = demo_trends(kw2, timeframe)
            n = min(len(l1),len(l2))
            labels,v1,v2 = l1[:n],v1[:n],v2[:n]
        result = {"labels": labels, "kw1": {"name": kw1, "values": v1}, "kw2": {"name": kw2, "values": v2}}
        cache_set(ck, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_multi(keywords, timeframe):
    """Get trend data for multiple keywords (up to 5)."""
    ck = f"multi:{'|'.join(keywords)}:{timeframe}"
    if (hit := cache_get(ck)): return hit
    try:
        datasets = []
        all_labels = None
        for kw in keywords[:5]:
            kw = kw.strip()
            if not kw:
                continue
            if is_real_mode():
                labels, values = fetch_real_trends(kw, timeframe)
            else:
                labels, values = demo_trends(kw, timeframe)
            if all_labels is None:
                all_labels = labels
            datasets.append({"name": kw, "values": values})
        result = {"labels": all_labels or [], "datasets": datasets}
        cache_set(ck, result)
        return result
    except Exception as e:
        return {"error": str(e)}


def get_summary(keyword, timeframe):
    """Generate AI summary by combining all analysis data."""
    try:
        trends  = get_trends(keyword, timeframe)
        regions = get_regions(keyword, timeframe)
        related = get_related(keyword, timeframe)
        if trends.get("error"):
            return {"error": trends["error"]}
        return generate_summary(keyword, trends, regions, related)
    except Exception as e:
        return {"error": str(e)}


def get_status():
    return {
        "mode":     "real" if is_real_mode() else "demo",
        "provider": ACTIVE_API,
    }

