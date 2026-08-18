"""Bloxy Nexus provider registry.

The registry describes how each source can be queried. Secrets are read only from
Render environment variables. Browser entries are search destinations rather
than pretend-to-be APIs; Nexus uses them as HTTP search fallbacks.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Provider:
    name: str
    group: str
    env: str | None = None
    kind: str = "source"
    base_url: str | None = None
    method: str = "GET"
    categories: tuple[str, ...] = ("general",)
    query_param: str = "q"

KEYED = [
("AllSports","ALLSPORTS_API_KEY","https://apiv2.allsportsapi.com/football/"),
("Alpha Vantage","ALPHA_VANTAGE_API_KEY","https://www.alphavantage.co/query"),
("Anthropic","ANTHROPIC_API_KEY","https://api.anthropic.com/v1/messages"),
("API-Sports","APISPORTS_API_KEY","https://v3.football.api-sports.io/fixtures"),
("Cohere","COHERE_API_KEY","https://api.cohere.com/v2/chat"),
("CoinGecko","COINGECKO_API_KEY","https://api.coingecko.com/api/v3/search"),
("DeepSeek","DEEPSEEK_API_KEY","https://api.deepseek.com/chat/completions"),
("DignityApex","DIGNITYAPEX_API_KEY","https://api.dignityapex.com"),
("Exa","EXA_API_KEY","https://api.exa.ai/search"),
("ExchangeRate.host","EXCHANGERATE.HOST_API_KEY","https://api.exchangerate.host/search"),
("ExchangeRate API","EXCHANGERATE_API_KEY","https://v6.exchangerate-api.com/v6"),
("Finnhub","FINNHUB_API_KEY","https://finnhub.io/api/v1/search"),
("Firecrawl","FIRECRAWL_API_KEY","https://api.firecrawl.dev/v1/search"),
("Geoapify","GEOAPIFY_API_KEY","https://api.geoapify.com/v1/geocode/search"),
("GNews","GNEWS_API_KEY","https://gnews.io/api/v4/search"),
("Groq","GROQ_API_KEY","https://api.groq.com/openai/v1/chat/completions"),
("The Guardian","GUARDIAN_API_KEY","https://content.guardianapis.com/search"),
("Hugging Face","HUGGINGFACE_API_KEY","https://huggingface.co/api/models"),
("IPinfo","IPINFO.IO_API_KEY","https://ipinfo.io"),
("Kimi","KIMI_API_KEY","https://api.moonshot.cn/v1/chat/completions"),
("Mailgun","MAILGUN_API_KEY","https://api.mailgun.net/v3"),
("MediaStack","MEDIASTACK_API_KEY","https://api.mediastack.com/v1/news"),
("Mistral","MISTRAL_API_KEY","https://api.mistral.ai/v1/chat/completions"),
("News API","NEWS_API_KEY","https://newsapi.org/v2/everything"),
("Odds API","ODDS_API_KEY","https://api.the-odds-api.com/v4/sports"),
("OMDb","OMDB_API_KEY","https://www.omdbapi.com/"),
("OpenAI","OPENAI_API_KEY","https://api.openai.com/v1/chat/completions"),
("OpenRouter","OPENROUTER_API_KEY","https://openrouter.ai/api/v1/chat/completions"),
("OpenWeather","OPENWEATHER_API_KEY","https://api.openweathermap.org/data/2.5/weather"),
("Qwen","QWEN_API_KEY","https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"),
("Random API","RANDOM_API_KEY","https://random.api"),
("Resend","RESEND_API_KEY","https://api.resend.com/emails"),
("REST Countries","RESTCOUNTRIES_API_KEY","https://restcountries.com/v3.1/name"),
("Search API","SEARCH_API_KEY","https://www.searchapi.io/api/v1/search"),
("SportMonks","SPORTMONK_API_KEY","https://api.sportmonks.com/v3/football/fixtures"),
("Sportradar","SPORTRADAR_API_KEY","https://api.sportradar.com"),
("Tavily","TAVILY_API_KEY","https://api.tavily.com/search"),
("TheSportsDB","THESPORTSDB_API_KEY","https://www.thesportsdb.com/api/v1/json"),
("TimeZoneDB","TIMEZONEDB_API_KEY","https://api.timezonedb.com/v2.1/get-time-zone"),
("TMDB","TMDB_API_KEY","https://api.themoviedb.org/3/search/multi"),
("Tomorrow.io","TOMORROW_IO_API_KEY","https://api.tomorrow.io/v4/weather/realtime"),
("Twelve Data","TWELVEDATA_API_KEY","https://api.twelvedata.com/symbol_search"),
("Wolfram","WOLFRAM_APP_ID","https://api.wolframalpha.com/v1/result"),
("WorldTime","WORLDTIME_API_KEY","https://api.worldtimeapi.org/api/timezone/Etc/UTC"),
]

BROWSER_SEARCH = [
("Safari","https://www.google.com/search"),("Opera","https://www.google.com/search"),
("Google","https://www.google.com/search"),("Yandex","https://yandex.com/search/"),
("Yahoo","https://search.yahoo.com/search"),("Microsoft Edge","https://www.bing.com/search"),
("Brave","https://search.brave.com/search"),("Google Chrome","https://www.google.com/search"),
("Mozilla Firefox","https://www.google.com/search"),("Samsung Internet","https://www.google.com/search"),
("UC Browser","https://www.google.com/search"),("Vivaldi","https://www.google.com/search"),
("DuckDuckGo","https://html.duckduckgo.com/html/"),("Bing","https://www.bing.com/search"),
("Baidu","https://www.baidu.com/s"),("Naver","https://search.naver.com/search.naver"),
("Ecosia","https://www.ecosia.org/search"),("Startpage","https://www.startpage.com/sp/search"),
("Qwant","https://www.qwant.com/"),("Tor Browser","https://duckduckgo.com/html/"),
]

KEYLESS = [
("Wikipedia","https://en.wikipedia.org/w/api.php"),("WikiHow","https://www.wikihow.com/api.php"),("Wikidata","https://www.wikidata.org/w/api.php"),("Wikimedia Commons","https://commons.wikimedia.org/w/api.php"),("MediaWiki API","https://www.mediawiki.org/w/api.php"),
("Open Library","https://openlibrary.org/search.json"),("Crossref","https://api.crossref.org/works"),("OpenAlex","https://api.openalex.org/works"),("arXiv API","https://export.arxiv.org/api/query"),("Europe PMC","https://www.ebi.ac.uk/europepmc/webservices/rest/search"),("PubMed E-utilities","https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"),("Internet Archive","https://archive.org/advancedsearch.php"),("Project Gutenberg","https://gutendex.com/books"),("Library of Congress","https://www.loc.gov/books/"),("World Bank API","https://api.worldbank.org/v2/country"),("IMF Data API","https://www.imf.org/external/datamapper/api/v1"),("UN Data","https://unstats.un.org/SDGAPI/v1/sdg/Series/Data"),("WHO GHO OData","https://ghoapi.azureedge.net/api/Indicator"),("US Census API","https://api.census.gov/data"),("USGS Earthquake API","https://earthquake.usgs.gov/fdsnws/event/1/query"),("Open-Meteo","https://api.open-meteo.com/v1/forecast"),("Nager.Date","https://date.nager.at/api/v3/PublicHolidays"),("REST Countries","https://restcountries.com/v3.1/name"),("Frankfurter","https://api.frankfurter.app/latest"),("CoinPaprika","https://api.coinpaprika.com/v1/search"),("GitHub REST API","https://api.github.com/search/repositories"),("Stack Exchange API","https://api.stackexchange.com/2.3/search/advanced"),("npm Registry API","https://registry.npmjs.org/-/v1/search"),("PyPI JSON API","https://pypi.org/pypi"),("Crates.io API","https://crates.io/api/v1/crates"),("Open-Meteo Geocoding","https://geocoding-api.open-meteo.com/v1/search"),("Nominatim / OpenStreetMap","https://nominatim.openstreetmap.org/search"),("Overpass API","https://overpass-api.de/api/interpreter"),("OpenFDA","https://api.fda.gov/drug/label.json"),("CDC public datasets","https://data.cdc.gov/resource"),("Data USA","https://datausa.io/api/data"),("OpenAQ","https://api.openaq.org/v3/locations"),("TVmaze API","https://api.tvmaze.com/search/shows"),("PokeAPI","https://pokeapi.co/api/v2/pokemon"),("Rick and Morty API","https://rickandmortyapi.com/api/character"),("SWAPI","https://swapi.dev/api/people"),("JokeAPI","https://v2.jokeapi.dev/joke/Any"),("Quotable","https://api.quotable.io/quotes/random"),("Bored API","https://www.boredapi.com/api/activity"),("Cat Facts API","https://catfact.ninja/fact"),("Dog CEO API","https://dog.ceo/api/breeds/image/random"),("Agify","https://api.agify.io"),("Genderize","https://api.genderize.io"),("Numbers API","http://numbersapi.com/random/trivia"),("WorldTimeAPI","https://worldtimeapi.org/api/timezone/Etc/UTC"),
]

AI_PROVIDERS = {"OpenAI","Anthropic","DeepSeek","Groq","Mistral","OpenRouter","Cohere","Qwen","Kimi","Hugging Face"}

PROVIDERS = [Provider(n,"render",e,"keyed",u) for n,e,u in KEYED]
PROVIDERS += [Provider(n,"browser_search",None,"search",u,"GET",("general","news")) for n,u in BROWSER_SEARCH]
PROVIDERS += [Provider(n,"keyless",None,"keyless",u) for n,u in KEYLESS]

assert len(KEYED) == 44
assert len(BROWSER_SEARCH) == 20
assert len(KEYLESS) == 50
assert len(PROVIDERS) == 114

# Backwards-compatible names used by the rest of the application.
ALL_PROVIDERS = [p.__dict__ for p in PROVIDERS]
KEYED_PROVIDERS = KEYED
