import asyncio
import re
from typing import Any
import httpx
from ai_engine import AIEngine
from providers import ALL_PROVIDERS, AI_PROVIDERS, KEYED_PROVIDERS

TIMEOUT = httpx.Timeout(12.0, connect=5.0)

class BloxyNexus:
    def __init__(self):
        self.providers = ALL_PROVIDERS
        self.ai = AIEngine()
        self.source_count = len(self.providers)
        self.ai_provider_count = len(AI_PROVIDERS)

    def provider_summary(self):
        return {
            "name": "Bloxy Nexus",
            "total": self.source_count,
            "render": len(KEYED_PROVIDERS),
            "browser_search": sum(1 for p in self.providers if p["group"] == "browser_search"),
            "keyless": sum(1 for p in self.providers if p["group"] == "keyless"),
            "ai_models": self.ai_provider_count,
        }

    def _route(self, q: str):
        s = q.lower()
        rules = {
            "sports": r"\b(sport|sports|football|soccer|basketball|tennis|nba|nfl|fifa|arsenal|chelsea|manchester|match|score|fixture|league)\b",
            "weather": r"\b(weather|temperature|forecast|rain|humidity|wind|climate)\b",
            "finance": r"\b(stock|share|forex|exchange rate|currency|crypto|bitcoin|market|nasdaq|s&p)\b",
            "news": r"\b(news|latest|today|breaking|headline|recent|yesterday)\b",
            "science": r"\b(science|physics|chemistry|biology|research|paper|study|scientific)\b",
            "books": r"\b(book|books|author|novel|isbn|literature)\b",
            "movies": r"\b(movie|film|actor|actress|tv|series|episode|cinema)\b",
            "location": r"\b(where|location|map|maps|address|near me|country|city|timezone)\b",
            "programming": r"\b(code|coding|programming|python|javascript|api|github|npm|bug|error)\b",
            "howto": r"\b(how do i|how to|steps|tutorial|guide|fix|install|setup)\b",
        }
        cats = [k for k, pat in rules.items() if re.search(pat, s)]
        return cats or ["general"]

    async def _direct_keyless(self, query: str, categories: list[str]):
        urls = []
        if "general" in categories or "science" in categories or "books" in categories:
            urls.append(("Wikipedia", "https://en.wikipedia.org/w/api.php", {"action":"query","list":"search","srsearch":query,"format":"json","srlimit":4}))
        if "books" in categories:
            urls.append(("Open Library", "https://openlibrary.org/search.json", {"q":query,"limit":4}))
        if "science" in categories:
            urls.append(("Crossref", "https://api.crossref.org/works", {"query.bibliographic":query,"rows":4}))
        if "weather" in categories:
            urls.append(("Open-Meteo", "https://geocoding-api.open-meteo.com/v1/search", {"name":query,"count":1,"language":"en","format":"json"}))
        if "location" in categories:
            urls.append(("Nominatim", "https://nominatim.openstreetmap.org/search", {"q":query,"format":"json","limit":3}))
        if "general" in categories or "programming" in categories:
            urls.append(("Stack Exchange", "https://api.stackexchange.com/2.3/search/advanced", {"order":"desc","sort":"relevance","q":query,"site":"stackoverflow","pagesize":4}))
        async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent":"Bloxy-bot/Bloxy-Nexus"}) as client:
            async def one(item):
                name, url, params = item
                try:
                    r = await client.get(url, params=params)
                    r.raise_for_status()
                    return {"source":name,"data":r.json()}
                except Exception:
                    return None
            results = await asyncio.gather(*(one(x) for x in urls))
        return [r for r in results if r]

    async def _web_fallback(self, query: str):
        return await self.ai.search_web(query)

    async def answer(self, query: str, conversation_id: str | None = None):
        categories = self._route(query)
        direct, web = await asyncio.gather(self._direct_keyless(query, categories), self._web_fallback(query))
        evidence = (direct + web)[:12]
        answer = await self.ai.generate(query, evidence, conversation_id)
        return {
            "answer": answer,
            "nexus": {"categories": categories, "sources_consulted": [x.get("source") for x in evidence], "source_count": self.source_count},
        }

    async def health(self):
        checks = {}
        async with httpx.AsyncClient(timeout=5) as client:
            for name, url in [("Wikipedia","https://en.wikipedia.org/w/api.php"),("Open-Meteo","https://api.open-meteo.com/v1/forecast"),("Open Library","https://openlibrary.org/search.json")]:
                try:
                    r = await client.get(url, params={"limit":1} if "openlibrary" in url else None)
                    checks[name] = r.status_code < 500
                except Exception:
                    checks[name] = False
        checks["Bloxy Nexus"] = True
        return checks
