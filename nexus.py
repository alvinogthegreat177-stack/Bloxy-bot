"""Bloxy Nexus orchestration and provider adapter layer."""
import asyncio
import os
import re
from urllib.parse import quote_plus
import httpx
from ai_engine import AIEngine
from providers import PROVIDERS, AI_PROVIDERS

TIMEOUT = httpx.Timeout(9.0, connect=4.0)
UA = "Bloxy-bot/1.0 Bloxy-Nexus"

class BloxyNexus:
    def __init__(self):
        self.providers = PROVIDERS
        self.ai = AIEngine()
        self.source_count = len(PROVIDERS)
        self.ai_provider_count = len(AI_PROVIDERS)

    def provider_summary(self):
        return {
            "name": "Bloxy Nexus", "total": self.source_count,
            "render": sum(p.group == "render" for p in self.providers),
            "browser_search": sum(p.group == "browser_search" for p in self.providers),
            "keyless": sum(p.group == "keyless" for p in self.providers),
            "ai_models": self.ai_provider_count,
        }

    def _route(self, q):
        rules = {
            "sports": r"\b(football|soccer|basketball|tennis|nba|nfl|fifa|arsenal|chelsea|match|score|fixture|league|sport)\b",
            "weather": r"\b(weather|temperature|forecast|rain|humidity|wind|climate)\b",
            "finance": r"\b(stock|share|forex|exchange rate|currency|crypto|bitcoin|market|nasdaq|s&p|finance)\b",
            "news": r"\b(news|latest|today|breaking|headline|recent|yesterday)\b",
            "science": r"\b(science|physics|chemistry|biology|research|paper|study|scientific)\b",
            "books": r"\b(book|author|novel|isbn|literature)\b",
            "movies": r"\b(movie|film|actor|actress|tv|series|episode|cinema)\b",
            "location": r"\b(where|location|map|address|near me|country|city|timezone)\b",
            "programming": r"\b(code|coding|programming|python|javascript|api|github|npm|bug|error|software)\b",
            "howto": r"\b(how do i|how to|steps|tutorial|guide|fix|install|setup)\b",
        }
        s = q.lower()
        return [c for c, p in rules.items() if re.search(p, s)] or ["general"]

    def _relevant(self, p, cats):
        if p.group == "browser_search":
            return True
        buckets = {
            "sports": ("sport", "odds", "all sports"),
            "weather": ("weather", "open-meteo", "tomorrow", "timezone", "worldtime"),
            "finance": ("alpha", "exchange", "finnhub", "coin", "twelve", "wolfram"),
            "news": ("news", "guardian", "gnews", "media", "tavily", "exa", "search"),
            "science": ("wikipedia", "wikidata", "crossref", "openalex", "arxiv", "europe", "pubmed", "fda", "who"),
            "books": ("library", "gutenberg", "wikipedia", "crossref"),
            "movies": ("tmdb", "omdb", "tvmaze", "rick"),
            "location": ("geo", "nominatim", "openstreet", "countries", "ipinfo", "timezone"),
            "programming": ("github", "stack", "npm", "pypi", "crates", "hugging"),
            "howto": ("wikihow", "wikipedia", "stack", "github"),
        }
        if "general" in cats:
            return True
        n = p.name.lower()
        return any(any(x in n for x in buckets.get(c, ())) for c in cats)

    async def _http(self, p, query, category):
        if p.group == "render" and p.env and not os.getenv(p.env):
            return None
        name, url = p.name, p.base_url
        headers = {"User-Agent": UA, "Accept": "application/json,text/html;q=0.8"}
        params = {"q": query}
        key = os.getenv(p.env or "")

        if p.group == "browser_search":
            params = {"q": query}
            headers["Accept"] = "text/html,application/xhtml+xml"
        elif p.group == "keyless":
            params = self._keyless_params(name, query)
            url = self._keyless_url(name, url, query)
        elif p.group == "render":
            if name in {"Tavily", "Exa"}:
                return await (self._tavily(key, query) if name == "Tavily" else self._exa(key, query))
            if name in AI_PROVIDERS:
                return None
            if name == "News API": params = {"q": query, "apiKey": key, "pageSize": 5}
            elif name == "GNews": params = {"q": query, "token": key, "max": 5}
            elif name == "The Guardian": params = {"q": query, "api-key": key, "page-size": 5}
            elif name == "MediaStack": params = {"access_key": key, "keywords": query, "limit": 5}
            elif name == "OMDb": params = {"apikey": key, "s": query}
            elif name == "TMDB": params = {"api_key": key, "query": query}
            elif name == "OpenWeather": params = {"q": query, "appid": key, "units": "metric"}
            elif name == "Geoapify": params = {"text": query, "apiKey": key, "limit": 3}
            elif name == "Finnhub": params = {"q": query, "token": key}
            elif name == "Alpha Vantage": params = {"function": "SYMBOL_SEARCH", "keywords": query, "apikey": key}
            elif name == "Twelve Data": params = {"symbol": query, "apikey": key}
            elif name == "CoinGecko": params = {"query": query, "x_cg_demo_api_key": key}
            elif name == "Search API": params = {"engine": "google", "q": query, "api_key": key}
            elif name == "Wolfram": params = {"appid": os.getenv("WOLFRAM_APP_ID", key), "i": query}
            elif name == "TimeZoneDB": params = {"key": key, "format": "json", "by": "zone", "zone": query}
            elif name == "Tomorrow.io": params = {"location": query, "apikey": key, "units": "metric"}
            elif name == "ExchangeRate.host": params = {"q": query, "access_key": key}
            elif name == "IPinfo": url = f"https://ipinfo.io/{quote_plus(query)}?token={key}"; params = {}
            elif name == "REST Countries": url = f"https://restcountries.com/v3.1/name/{quote_plus(query)}"; params = {}
            elif name == "AllSports": params = {"met": "Teams", "APIkey": key}
            elif name == "API-Sports": headers["x-apisports-key"] = key; params = {}
            elif name == "SportMonks": params = {"api_token": key}
            elif name == "TheSportsDB": url = f"https://www.thesportsdb.com/api/v1/json/{key}/searchteams.php"; params = {"t": query}
            elif name in {"Mailgun", "Resend", "DignityApex", "Sportradar", "Odds API", "ExchangeRate API", "WorldTime", "Random API"}:
                return None
            else:
                headers["Authorization"] = f"Bearer {key}"

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
                r = await client.get(url, params=params)
                if r.status_code >= 400:
                    return None
                try:
                    data = r.json()
                except Exception:
                    data = {"text": re.sub(r"\s+", " ", r.text[:12000])}
                return {"source": name, "category": category, "url": str(r.url), "data": data}
        except Exception:
            return None

    def _keyless_url(self, name, url, query):
        if name == "REST Countries": return f"https://restcountries.com/v3.1/name/{quote_plus(query)}"
        if name in {"PokeAPI", "Rick and Morty API", "SWAPI"}:
            return url.rstrip("/") + "/" + quote_plus(query.split()[0])
        return url

    def _keyless_params(self, name, query):
        if name in {"Wikipedia", "WikiHow", "Wikidata", "Wikimedia Commons", "MediaWiki API"}: return {"action":"query","list":"search","srsearch":query,"format":"json","srlimit":5}
        if name == "Open Library": return {"q":query,"limit":5}
        if name == "Crossref": return {"query.bibliographic":query,"rows":5}
        if name == "OpenAlex": return {"search":query,"per-page":5}
        if name == "arXiv API": return {"search_query":f"all:{query}","start":0,"max_results":5}
        if name == "Europe PMC": return {"query":query,"format":"json","pageSize":5}
        if name == "PubMed E-utilities": return {"db":"pubmed","term":query,"retmode":"json","retmax":5}
        if name == "Internet Archive": return {"q":query,"output":"json","rows":5}
        if name == "Library of Congress": return {"q":query,"fo":"json","c":5}
        if name == "USGS Earthquake API": return {"format":"geojson","orderby":"time","limit":5}
        if name == "GitHub REST API": return {"q":query,"per_page":5}
        if name == "Stack Exchange API": return {"order":"desc","sort":"relevance","q":query,"site":"stackoverflow","pagesize":5}
        if name == "npm Registry API": return {"text":query,"size":5}
        if name == "Crates.io API": return {"q":query,"per_page":5}
        if name == "Open-Meteo Geocoding": return {"name":query,"count":5,"language":"en","format":"json"}
        if name == "Nominatim / OpenStreetMap": return {"q":query,"format":"json","limit":5}
        if name == "OpenFDA": return {"search":f"openfda.generic_name:{query}","limit":5}
        if name == "Data USA": return {"show":"geo","geo":query}
        if name == "TVmaze API": return {"q":query}
        if name in {"Agify","Genderize"}: return {"name":query}
        if name == "Frankfurter": return {"from":"USD","to":"EUR"}
        if name == "JokeAPI": return {"format":"json","type":"single"}
        return {"q":query}

    async def _tavily(self,key,q):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r=await c.post("https://api.tavily.com/search",json={"api_key":key,"query":q,"search_depth":"advanced","max_results":5}); r.raise_for_status(); return {"source":"Tavily","data":r.json()}
        except Exception:return None

    async def _exa(self,key,q):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r=await c.post("https://api.exa.ai/search",headers={"x-api-key":key},json={"query":q,"numResults":5,"contents":{"text":{"maxCharacters":3000}}}); r.raise_for_status(); return {"source":"Exa","data":r.json()}
        except Exception:return None

    async def answer(self, query, conversation_id=None):
        categories = self._route(query)
        candidates = [p for p in self.providers if self._relevant(p, categories)]
        results = await asyncio.gather(*(self._http(p, query, categories[0]) for p in candidates), return_exceptions=True)
        evidence = [x for x in results if isinstance(x, dict)]
        if len(evidence) < 3:
            fallbacks = await asyncio.gather(
                self._tavily(os.getenv("TAVILY_API_KEY"), query) if os.getenv("TAVILY_API_KEY") else asyncio.sleep(0),
                self._exa(os.getenv("EXA_API_KEY"), query) if os.getenv("EXA_API_KEY") else asyncio.sleep(0),
            )
            evidence.extend(x for x in fallbacks if isinstance(x, dict))
        evidence = evidence[:20]
        answer = await self.ai.generate(query, evidence, conversation_id)
        return {"answer":answer,"nexus":{"categories":categories,"sources_consulted":[x["source"] for x in evidence],"sources_available":self.source_count,"candidates":len(candidates)}}

    async def health(self):
        checks={"Bloxy Nexus":True}
        async def one(p):
            try:
                async with httpx.AsyncClient(timeout=4,headers={"User-Agent":UA}) as c:
                    r=await c.get(p.base_url,params={"limit":1} if "openlibrary" in p.base_url else None)
                    return p.name,r.status_code<500
            except Exception:return p.name,False
        sample=[p for p in self.providers if p.group=="keyless"][:15]
        checks.update(dict(await asyncio.gather(*(one(p) for p in sample))))
        return checks
