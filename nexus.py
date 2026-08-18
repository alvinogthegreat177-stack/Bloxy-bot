"""Bloxy Nexus: one unified gateway for the 114-source knowledge network."""
import asyncio
import os
import re
from typing import Any
from urllib.parse import quote_plus

import httpx

from ai_engine import AIEngine
from providers import PROVIDERS, Provider, AI_PROVIDERS

TIMEOUT = httpx.Timeout(12.0, connect=5.0)
USER_AGENT = "Bloxy-bot/1.0 (Bloxy Nexus; unified 114-source gateway)"


class BloxyNexus:
    def __init__(self) -> None:
        self.providers = PROVIDERS
        self.ai = AIEngine()
        self.source_count = len(PROVIDERS)
        self.ai_provider_count = len(AI_PROVIDERS)

    def provider_summary(self) -> dict[str, Any]:
        return {
            "name": "Bloxy Nexus",
            "version": "1.0.0",
            "total_sources": self.source_count,
            "render_sources": sum(p.group == "render" for p in self.providers),
            "browser_search_sources": sum(p.group == "browser_search" for p in self.providers),
            "keyless_sources": sum(p.group == "keyless" for p in self.providers),
            "ai_models": self.ai_provider_count,
            "unified_endpoint": "/ai/chat",
        }

    @staticmethod
    def _categories(query: str) -> list[str]:
        text = query.lower()
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
        found = [name for name, pattern in rules.items() if re.search(pattern, text)]
        return found or ["general"]

    @staticmethod
    def _relevant(provider: Provider, categories: list[str]) -> bool:
        if provider.group == "browser_search" or "general" in categories:
            return True
        name = provider.name.lower()
        mapping = {
            "sports": ("sport", "odds"),
            "weather": ("weather", "open-meteo", "time", "timezone"),
            "finance": ("alpha", "exchange", "finnhub", "coin", "twelve", "wolfram"),
            "news": ("news", "guardian", "gnews", "media", "tavily", "exa", "search", "firecrawl"),
            "science": ("wiki", "crossref", "openalex", "arxiv", "europe", "pubmed", "fda", "who", "world bank", "imf"),
            "books": ("library", "gutenberg", "wiki", "crossref"),
            "movies": ("tmdb", "omdb", "tvmaze", "rick"),
            "location": ("geo", "nominatim", "openstreet", "countries", "ipinfo", "timezone", "worldtime"),
            "programming": ("github", "stack", "npm", "pypi", "crates", "hugging"),
            "howto": ("wikihow", "wikipedia", "stack", "github"),
        }
        return any(any(token in name for token in mapping.get(category, ())) for category in categories)

    async def _request(self, method: str, url: str, *, params=None, json=None, headers=None) -> Any | None:
        try:
            request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
            if headers:
                request_headers.update(headers)
            async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
                response = await client.request(method, url, params=params, json=json, headers=request_headers)
                if response.status_code >= 400:
                    return None
                try:
                    return response.json()
                except ValueError:
                    return {"text": re.sub(r"\s+", " ", response.text)[:12000]}
        except httpx.HTTPError:
            return None

    async def _query_keyless(self, p: Provider, query: str) -> dict[str, Any] | None:
        name, url = p.name, p.base_url
        params: dict[str, Any] = {}
        if name in {"Wikipedia", "WikiHow", "Wikidata", "Wikimedia Commons", "MediaWiki API"}:
            params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "utf8": 1, "srlimit": 5}
        elif name == "Open Library": params = {"q": query, "limit": 5}
        elif name == "Crossref": params = {"query.bibliographic": query, "rows": 5}
        elif name == "OpenAlex": params = {"search": query, "per-page": 5}
        elif name == "arXiv API": params = {"search_query": f"all:{query}", "start": 0, "max_results": 5}
        elif name == "Europe PMC": params = {"query": query, "format": "json", "pageSize": 5}
        elif name == "PubMed E-utilities": params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": 5}
        elif name == "Internet Archive": params = {"q": query, "output": "json", "rows": 5}
        elif name == "Library of Congress": params = {"q": query, "fo": "json", "c": 5}
        elif name == "USGS Earthquake API": params = {"format": "geojson", "orderby": "time", "limit": 5}
        elif name == "GitHub REST API": params = {"q": query, "per_page": 5}
        elif name == "Stack Exchange API": params = {"order": "desc", "sort": "relevance", "q": query, "site": "stackoverflow", "pagesize": 5}
        elif name == "npm Registry API": params = {"text": query, "size": 5}
        elif name == "Crates.io API": params = {"q": query, "per_page": 5}
        elif name == "Open-Meteo Geocoding": params = {"name": query, "count": 5, "language": "en", "format": "json"}
        elif name == "Nominatim / OpenStreetMap": params = {"q": query, "format": "jsonv2", "limit": 5}
        elif name == "OpenFDA": params = {"search": f"openfda.generic_name:{query}", "limit": 5}
        elif name == "Data USA": params = {"show": "geo", "geo": query}
        elif name == "TVmaze API": params = {"q": query}
        elif name in {"Agify", "Genderize"}: params = {"name": query}
        elif name == "Frankfurter": params = {"from": "USD", "to": "EUR"}
        elif name == "JokeAPI": params = {"type": "single,twopart"}
        elif name in {"Quotable", "Bored API", "Cat Facts API", "Dog CEO API", "Numbers API", "WorldTimeAPI", "Nager.Date"}: params = {}
        elif name == "CoinPaprika": params = {"q": query}
        elif name == "PokeAPI": url = f"{url.rstrip('/')}/{quote_plus(query)}"
        elif name == "Rick and Morty API": params = {"name": query}
        elif name == "SWAPI": params = {"search": query}
        else: return None
        data = await self._request("GET", url, params=params)
        return {"source": name, "url": url, "data": data} if data is not None else None

    async def _query_render(self, p: Provider, query: str) -> dict[str, Any] | None:
        key = os.getenv(p.env or "")
        if not key: return None
        name, url = p.name, p.base_url
        params: dict[str, Any] = {}
        headers: dict[str, str] = {}
        if name == "Tavily":
            data = await self._request("POST", url, json={"api_key": key, "query": query, "search_depth": "advanced", "max_results": 5})
        elif name == "Exa":
            data = await self._request("POST", url, headers={"x-api-key": key}, json={"query": query, "numResults": 5, "contents": {"text": {"maxCharacters": 3000}}})
        elif name in AI_PROVIDERS: return None
        elif name == "News API": params = {"q": query, "apiKey": key, "pageSize": 5}; data = await self._request("GET", url, params=params)
        elif name == "GNews": params = {"q": query, "token": key, "max": 5}; data = await self._request("GET", url, params=params)
        elif name == "The Guardian": params = {"q": query, "api-key": key, "page-size": 5}; data = await self._request("GET", url, params=params)
        elif name == "MediaStack": params = {"access_key": key, "keywords": query, "limit": 5}; data = await self._request("GET", url, params=params)
        elif name == "OMDb": params = {"apikey": key, "s": query}; data = await self._request("GET", url, params=params)
        elif name == "TMDB": params = {"api_key": key, "query": query}; data = await self._request("GET", url, params=params)
        elif name == "OpenWeather": params = {"q": query, "appid": key, "units": "metric"}; data = await self._request("GET", url, params=params)
        elif name == "Geoapify": params = {"text": query, "apiKey": key, "limit": 5}; data = await self._request("GET", url, params=params)
        elif name == "Finnhub": params = {"q": query, "token": key}; data = await self._request("GET", url, params=params)
        elif name == "Alpha Vantage": params = {"function": "SYMBOL_SEARCH", "keywords": query, "apikey": key}; data = await self._request("GET", url, params=params)
        elif name == "Twelve Data": params = {"symbol": query, "apikey": key}; data = await self._request("GET", url, params=params)
        elif name == "CoinGecko": data = await self._request("GET", url, params={"query": query}, headers={"x-cg-demo-api-key": key})
        elif name == "REST Countries": data = await self._request("GET", f"{url}/{quote_plus(query)}")
        elif name == "Search API": data = await self._request("GET", url, params={"engine": "google", "q": query, "api_key": key})
        elif name == "IPinfo": data = await self._request("GET", f"{url.rstrip('/')}/{quote_plus(query)}", params={"token": key})
        elif name == "TimeZoneDB": data = await self._request("GET", url, params={"key": key, "format": "json", "by": "zone", "zone": query})
        elif name == "Tomorrow.io": data = await self._request("GET", url, params={"location": query, "apikey": key, "units": "metric"})
        elif name == "ExchangeRate.host": data = await self._request("GET", url, params={"access_key": key, "q": query})
        elif name == "TheSportsDB": data = await self._request("GET", f"{url}/{key}/searchteams.php", params={"t": query})
        elif name == "AllSports": data = await self._request("GET", url, params={"met": "Teams", "APIkey": key})
        elif name == "API-Sports": data = await self._request("GET", url, headers={"x-apisports-key": key}, params={"team": query})
        elif name == "SportMonks": data = await self._request("GET", url, params={"api_token": key})
        elif name == "Wolfram": data = await self._request("GET", url, params={"appid": key, "i": query})
        elif name == "WorldTime": data = await self._request("GET", url)
        elif name == "Firecrawl": data = await self._request("POST", url, headers={"Authorization": f"Bearer {key}"}, json={"query": query})
        else:
            # Non-query services (mail delivery, generic app services, etc.) are
            # registered but deliberately not invoked by a normal chat request.
            return None
        return {"source": name, "url": url, "data": data} if data is not None else None

    async def _query_browser(self, p: Provider, query: str) -> dict[str, Any] | None:
        data = await self._request("GET", p.base_url, params={"q": query}, headers={"Accept": "text/html,application/xhtml+xml"})
        return {"source": p.name, "url": p.base_url, "data": data} if data is not None else None

    async def _query(self, p: Provider, query: str) -> dict[str, Any] | None:
        if p.group == "keyless": return await self._query_keyless(p, query)
        if p.group == "render": return await self._query_render(p, query)
        return await self._query_browser(p, query)

    async def answer(self, query: str, conversation_id: str | None = None) -> dict[str, Any]:
        categories = self._categories(query)
        candidates = [p for p in self.providers if self._relevant(p, categories)]
        raw = await asyncio.gather(*(self._query(p, query) for p in candidates), return_exceptions=True)
        evidence = [item for item in raw if isinstance(item, dict)]
        if len(evidence) < 3:
            fallback_names = {"Tavily", "Exa", "Wikipedia", "OpenAlex", "Crossref"}
            fallback = [p for p in self.providers if p.name in fallback_names and p not in candidates]
            extra = await asyncio.gather(*(self._query(p, query) for p in fallback), return_exceptions=True)
            evidence.extend(item for item in extra if isinstance(item, dict))
        unique = {}
        for item in evidence: unique.setdefault(item["source"], item)
        evidence = list(unique.values())[:24]
        answer = await self.ai.generate(query, evidence, conversation_id)
        return {"answer": answer, "nexus": {"name": "Bloxy Nexus", "categories": categories, "sources_available": self.source_count, "sources_candidates": len(candidates), "sources_consulted": [item["source"] for item in evidence]}}

    async def health(self) -> dict[str, Any]:
        configured = {p.name: bool(os.getenv(p.env or "")) if p.env else True for p in self.providers}
        sample_names = {"Wikipedia", "Open Library", "Crossref", "OpenAlex", "GitHub REST API", "Open-Meteo"}
        sample = [p for p in self.providers if p.name in sample_names]
        results = await asyncio.gather(*(self._query(p, "test") for p in sample), return_exceptions=True)
        probes = {p.name: isinstance(result, dict) for p, result in zip(sample, results)}
        return {"service": "Bloxy Nexus", "total_sources": self.source_count, "configured": configured, "public_probe": probes}
