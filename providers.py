"""The canonical 114-source Bloxy Nexus registry.
Provider entries are routing metadata; secrets are read only from Render environment variables.
"""

def _p(name, group, env=None, kind="source", categories=None):
    return {"name": name, "group": group, "env": env, "kind": kind, "categories": categories or ["general"]}

KEYED_PROVIDERS = [
    ("AllSports","ALLSPORTS_API_KEY"),("Alpha Vantage","ALPHA_VANTAGE_API_KEY"),("Anthropic","ANTHROPIC_API_KEY"),("API-Sports","APISPORTS_API_KEY"),("Cohere","COHERE_API_KEY"),("CoinGecko","COINGECKO_API_KEY"),("DeepSeek","DEEPSEEK_API_KEY"),("DignityApex","DIGNITYAPEX_API_KEY"),("Exa","EXA_API_KEY"),("ExchangeRate.host","EXCHANGERATE.HOST_API_KEY"),("ExchangeRate API","EXCHANGERATE_API_KEY"),("Finnhub","FINNHUB_API_KEY"),("Firecrawl","FIRECRAWL_API_KEY"),("Geoapify","GEOAPIFY_API_KEY"),("GNews","GNEWS_API_KEY"),("Groq","GROQ_API_KEY"),("The Guardian","GUARDIAN_API_KEY"),("Hugging Face","HUGGINGFACE_API_KEY"),("IPinfo","IPINFO.IO_API_KEY"),("Kimi","KIMI_API_KEY"),("Mailgun","MAILGUN_API_KEY"),("MediaStack","MEDIASTACK_API_KEY"),("Mistral","MISTRAL_API_KEY"),("News API","NEWS_API_KEY"),("Odds API","ODDS_API_KEY"),("OMDb","OMDB_API_KEY"),("OpenAI","OPENAI_API_KEY"),("OpenRouter","OPENROUTER_API_KEY"),("OpenWeather","OPENWEATHER_API_KEY"),("Qwen","QWEN_API_KEY"),("Random API","RANDOM_API_KEY"),("Resend","RESEND_API_KEY"),("REST Countries","RESTCOUNTRIES_API_KEY"),("Search API","SEARCH_API_KEY"),("SportMonks","SPORTMONK_API_KEY"),("Sportradar","SPORTRADAR_API_KEY"),("Tavily","TAVILY_API_KEY"),("TheSportsDB","THESPORTSDB_API_KEY"),("TimeZoneDB","TIMEZONEDB_API_KEY"),("TMDB","TMDB_API_KEY"),("Tomorrow.io","TOMORROW_IO_API_KEY"),("Twelve Data","TWELVEDATA_API_KEY"),("Wolfram","WOLFRAM_API_KEY"),("WorldTime","WORLDTIME_API_KEY")]

BROWSER_SEARCH = ["Safari","Opera","Google","Yandex","Yahoo","Microsoft Edge","Brave","Google Chrome","Mozilla Firefox","Samsung Internet","UC Browser","Vivaldi","DuckDuckGo","Bing","Baidu","Naver","Ecosia","Startpage","Qwant","Tor Browser"]

KEYLESS = ["Wikipedia","WikiHow","Wikidata","Wikimedia Commons","MediaWiki API","Open Library","Crossref","OpenAlex","arXiv API","Europe PMC","PubMed E-utilities","Internet Archive","Project Gutenberg","Library of Congress","World Bank API","IMF Data API","UN Data","WHO GHO OData","US Census API","USGS Earthquake API","Open-Meteo","Nager.Date","REST Countries","Frankfurter","CoinPaprika","GitHub REST API","Stack Exchange API","npm Registry API","PyPI JSON API","Crates.io API","Open-Meteo Geocoding","Nominatim / OpenStreetMap","Overpass API","OpenFDA","CDC public datasets","Data USA","OpenAQ","TVmaze API","PokeAPI","Rick and Morty API","SWAPI","JokeAPI","Quotable","Bored API","Cat Facts API","Dog CEO API","Agify","Genderize","Numbers API","WorldTimeAPI"]

AI_PROVIDERS = ["OpenAI","Anthropic","DeepSeek","Groq","Mistral","OpenRouter","Cohere","Qwen","Kimi","Hugging Face"]

ALL_PROVIDERS = []
for name, env in KEYED_PROVIDERS:
    ALL_PROVIDERS.append(_p(name, "render", env, "keyed"))
for name in BROWSER_SEARCH:
    ALL_PROVIDERS.append(_p(name, "browser_search", None, "search"))
for name in KEYLESS:
    ALL_PROVIDERS.append(_p(name, "keyless", None, "keyless"))

assert len(KEYED_PROVIDERS) == 44
assert len(BROWSER_SEARCH) == 20
assert len(KEYLESS) == 50
assert len(ALL_PROVIDERS) == 114
