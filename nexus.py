"""Bloxy Nexus: query routing, source adapters, fallback and evidence fusion."""
import asyncio, os, re
from typing import Any
from urllib.parse import quote_plus
import httpx
from ai_engine import AIEngine
from providers import PROVIDERS, AI_PROVIDERS

TIMEOUT = httpx.Timeout(10.0, connect=4.0)
USER_AGENT = "Bloxy-bot/1.0 (Bloxy Nexus)"

class BloxyNexus:
    def __init__(self):
        self.providers = PROVIDERS
        self.ai = AIEngine()
        self.source_count = len(PROVIDERS)
        self.ai_provider_count = len(AI_PROVIDERS)

    def provider_summary(self):
        return {"name":"Bloxy Nexus","total":self.source_count,
                "render":sum(p.group=="render" for p in self.providers),
                "browser_search":sum(p.group=="browser_search" for p in self.providers),
                "keyless":sum(p.group=="keyless" for p in self.providers),
                "ai_models":self.ai_provider_count}

    def _route(self, q: str):
        s=q.lower(); rules={
            "sports":r"\b(football|soccer|basketball|tennis|nba|nfl|fifa|arsenal|chelsea|match|score|fixture|league|sport)\b",
            "weather":r"\b(weather|temperature|forecast|rain|humidity|wind|climate)\b",
            "finance":r"\b(stock|share|forex|exchange rate|currency|crypto|bitcoin|market|nasdaq|s&p|finance)\b",
            "news":r"\b(news|latest|today|breaking|headline|recent|yesterday)\b",
            "science":r"\b(science|physics|chemistry|biology|research|paper|study|scientific)\b",
            "books":r"\b(book|author|novel|isbn|literature)\b",
            "movies":r"\b(movie|film|actor|actress|tv|series|episode|cinema)\b",
            "location":r"\b(where|location|map|address|near me|country|city|timezone)\b",
            "programming":r"\b(code|coding|programming|python|javascript|api|github|npm|bug|error|software)\b",
            "howto":r"\b(how do i|how to|steps|tutorial|guide|fix|install|setup)\b"}
        return [k for k,p in rules.items() if re.search(p,s)] or ["general"]

    def _relevant(self, p, cats):
        n=p.name.lower()
        if p.group=="browser_search": return True
        groups={
            "sports":("sports","allsports","api-sports","sportmonks","sportradar","thesportsdb","odds"),
            "weather":("weather","openweather","tomorrow","open-meteo","worldtime","timezone"),
            "finance":("alpha","exchange","finnhub","coin","twelve","wolfram"),
            "news":("news","guardian","gnews","mediastack","tavily","exa","search"),
            "science":("wikipedia","wikidata","crossref","openalex","arxiv","europe","pubmed","openfda","who","world bank"),
            "books":("library","open library","gutenberg","wikipedia","crossref"),
            "movies":("tmdb","omdb","tvmaze","rick and morty"),
            "location":("geo","nominatim","openstreet","countries","ipinfo","timezone","worldtime"),
            "programming":("github","stack exchange","npm","pypi","crates","hugging"),
            "howto":("wikihow","wikipedia","stack exchange","github")}
        if "general" in cats: return True
        return any(any(x in n for x in groups.get(c,())) for c in cats)

    async def _query_provider(self, p, query, category):
        """Best-effort adapter for each registered source. Provider-specific APIs
        that use unusual payloads are handled by dedicated search/AI fallbacks."""
        if p.group=="render" and not os.getenv(p.env or ""):
            return None
        headers={"User-Agent":USER_AGENT,"Accept":"application/json"}
        params={}
        url=p.base_url
        name=p.name
        # Common authentication patterns.
        if p.group=="render":
            key=os.getenv(p.env)
            if name in {"Tavily"}: return await self._tavily(key,query)
            if name=="Exa": return await self._exa(key,query)
            if name in {"OpenAI","DeepSeek","Groq","Mistral","OpenRouter","Qwen","Kimi"}: return None
            if name=="Anthropic" or name=="Cohere": return None
            if name=="Wolfram": params.update(appid=os.getenv("WOLFRAM_APP_ID",key),i=query)
            elif name=="News API": params.update(q=query,apiKey=key,pageSize=5)
            elif name=="GNews": params.update(q=query,token=key,max=5)
            elif name=="The Guardian": params.update(q=query,api-key=key,page_size=5)
            elif name=="MediaStack": params.update(access_key=key,keywords=query,limit=5)
            elif name=="OMDb": params.update(apikey=key,s=query)
            elif name=="TMDB": params.update(api_key=key,query=query)
            elif name=="OpenWeather": params.update(q=query,appid=key,units="metric")
            elif name=="Geoapify": params.update(text=query,apiKey=key,limit=3)
            elif name=="Finnhub": params.update(q=query,token=key)
            elif name=="Alpha Vantage": params.update(function="SYMBOL_SEARCH",keywords=query,apikey=key)
            elif name=="Twelve Data": params.update(symbol=query,apikey=key)
            elif name=="CoinGecko": params.update(query=query)
            elif name=="REST Countries": params.update()
            elif name=="Search API": params.update(engine="google",q=query,api_key=key)
            elif name=="IPinfo": url=f"https://ipinfo.io/{quote_plus(query)}?token={key}"
            elif name=="TimeZoneDB": params.update(key=key,format="json",by= "zone",zone=query)
            elif name=="Tomorrow.io": params.update(location=query,apikey=key,units="metric")
            elif name=="ExchangeRate API": return None
            elif name=="ExchangeRate.host": params.update(q=query,access_key=key)
            elif name=="Odds API": return None
            elif name=="AllSports": params.update( met= "Teams", APIkey=key)
            elif name=="API-Sports": headers["x-apisports-key"]=key
            elif name=="SportMonks": params.update(api_token=key)
            elif name=="TheSportsDB": url=f"https://www.thesportsdb.com/api/v1/json/{key}/searchteams.php"; params.update(t=query)
            elif name=="WorldTime": return None
            elif name in {"Mailgun","Resend","DignityApex"}: return None
            else:
                headers["Authorization"]=f"Bearer {key}"
        if name=="REST Countries": url=f"https://restcountries.com/v3.1/name/{quote_plus(query)}"
        if p.group=="keyless":
            if name in {"Wikipedia","WikiHow","Wikidata","Wikimedia Commons","MediaWiki API"}: params.update(action="query",list="search",srsearch=query,format="json",utf8=1,srlimit=5)
            elif name=="Open Library": params.update(q=query,limit=5)
            elif name in {"Crossref","OpenAlex"}: params.update(search=query,per_page=5 if name=="Crossref" else 5)
            elif name=="arXiv API": params.update(search_query=f"all:{query}",start=0,max_results=5)
            elif name in {"Europe PMC"}: params.update(query=query,format="json",pageSize=5)
            elif name=="PubMed E-utilities": params.update(db="pubmed",term=query,retmode="json",retmax=5)
            elif name=="Internet Archive": params.update(q=query,output="json",rows=5)
            elif name=="Library of Congress": params.update(q=query,fo="json",c=5)
            elif name=="World Bank API": return None
            elif name=="IMF Data API": return None
            elif name=="USGS Earthquake API": params.update(format="geojson",orderby="time",limit=5)
            elif name=="Open-Meteo": return await self._geocode_then_weather(query)
            elif name=="Nager.Date": return None
            elif name=="Frankfurter": params.update(amount=1,from_="USD",to="EUR")
            elif name=="GitHub REST API": params.update(q=query,per_page=5)
            elif name=="Stack Exchange API": params.update(order="desc",sort="relevance",q=query,site="stackoverflow",pagesize=5)
            elif name=="npm Registry API": params.update(text=query,size=5)
            elif name=="Crates.io API": params.update(q=query,per_page=5)
            elif name=="Open-Meteo Geocoding": params.update(name=query,count=5,language="en",format="json")
            elif name=="Nominatim / OpenStreetMap": params.update(q=query,format="json",limit=5)
            elif name=="OpenFDA": params.update(search=f"openfda.generic_name:{query}",limit=5)
            elif name=="Data USA": params.update(show="geo",geo=query)
            elif name=="TVmaze API": params.update(q=query)
            elif name in {"PokeAPI","Rick and Morty API","SWAPI"}: url=url.rstrip("/")/""; return None
            elif name=="Agify" or name=="Genderize": params.update(name=query)
            else: params={}
        if p.group=="browser_search":
            params={"q":query}
            headers["Accept"]="text/html,application/xhtml+xml"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT,headers=headers,follow_redirects=True) as c:
                r=await c.get(url,params=params)
                if r.status_code>=400: return None
                text=r.text[:12000]
                try: data=r.json()
                except Exception: data={"text":re.sub(r"\\s+"," ",text)}
                return {"source":name,"category":category,"url":str(r.url),"data":data}
        except Exception:
            return None

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
    async def _geocode_then_weather(self,q):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                g=await c.get("https://geocoding-api.open-meteo.com/v1/search",params={"name":q,"count":1,"language":"en","format":"json"}); j=g.json(); x=(j.get("results") or [None])[0]
                if not x:return None
                w=await c.get("https://api.open-meteo.com/v1/forecast",params={"latitude":x["latitude"],"longitude":x["longitude"],"current":"temperature_2m,relative_humidity_2m,wind_speed_10m"}); return {"source":"Open-Meteo","data":{"location":x,"weather":w.json()}}
        except Exception:return None

    async def answer(self,query,conversation_id=None):
        cats=self._route(query)
        candidates=[p for p in self.providers if self._relevant(p,cats)]
        # Keep latency bounded while allowing broad redundancy.
        results=await asyncio.gather(*(self._query_provider(p,query,cats[0]) for p in candidates),return_exceptions=True)
        evidence=[r for r in results if isinstance(r,dict)]
        # Always use the best search providers as a Nexus fallback.
        if len(evidence)<3:
            extra=await asyncio.gather(self._tavily(os.getenv("TAVILY_API_KEY"),query) if os.getenv("TAVILY_API_KEY") else asyncio.sleep(0),self._exa(os.getenv("EXA_API_KEY"),query) if os.getenv("EXA_API_KEY") else asyncio.sleep(0))
            evidence += [x for x in extra if isinstance(x,dict)]
        evidence=evidence[:20]
        answer=await self.ai.generate(query,evidence,conversation_id)
        return {"answer":answer,"nexus":{"categories":cats,"sources_consulted":[x["source"] for x in evidence],"sources_available":self.source_count,"sources_queried":len(candidates)}}

    async def health(self):
        checks={"Bloxy Nexus":True}
        async with httpx.AsyncClient(timeout=5,headers={"User-Agent":USER_AGENT}) as c:
            sample=[p for p in self.providers if p.group=="keyless"][:12]
            async def one(p):
                try:return p.name,(await c.get(p.base_url,params={"limit":1} if "openlibrary" in p.base_url else None)).status_code<500
                except Exception:return p.name,False
            checks.update(dict(await asyncio.gather(*(one(p) for p in sample))))
        return checks
