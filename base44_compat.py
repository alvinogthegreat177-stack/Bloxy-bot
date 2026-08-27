"""Base44-style live context compatibility layer for Bloxy Nexus.

Mirrors the important AI behavior of the Base44 Bloxy-bot client: parallel
meta-search, DuckDuckGo, Reddit and Wikipedia context before the LLM call.
It does not depend on Base44 credits or Base44 SDK credentials.
"""
import asyncio
from urllib.parse import quote_plus
import httpx

SEARX_INSTANCES = [
    "https://searx.tiekoetter.com",
    "https://search.bus-hit.me",
    "https://searx.be",
    "https://search.mdosch.de",
    "https://searx.divided-by-zero.eu",
    "https://searxng.site",
    "https://search.sapti.me",
    "https://searx.work",
    "https://search.ononoki.org",
]
SEARX_ENGINES = "google,bing,brave,duckduckgo,startpage,mojeek,qwant,ecosia,yandex,wikipedia,apple"

async def _get(url: str, *, params=None, timeout: float = 5.0, headers=None):
    try:
        h = {"User-Agent": "Bloxy-bot/1.0", "Accept": "application/json"}
        if headers:
            h.update(headers)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.get(url, params=params, headers=h)
            if r.status_code >= 400:
                return None
            return r.json()
    except Exception:
        return None

async def _searx(query: str):
    for base in SEARX_INSTANCES:
        data = await _get(
            f"{base}/search",
            params={"q": query, "format": "json", "categories": "general", "engines": SEARX_ENGINES, "pageno": 1},
        )
        if data and data.get("results"):
            rows = []
            for r in data["results"][:5]:
                title = r.get("title", "")
                content = (r.get("content") or "")[:350]
                url = r.get("url", "")
                rows.append(f"- {title}: {content} {url}".strip())
            return "Multi-engine search:\n" + "\n".join(rows)
    return ""

async def _ddg(query: str):
    data = await _get("https://api.duckduckgo.com/", params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1})
    if not data:
        return ""
    parts = []
    if data.get("AbstractText"):
        parts.append("DuckDuckGo: " + data["AbstractText"][:1800])
    topics = [x.get("Text") for x in data.get("RelatedTopics", []) if isinstance(x, dict) and x.get("Text")]
    if topics:
        parts.append("DuckDuckGo related:\n" + "\n".join(topics[:3]))
    return "\n".join(parts)

async def _reddit(query: str):
    data = await _get(
        "https://www.reddit.com/search.json",
        params={"q": query, "sort": "new", "limit": 3, "t": "month"},
        headers={"Accept": "application/json"},
    )
    children = ((data or {}).get("data") or {}).get("children") or []
    posts = []
    for child in children[:3]:
        d = child.get("data") or {}
        if d.get("title"):
            posts.append(f"- {d['title']} (r/{d.get('subreddit', '')})")
    return "Reddit recent:\n" + "\n".join(posts) if posts else ""

async def _wikipedia(query: str):
    data = await _get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(query),
        timeout=5.0,
    )
    if data and data.get("extract"):
        return "Wikipedia: " + data["extract"][:2500]
    return ""

async def _social(query: str):
    platforms = [
        ("Instagram", "instagram.com"), ("X/Twitter", "twitter.com"),
        ("TikTok", "tiktok.com"), ("Threads", "threads.net"),
        ("LinkedIn", "linkedin.com"), ("YouTube", "youtube.com"),
    ]
    async def one(name, site):
        data = await _get(
            "https://searx.tiekoetter.com/search",
            params={"q": f"site:{site} {query}", "format": "json", "categories": "general", "pageno": 1},
        )
        results = (data or {}).get("results") or []
        if not results:
            return ""
        lines = [f"- {r.get('title', '')}: {(r.get('content') or '')[:180]}" for r in results[:3]]
        return name + ":\n" + "\n".join(lines)
    values = await asyncio.gather(*(one(*p) for p in platforms), return_exceptions=True)
    return "\n\n".join(v for v in values if isinstance(v, str) and v)

async def gather_base44_live_context(query: str) -> str:
    """Gather the same classes of live context used by the Base44 client."""
    values = await asyncio.gather(
        _searx(query), _ddg(query), _reddit(query), _wikipedia(query), _social(query),
        return_exceptions=True,
    )
    parts = [v for v in values if isinstance(v, str) and v]
    return "\n\n".join(parts)[:14000]
