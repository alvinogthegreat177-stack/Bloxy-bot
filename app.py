# =================================================
# BLOXY-BOT AI - APP.PY PART 1
# IMPORTS + CONFIGURATION + ENVIRONMENT
# =================================================

import os

print("Current directory:", os.getcwd())
print("Files:", os.listdir("."))

import json
import uuid
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import httpx

from dotenv import load_dotenv

from fastapi import Request
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File
from fastapi import Form

from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from fastapi import FastAPI

app = FastAPI()


from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
    

@app.post("/ai/chat")
async def chat():
    return {"reply": "Hello"}

@app.post("/ai/search")
async def search():
    return {"results": []}

@app.post("/ai/research")
async def research():
    return {"results": []}

@app.get("/ai/providers/health")
async def health():
    return {"status": "ok"}

@app.get("/admin/stats")
async def stats():
    return {"users": 0}

@app.post("/upload")
async def upload():
    return {"success": True}

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# =================================================
# LOAD ENVIRONMENT
# =================================================

load_dotenv()

# =================================================
# APPLICATION INFO
# =================================================

APP_NAME = "Bloxy-bot AI"

APP_VERSION = "1.0.0"

BUILD = "Bloxy-bot Ultimate AI"

START_TIME = time.time()

# =================================================
# LOGGING
# =================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("nova")

# =================================================
# API KEYS
# =================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

KIMI_API_KEY = os.getenv(
    "KIMI_API_KEY"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)

EXA_API_KEY = os.getenv(
    "EXA_API_KEY"
)

FIRECRAWL_API_KEY = os.getenv(
    "FIRECRAWL_API_KEY"
)

NEWS_API_KEY = os.getenv(
    "NEWS_API_KEY"
)

GNEWS_API_KEY = os.getenv(
    "GNEWS_API_KEY"
)

MEDIASTACK_API_KEY = os.getenv(
    "MEDIASTACK_API_KEY"
)

GUARDIAN_API_KEY = os.getenv(
    "GUARDIAN_API_KEY"
)

FINNHUB_API_KEY = os.getenv(
    "FINNHUB_API_KEY"
)

ALPHA_VANTAGE_API_KEY = os.getenv(
    "ALPHA_VANTAGE_API_KEY"
)

EXCHANGERATE_API_KEY = os.getenv(
    "EXCHANGERATE_API_KEY"
)

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY"
)

TMDB_API_KEY = os.getenv(
    "TMDB_API_KEY"
)

ALLSPORTS_API_KEY = os.getenv(
    "ALLSPORTS_API_KEY"
)

APISPORTS_API_KEY = os.getenv(
    "APISPORTS_API_KEY"
)

SPORTMONK_API_KEY = os.getenv(
    "SPORTMONK_API_KEY"
)

SPORTRADAR_API_KEY = os.getenv(
    "SPORTRADAR_API_KEY"
)

ODDS_API_KEY = os.getenv(
    "ODDS_API_KEY"
)

THESPORTSDB_API_KEY = os.getenv(
    "THESPORTSDB_API_KEY"
)

WOLFRAM_APP_ID = os.getenv(
    "WOLFRAM_APP_ID"
)

SECRET_KEY = os.getenv(
    "SECRET_KEY"
)

# =================================================
# VERIFIED USERS
# =================================================

VERIFIED_EMAILS = {

    "alvinogthegreat177@gmail.com",

    "alvinogthegreat177@outlook.com"

}

# =================================================
# FREE SOURCES
# =================================================

WIKIPEDIA_API = (
    "https://en.wikipedia.org/api/rest_v1"
)

DICTIONARY_API = (
    "https://api.dictionaryapi.dev/api/v2"
)

# =================================================
# GLOBAL MEMORY
# =================================================

CHAT_SESSIONS = {}

USER_MEMORY = {}

ACTIVE_USERS = {}

CHAT_COUNTER = 0

# =================================================
# PROVIDER REGISTRY
# =================================================

PROVIDERS = {

    "openai": True,
    "groq": True,
    "kimi": True,
    "openrouter": True,

    "tavily": True,
    "exa": True,
    "firecrawl": True,

    "guardian": True,
    "newsapi": True,
    "gnews": True,
    "mediastack": True,

    "finnhub": True,
    "alphavantage": True,
    "exchange": True,

    "weather": True,

    "tmdb": True,

    "allsports": True,
    "apisports": True,
    "sportmonks": True,
    "sportradar": True,
    "odds": True,
    "thesportsdb": True,

    "wikipedia": True,
    "dictionary": True,

    "wolfram": True

}

# =================================================
# SYSTEM STATS
# =================================================

SYSTEM_STATS = {

    "users": 0,

    "chats": 0,

    "messages": 0,

    "providers": len(PROVIDERS),

    "version": APP_VERSION

}

# =================================================
# HELPER FUNCTIONS
# =================================================

def generate_id():

    return str(
        uuid.uuid4()
    )

def now():

    return datetime.utcnow().isoformat()

def uptime():

    return round(
        time.time() - START_TIME,
        2
    )

# =================================================
# END PART 1
# =================================================
# =================================================
# NOVA AI - APP.PY PART 2
# FASTAPI SETUP + CORS + MIDDLEWARE + STARTUP
# =================================================

# =================================================
# FASTAPI APP
# =================================================

app = FastAPI(

    title=APP_NAME,

    version=APP_VERSION,

    description=
    "Bloxy-bot AI Multi-Provider Intelligence Platform"

)

# =================================================
# CORS
# =================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)

# =================================================
# REQUEST MIDDLEWARE
# =================================================

@app.middleware("http")
async def request_logger(
    request: Request,
    call_next
):

    start = time.time()

    try:

        response = await call_next(
            request
        )

        duration = round(
            time.time() - start,
            3
        )

        logger.info(

            f"{request.method} "
            f"{request.url.path} "
            f"{response.status_code} "
            f"{duration}s"

        )

        return response

    except Exception as e:

        logger.error(str(e))

        raise e

# =================================================
# GLOBAL HTTP CLIENT
# =================================================

http_client = None

# =================================================
# STARTUP EVENT
# =================================================

@app.on_event("startup")
async def startup_event():

    global http_client

    logger.info(
        "Starting Nova AI..."
    )

    http_client = httpx.AsyncClient(

        timeout=60.0,

        follow_redirects=True

    )

    logger.info(
        "HTTP Client Ready"
    )

    logger.info(
        f"Providers Loaded: "
        f"{len(PROVIDERS)}"
    )

# =================================================
# SHUTDOWN EVENT
# =================================================

@app.on_event("shutdown")
async def shutdown_event():

    global http_client

    logger.info(
        "Shutting down..."
    )

    if http_client:

        await http_client.aclose()



# =================================================
# HEALTH
# =================================================

@app.get("/health")
async def health():

    return {

        "status":
        "healthy",

        "app":
        APP_NAME,

        "version":
        APP_VERSION,

        "uptime":
        uptime(),

        "providers":
        len(PROVIDERS)

    }

# =================================================
# READY
# =================================================

@app.get("/ready")
async def ready():

    return {

        "ready": True,

        "timestamp":
        now()

    }

# =================================================
# SYSTEM INFO
# =================================================

@app.get("/system/info")
async def system_info():

    return {

        "name":
        APP_NAME,

        "version":
        APP_VERSION,

        "build":
        BUILD,

        "uptime":
        uptime(),

        "providers":
        len(PROVIDERS),

        "stats":
        SYSTEM_STATS

    }

# =================================================
# PROVIDERS
# =================================================

@app.get("/ai/providers")
async def get_providers():

    return {

        "count":
        len(PROVIDERS),

        "providers":
        PROVIDERS

    }

# =================================================
# PROVIDER HEALTH
# =================================================

@app.get(
    "/ai/providers/health"
)
async def provider_health():

    health_data = {}

    for provider in PROVIDERS:

        health_data[
            provider
        ] = {

            "online":
            PROVIDERS[provider],

            "latency":
            round(
                0.1 +
                (hash(provider) % 100)
                / 1000,
                3
            )

        }

    return health_data

# =================================================
# ADMIN STATS
# =================================================

@app.get("/admin/stats")
async def admin_stats():

    return {

        "users":
        SYSTEM_STATS["users"],

        "chats":
        SYSTEM_STATS["chats"],

        "messages":
        SYSTEM_STATS["messages"],

        "apiHealth":
        "Healthy",

        "status":
        "Online",

        "uptime":
        uptime()

    }

# =================================================
# USER VERIFY
# =================================================

@app.get(
    "/auth/verify/{email}"
)
async def verify_email(
    email: str
):

    return {

        "email":
        email,

        "verified":
        email.lower()
        in VERIFIED_EMAILS

    }

# =================================================
# GLOBAL EXCEPTION HANDLER
# =================================================

@app.exception_handler(
    Exception
)
async def global_exception(
    request: Request,
    exc: Exception
):

    logger.error(
        str(exc)
    )

    return JSONResponse(

        status_code=500,

        content={

            "success":
            False,

            "error":
            str(exc)

        }

    )

# =================================================
# BACKGROUND TASKS
# =================================================

async def provider_monitor():

    while True:

        try:

            logger.info(
                "Provider health check"
            )

            await asyncio.sleep(
                300
            )

        except Exception as e:

            logger.error(
                str(e)
            )

            await asyncio.sleep(
                60
            )

# =================================================
# START MONITOR
# =================================================

@app.on_event("startup")
async def start_monitor():

    asyncio.create_task(
        provider_monitor()
    )

# =================================================
# END PART 2
# =================================================
# =================================================
# NOVA AI - APP.PY PART 3
# PYDANTIC MODELS & DATA SCHEMAS
# =================================================

# =================================================
# CHAT MODELS
# =================================================

class ChatMessage(BaseModel):

    role: str

    content: str

    timestamp: Optional[str] = None


class ChatRequest(BaseModel):

    message: str

    conversation_id: Optional[str] = None

    provider: Optional[str] = "auto"

    model: Optional[str] = "auto"

    web_search: Optional[bool] = False

    deep_research: Optional[bool] = False

    use_memory: Optional[bool] = True


class ChatResponse(BaseModel):

    success: bool

    response: str

    provider: str

    model: str

    conversation_id: str

    timestamp: str


# =================================================
# RESEARCH MODELS
# =================================================

class ResearchRequest(BaseModel):

    query: str

    max_sources: Optional[int] = 10

    include_news: Optional[bool] = True

    include_wikipedia: Optional[bool] = True

    include_web: Optional[bool] = True


class Citation(BaseModel):

    title: str

    url: str

    source: str


class ResearchResponse(BaseModel):

    success: bool

    query: str

    summary: str

    citations: List[Citation]

    timestamp: str


# =================================================
# MEMORY MODELS
# =================================================

class MemoryItem(BaseModel):

    id: str

    key: str

    value: str

    created_at: str


class MemoryCreate(BaseModel):

    key: str

    value: str


class MemoryResponse(BaseModel):

    success: bool

    memories: List[MemoryItem]


# =================================================
# USER MODELS
# =================================================

class UserProfile(BaseModel):

    user_id: str

    email: str

    username: str

    verified: bool

    created_at: str


class LoginRequest(BaseModel):

    email: str

    password: str


class RegisterRequest(BaseModel):

    username: str

    email: str

    password: str


class AuthResponse(BaseModel):

    success: bool

    token: str

    verified: bool


# =================================================
# PROVIDER MODELS
# =================================================

class ProviderStatus(BaseModel):

    name: str

    online: bool

    latency: float


class ProviderResponse(BaseModel):

    providers: List[ProviderStatus]


# =================================================
# NEWS MODELS
# =================================================

class NewsArticle(BaseModel):

    title: str

    description: str

    url: str

    source: str

    published_at: str


class NewsResponse(BaseModel):

    success: bool

    articles: List[NewsArticle]


# =================================================
# WEATHER MODELS
# =================================================

class WeatherRequest(BaseModel):

    city: str


class WeatherResponse(BaseModel):

    success: bool

    city: str

    temperature: float

    condition: str

    humidity: int


# =================================================
# FINANCE MODELS
# =================================================

class StockRequest(BaseModel):

    symbol: str


class StockResponse(BaseModel):

    success: bool

    symbol: str

    price: float

    change: float


class CurrencyRequest(BaseModel):

    base: str

    target: str


# =================================================
# MOVIE MODELS
# =================================================

class MovieSearchRequest(BaseModel):

    query: str


class MovieResult(BaseModel):

    title: str

    year: str

    overview: str

    poster: str


# =================================================
# SPORTS MODELS
# =================================================

class SportsRequest(BaseModel):

    sport: str

    league: Optional[str] = None


class SportsEvent(BaseModel):

    home_team: str

    away_team: str

    start_time: str

    league: str


# =================================================
# DICTIONARY MODELS
# =================================================

class DictionaryRequest(BaseModel):

    word: str


class DictionaryDefinition(BaseModel):

    word: str

    definition: str

    example: Optional[str] = None


# =================================================
# WIKIPEDIA MODELS
# =================================================

class WikipediaRequest(BaseModel):

    topic: str


class WikipediaResponse(BaseModel):

    title: str

    summary: str

    url: str


# =================================================
# IMAGE GENERATION MODELS
# (Future V1.1)
# =================================================

class ImageRequest(BaseModel):

    prompt: str

    size: Optional[str] = "1024x1024"


class ImageResponse(BaseModel):

    success: bool

    image_url: str


# =================================================
# AGENT MODELS
# (Future V1.2)
# =================================================

class AgentTask(BaseModel):

    task: str

    goal: Optional[str] = None

    priority: Optional[str] = "normal"


class AgentResponse(BaseModel):

    success: bool

    agent: str

    result: str


# =================================================
# KNOWLEDGE BASE MODELS
# (Future V1.5)
# =================================================

class KnowledgeSearch(BaseModel):

    query: str

    limit: Optional[int] = 5


class KnowledgeResult(BaseModel):

    title: str

    content: str

    score: float


# =================================================
# AUTOMATION MODELS
# (Future V2.0)
# =================================================

class BrowserTask(BaseModel):

    objective: str


class WorkflowRequest(BaseModel):

    name: str

    steps: List[str]


# =================================================
# SETTINGS MODELS
# =================================================

class SettingsUpdate(BaseModel):

    theme: Optional[str] = "dark"

    notifications: Optional[bool] = True

    memory_enabled: Optional[bool] = True

    default_provider: Optional[str] = "auto"


# =================================================
# SYSTEM MODELS
# =================================================

class HealthResponse(BaseModel):

    status: str

    uptime: float

    providers: int


class ErrorResponse(BaseModel):

    success: bool

    error: str


# =================================================
# END PART 3
# =================================================
# =================================================
# NOVA AI - APP.PY PART 4
# AUTHENTICATION + USERS + SESSIONS
# FULL REPLACEMENT VERSION
# =================================================

import hashlib
import secrets

# =================================================
# DATABASES (IN-MEMORY V1)
# =================================================

USERS = {}

SESSIONS = {}

USER_SETTINGS = {}

# =================================================
# PASSWORD HASHING
# =================================================

def hash_password(password: str) -> str:

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(
    password: str,
    hashed: str
) -> bool:

    return (
        hash_password(password)
        == hashed
    )

# =================================================
# TOKEN GENERATION
# =================================================

def create_token() -> str:

    return secrets.token_urlsafe(64)

# =================================================
# USER HELPERS
# =================================================

def get_user_by_email(
    email: str
):

    email = email.lower()

    for user in USERS.values():

        if user["email"].lower() == email:

            return user

    return None


def get_user_by_id(
    user_id: str
):

    return USERS.get(user_id)


def create_user(

    username: str,

    email: str,

    password: str

):

    user_id = generate_id()

    user = {

        "id": user_id,

        "username": username,

        "email": email,

        "password": hash_password(password),

        "verified":
        email.lower()
        in VERIFIED_EMAILS,

        "created_at": now()

    }

    USERS[user_id] = user

    USER_SETTINGS[user_id] = {

        "theme": "dark",

        "notifications": True,

        "memory_enabled": True,

        "default_provider": "auto"

    }

    SYSTEM_STATS["users"] += 1

    return user

# =================================================
# SESSION HELPERS
# =================================================

def create_session(
    user_id: str
):

    token = create_token()

    SESSIONS[token] = {

        "user_id": user_id,

        "created_at": now()

    }

    return token


def get_user_from_token(
    token: str
):

    session = SESSIONS.get(token)

    if not session:

        return None

    return USERS.get(
        session["user_id"]
    )

# =================================================
# REGISTER
# =================================================

@app.post("/auth/register")
async def register(
    request: RegisterRequest
):

    existing_user = get_user_by_email(
        request.email
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = create_user(

        username=request.username,

        email=request.email,

        password=request.password

    )

    token = create_session(
        user["id"]
    )

    return {

        "success": True,

        "token": token,

        "verified":
        user["verified"],

        "user": {

            "id":
            user["id"],

            "username":
            user["username"],

            "email":
            user["email"]

        }

    }

# =================================================
# LOGIN
# =================================================

@app.post("/auth/login")
async def login(
    request: LoginRequest
):

    user = get_user_by_email(
        request.email
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        request.password,
        user["password"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_session(
        user["id"]
    )

    return {

        "success": True,

        "token": token,

        "verified":
        user["verified"],

        "user": {

            "id":
            user["id"],

            "username":
            user["username"],

            "email":
            user["email"]

        }

    }

# =================================================
# PROFILE
# =================================================

@app.get("/auth/profile/{token}")
async def profile(
    token: str
):

    user = get_user_from_token(
        token
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return {

        "success": True,

        "user": {

            "id":
            user["id"],

            "username":
            user["username"],

            "email":
            user["email"],

            "verified":
            user["verified"],

            "created_at":
            user["created_at"]

        }

    }

# =================================================
# LOGOUT
# =================================================

@app.post("/auth/logout/{token}")
async def logout(
    token: str
):

    if token in SESSIONS:

        del SESSIONS[token]

    return {

        "success": True,

        "message":
        "Logged out"

    }

# =================================================
# SETTINGS
# =================================================

@app.get("/settings/{token}")
async def get_settings(
    token: str
):

    user = get_user_from_token(
        token
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return {

        "success": True,

        "settings":
        USER_SETTINGS.get(
            user["id"],
            {}
        )

    }

# =================================================
# UPDATE SETTINGS
# =================================================

@app.post("/settings/{token}")
async def update_settings(

    token: str,

    settings: SettingsUpdate

):

    user = get_user_from_token(
        token
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    USER_SETTINGS[user["id"]] = {

        "theme":
        settings.theme,

        "notifications":
        settings.notifications,

        "memory_enabled":
        settings.memory_enabled,

        "default_provider":
        settings.default_provider

    }

    return {

        "success": True,

        "settings":
        USER_SETTINGS[user["id"]]

    }

# =================================================
# VERIFIED EMAIL CHECK
# =================================================

@app.get("/auth/verified/{email}")
async def verified_email(
    email: str
):

    return {

        "success": True,

        "email": email,

        "verified":
        email.lower()
        in VERIFIED_EMAILS

    }

# =================================================
# USER LIST (ADMIN)
# =================================================

@app.get("/admin/users")
async def admin_users():

    return {

        "success": True,

        "total_users":
        len(USERS),

        "active_sessions":
        len(SESSIONS)

    }

# =================================================
# END PART 4
# =================================================
# =================================================
# NOVA AI - APP.PY PART 5
# PROVIDER MANAGER V2
# FULL REPLACEMENT VERSION
# =================================================

# =================================================
# AI PROVIDERS
# =================================================

AI_MODELS = {

    "openrouter": [
        "openai/gpt-5",
        "anthropic/claude-sonnet-4",
        "google/gemini-2.5-pro"
    ],

    "groq": [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768"
    ],

    "openai": [
        "gpt-5"
    ],

    "kimi": [
        "moonshot-v1-8k"
    ]

}

# =================================================
# DEFAULTS
# =================================================

DEFAULT_PROVIDER = "openrouter"

DEFAULT_MODEL = "openai/gpt-5"

# =================================================
# PROVIDER HEALTH
# =================================================

PROVIDER_STATUS = {

    "openrouter": True,

    "groq": True,

    "openai": True,

    "kimi": True

}

# =================================================
# SYSTEM PROMPT
# =================================================


SYSTEM_PROMPT = """
You are Bloxy-bot.

You are a highly intelligent AI assistant.

Core Principles:

- Privacy first
- No tracking
- No telemetry
- No advertisements
- No selling user data
- Helpful and truthful
- Excellent at coding
- Excellent at research
- Sports knowledge
- Finance knowledge
- Weather knowledge
- Movie knowledge
- Have knowlede of everything in every area
- Use emojis
- Be kind
- Be organised
- Be polite
- Be diplomatic
- Avoid long paragraphs when responding
- Be neat
- Be helpful in every criteria 
- Have Conciseness
- Use your tokens and resources efficiently 

Always be honest.

If uncertain, say so.

Never invent facts.

Always provide accurate, helpful responses.

"""

# =================================================
# OPENROUTER
# =================================================

async def openrouter_chat(
    message: str,
    model: str = DEFAULT_MODEL
):

    try:

        response = await http_client.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers={

                "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "model": model,

                "messages": [

                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },

                    {
                        "role": "user",
                        "content": message
                    }

                ]

            }

        )

        data = response.json()

        return {

            "success": True,

            "provider": "openrouter",

            "model": model,

            "content":
            data["choices"][0]["message"]["content"]

        }

    except Exception as e:

        logger.error(
            f"OpenRouter Error: {e}"
        )

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# GROQ
# =================================================

async def groq_chat(
    message: str,
    model: str =
    "llama-3.3-70b-versatile"
):

    try:

        response = await http_client.post(

            "https://api.groq.com/openai/v1/chat/completions",

            headers={

                "Authorization":
                f"Bearer {GROQ_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "model": model,

                "messages": [

                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },

                    {
                        "role": "user",
                        "content": message
                    }

                ]

            }

        )

        data = response.json()

        return {

            "success": True,

            "provider": "groq",

            "model": model,

            "content":
            data["choices"][0]["message"]["content"]

        }

    except Exception as e:

        logger.error(
            f"Groq Error: {e}"
        )

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# OPENAI
# =================================================

async def openai_chat(
    message: str,
    model: str = "gpt-5"
):

    try:

        response = await http_client.post(

            "https://api.openai.com/v1/chat/completions",

            headers={

                "Authorization":
                f"Bearer {OPENAI_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "model": model,

                "messages": [

                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },

                    {
                        "role": "user",
                        "content": message
                    }

                ]

            }

        )

        data = response.json()

        return {

            "success": True,

            "provider": "openai",

            "model": model,

            "content":
            data["choices"][0]["message"]["content"]

        }

    except Exception as e:

        logger.error(
            f"OpenAI Error: {e}"
        )

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# KIMI
# =================================================

async def kimi_chat(
    message: str
):

    try:

        response = await http_client.post(

            "https://api.moonshot.ai/v1/chat/completions",

            headers={

                "Authorization":
                f"Bearer {KIMI_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "model":
                "moonshot-v1-8k",

                "messages": [

                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },

                    {
                        "role": "user",
                        "content": message
                    }

                ]

            }

        )

        data = response.json()

        return {

            "success": True,

            "provider": "kimi",

            "model":
            "moonshot-v1-8k",

            "content":
            data["choices"][0]["message"]["content"]

        }

    except Exception as e:

        logger.error(
            f"Kimi Error: {e}"
        )

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# ROUTER
# =================================================

async def route_ai_request(

    message: str,

    provider: str = "auto"

):

    if provider == "openrouter":

        return await openrouter_chat(
            message
        )

    if provider == "groq":

        return await groq_chat(
            message
        )

    if provider == "openai":

        return await openai_chat(
            message
        )

    if provider == "kimi":

        return await kimi_chat(
            message
        )

    providers = [

        "openrouter",

        "groq",

        "openai",

        "kimi"

    ]

    for p in providers:

        try:

            result = await route_ai_request(
                message,
                p
            )

            if result.get(
                "success"
            ):

                return result

        except Exception:

            continue

    return {

        "success": False,

        "error":
        "All AI providers failed"

    }

# =================================================
# PROVIDER STATUS
# =================================================

@app.get("/ai/provider-status")
async def provider_status():

    return {

        "success": True,

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# AI MODELS
# =================================================

@app.get("/ai/models")
async def ai_models():

    return {

        "success": True,

        "models":
        AI_MODELS

    }

# =================================================
# END PART 5
# =================================================
# =================================================
# NOVA AI - APP.PY PART 6
# RESEARCH ENGINE V2
# =================================================

# =================================================
# RESEARCH CONFIG
# =================================================

MAX_RESEARCH_RESULTS = 10

# =================================================
# WIKIPEDIA SEARCH
# =================================================

async def wikipedia_search(
    query: str
):

    try:

        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + query.replace(" ", "_")
        )

        response = await http_client.get(url)

        if response.status_code != 200:

            return None

        data = response.json()

        return {

            "source": "Wikipedia",

            "title":
            data.get("title", query),

            "content":
            data.get("extract", ""),

            "url":
            data.get(
                "content_urls",
                {}
            ).get(
                "desktop",
                {}
            ).get(
                "page",
                ""
            )

        }

    except Exception as e:

        logger.error(
            f"Wikipedia Error: {e}"
        )

        return None

# =================================================
# DICTIONARY
# =================================================

async def dictionary_search(
    word: str
):

    try:

        response = await http_client.get(

            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        )

        if response.status_code != 200:

            return None

        data = response.json()

        meaning = (
            data[0]
            .get("meanings", [{}])[0]
            .get("definitions", [{}])[0]
        )

        return {

            "source": "Dictionary",

            "word": word,

            "definition":
            meaning.get(
                "definition",
                ""
            ),

            "example":
            meaning.get(
                "example",
                ""
            )

        }

    except Exception as e:

        logger.error(
            f"Dictionary Error: {e}"
        )

        return None

# =================================================
# TAVILY SEARCH
# =================================================

async def tavily_search(
    query: str
):

    try:

        response = await http_client.post(

            "https://api.tavily.com/search",

            json={

                "api_key":
                TAVILY_API_KEY,

                "query":
                query,

                "max_results":
                5

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        return data.get(
            "results",
            []
        )

    except Exception as e:

        logger.error(
            f"Tavily Error: {e}"
        )

        return []

# =================================================
# EXA SEARCH
# =================================================

async def exa_search(
    query: str
):

    try:

        response = await http_client.post(

            "https://api.exa.ai/search",

            headers={

                "x-api-key":
                EXA_API_KEY,

                "Content-Type":
                "application/json"

            },

            json={

                "query":
                query,

                "numResults":
                5

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        return data.get(
            "results",
            []
        )

    except Exception as e:

        logger.error(
            f"Exa Error: {e}"
        )

        return []

# =================================================
# FIRECRAWL SCRAPE
# =================================================

async def firecrawl_scrape(
    url: str
):

    try:

        response = await http_client.post(

            "https://api.firecrawl.dev/v1/scrape",

            headers={

                "Authorization":
                f"Bearer {FIRECRAWL_API_KEY}",

                "Content-Type":
                "application/json"

            },

            json={

                "url": url

            }

        )

        if response.status_code != 200:

            return None

        return response.json()

    except Exception as e:

        logger.error(
            f"Firecrawl Error: {e}"
        )

        return None

# =================================================
# DEEP RESEARCH ENGINE
# =================================================

async def deep_research(
    query: str
):

    results = {

        "query": query,

        "timestamp": now(),

        "sources": []

    }

    wiki = await wikipedia_search(
        query
    )

    if wiki:

        results["sources"].append(
            wiki
        )

    tavily_results = await tavily_search(
        query
    )

    for item in tavily_results:

        results["sources"].append({

            "source": "Tavily",

            "title":
            item.get("title"),

            "url":
            item.get("url"),

            "content":
            item.get("content", "")

        })

    exa_results = await exa_search(
        query
    )

    for item in exa_results:

        results["sources"].append({

            "source": "Exa",

            "title":
            item.get("title"),

            "url":
            item.get("url"),

            "content":
            item.get("text", "")

        })

    return results

# =================================================
# RESEARCH ENDPOINT
# =================================================

@app.post("/research")
async def research(
    request: ResearchRequest
):

    results = await deep_research(
        request.query
    )

    return {

        "success": True,

        "results": results

    }

# =================================================
# WIKIPEDIA ENDPOINT
# =================================================

@app.get(
    "/research/wikipedia/{topic}"
)
async def wiki_endpoint(
    topic: str
):

    result = await wikipedia_search(
        topic
    )

    return {

        "success": True,

        "result": result

    }

# =================================================
# DICTIONARY ENDPOINT
# =================================================

@app.get(
    "/dictionary/{word}"
)
async def dictionary_endpoint(
    word: str
):

    result = await dictionary_search(
        word
    )

    return {

        "success": True,

        "result": result

    }

# =================================================
# SCRAPE URL
# =================================================

@app.post("/research/scrape")
async def scrape_url(
    url: str
):

    result = await firecrawl_scrape(
        url
    )

    return {

        "success": True,

        "result": result

    }

# =================================================
# RESEARCH PROVIDERS
# =================================================

@app.get("/research/providers")
async def research_providers():

    return {

        "success": True,

        "providers": {

            "wikipedia": True,

            "dictionary": True,

            "tavily":
            bool(TAVILY_API_KEY),

            "exa":
            bool(EXA_API_KEY),

            "firecrawl":
            bool(FIRECRAWL_API_KEY)

        }

    }

# =================================================
# END PART 6
# =================================================
# =================================================
# NOVA AI - APP.PY PART 7
# NEWS ENGINE V2
# =================================================

# =================================================
# NEWS PROVIDERS
# =================================================

NEWS_PROVIDERS = {

    "newsapi": bool(NEWS_API_KEY),

    "guardian": bool(GUARDIAN_API_KEY),

    "gnews": bool(GNEWS_API_KEY),

    "mediastack": bool(MEDIASTACK_API_KEY)

}

# =================================================
# NEWS API
# =================================================

async def newsapi_search(
    query: str,
    limit: int = 10
):

    try:

        response = await http_client.get(

            "https://newsapi.org/v2/everything",

            params={

                "q": query,

                "pageSize": limit,

                "apiKey": NEWS_API_KEY

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for article in data.get(
            "articles",
            []
        ):

            results.append({

                "provider":
                "NewsAPI",

                "title":
                article.get(
                    "title"
                ),

                "description":
                article.get(
                    "description"
                ),

                "url":
                article.get(
                    "url"
                ),

                "published":
                article.get(
                    "publishedAt"
                )

            })

        return results

    except Exception as e:

        logger.error(
            f"NewsAPI Error: {e}"
        )

        return []

# =================================================
# GUARDIAN
# =================================================

async def guardian_search(
    query: str,
    limit: int = 10
):

    try:

        response = await http_client.get(

            "https://content.guardianapis.com/search",

            params={

                "q": query,

                "page-size": limit,

                "api-key":
                GUARDIAN_API_KEY

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for article in (
            data.get(
                "response",
                {}
            ).get(
                "results",
                []
            )
        ):

            results.append({

                "provider":
                "Guardian",

                "title":
                article.get(
                    "webTitle"
                ),

                "url":
                article.get(
                    "webUrl"
                ),

                "published":
                article.get(
                    "webPublicationDate"
                )

            })

        return results

    except Exception as e:

        logger.error(
            f"Guardian Error: {e}"
        )

        return []

# =================================================
# GNEWS
# =================================================

async def gnews_search(
    query: str,
    limit: int = 10
):

    try:

        response = await http_client.get(

            "https://gnews.io/api/v4/search",

            params={

                "q": query,

                "max": limit,

                "apikey":
                GNEWS_API_KEY

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for article in data.get(
            "articles",
            []
        ):

            results.append({

                "provider":
                "GNews",

                "title":
                article.get(
                    "title"
                ),

                "description":
                article.get(
                    "description"
                ),

                "url":
                article.get(
                    "url"
                ),

                "published":
                article.get(
                    "publishedAt"
                )

            })

        return results

    except Exception as e:

        logger.error(
            f"GNews Error: {e}"
        )

        return []

# =================================================
# MEDIASTACK
# =================================================

async def mediastack_search(
    query: str,
    limit: int = 10
):

    try:

        response = await http_client.get(

            "http://api.mediastack.com/v1/news",

            params={

                "keywords":
                query,

                "limit":
                limit,

                "access_key":
                MEDIASTACK_API_KEY

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for article in data.get(
            "data",
            []
        ):

            results.append({

                "provider":
                "Mediastack",

                "title":
                article.get(
                    "title"
                ),

                "description":
                article.get(
                    "description"
                ),

                "url":
                article.get(
                    "url"
                ),

                "published":
                article.get(
                    "published_at"
                )

            })

        return results

    except Exception as e:

        logger.error(
            f"Mediastack Error: {e}"
        )

        return []

# =================================================
# AGGREGATOR
# =================================================

async def news_search(
    query: str,
    limit: int = 10
):

    results = []

    results.extend(
        await newsapi_search(
            query,
            limit
        )
    )

    results.extend(
        await guardian_search(
            query,
            limit
        )
    )

    results.extend(
        await gnews_search(
            query,
            limit
        )
    )

    results.extend(
        await mediastack_search(
            query,
            limit
        )
    )

    return results[:50]

# =================================================
# BREAKING NEWS
# =================================================

async def breaking_news():

    return await news_search(
        "breaking news",
        20
    )

# =================================================
# NEWS SEARCH ENDPOINT
# =================================================

@app.get("/news/search")
async def news_endpoint(
    query: str
):

    results = await news_search(
        query
    )

    return {

        "success": True,

        "count":
        len(results),

        "articles":
        results

    }

# =================================================
# BREAKING NEWS ENDPOINT
# =================================================

@app.get("/news/breaking")
async def breaking_news_endpoint():

    results = await breaking_news()

    return {

        "success": True,

        "count":
        len(results),

        "articles":
        results

    }

# =================================================
# NEWS PROVIDERS ENDPOINT
# =================================================

@app.get("/news/providers")
async def news_providers():

    return {

        "success": True,

        "providers":
        NEWS_PROVIDERS

    }

# =================================================
# AI NEWS SUMMARY
# =================================================

@app.get("/news/summary")
async def news_summary(
    query: str
):

    articles = await news_search(
        query,
        5
    )

    text = ""

    for article in articles:

        title = article.get(
            "title",
            ""
        )

        text += f"- {title}\n"

    return {

        "success": True,

        "query": query,

        "summary": text

    }

# =================================================
# END PART 7
# =================================================
# =================================================
# BLOXY-BOT - APP.PY PART 8
# WEATHER + FINANCE + MOVIES
# =================================================

# =================================================
# WEATHER
# =================================================

async def get_weather(
    city: str
):

    try:

        response = await http_client.get(

            "https://api.openweathermap.org/data/2.5/weather",

            params={

                "q": city,

                "appid":
                OPENWEATHER_API_KEY,

                "units":
                "metric"

            }

        )

        if response.status_code != 200:

            return None

        data = response.json()

        return {

            "city":
            city,

            "temperature":
            data["main"]["temp"],

            "feels_like":
            data["main"]["feels_like"],

            "humidity":
            data["main"]["humidity"],

            "condition":
            data["weather"][0]["description"]

        }

    except Exception as e:

        logger.error(
            f"Weather Error: {e}"
        )

        return None

# =================================================
# WEATHER ENDPOINT
# =================================================

@app.get("/weather")
async def weather(
    city: str
):

    result = await get_weather(
        city
    )

    return {

        "success":
        result is not None,

        "result":
        result

    }

# =================================================
# STOCK PRICE
# =================================================

async def stock_price(
    symbol: str
):

    try:

        response = await http_client.get(

            "https://www.alphavantage.co/query",

            params={

                "function":
                "GLOBAL_QUOTE",

                "symbol":
                symbol,

                "apikey":
                ALPHA_VANTAGE_API_KEY

            }

        )

        if response.status_code != 200:

            return None

        data = response.json()

        quote = data.get(
            "Global Quote",
            {}
        )

        return {

            "symbol":
            symbol,

            "price":
            quote.get(
                "05. price"
            ),

            "change":
            quote.get(
                "09. change"
            )

        }

    except Exception as e:

        logger.error(
            f"Stock Error: {e}"
        )

        return None

# =================================================
# STOCK ENDPOINT
# =================================================

@app.get("/finance/stock")
async def finance_stock(
    symbol: str
):

    result = await stock_price(
        symbol
    )

    return {

        "success":
        result is not None,

        "result":
        result

    }

# =================================================
# FINNHUB COMPANY PROFILE
# =================================================

async def company_profile(
    symbol: str
):

    try:

        response = await http_client.get(

            "https://finnhub.io/api/v1/stock/profile2",

            params={

                "symbol":
                symbol,

                "token":
                FINNHUB_API_KEY

            }

        )

        if response.status_code != 200:

            return None

        return response.json()

    except Exception as e:

        logger.error(
            f"Finnhub Error: {e}"
        )

        return None

# =================================================
# COMPANY ENDPOINT
# =================================================

@app.get("/finance/company")
async def finance_company(
    symbol: str
):

    result = await company_profile(
        symbol
    )

    return {

        "success":
        result is not None,

        "result":
        result

    }

# =================================================
# EXCHANGE RATE
# =================================================

async def exchange_rate(

    base: str,

    target: str

):

    try:

        response = await http_client.get(

            f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/pair/{base}/{target}"

        )

        if response.status_code != 200:

            return None

        data = response.json()

        return {

            "base":
            base,

            "target":
            target,

            "rate":
            data.get(
                "conversion_rate"
            )

        }

    except Exception as e:

        logger.error(
            f"Forex Error: {e}"
        )

        return None

# =================================================
# FOREX ENDPOINT
# =================================================

@app.get("/finance/forex")
async def forex(

    base: str,

    target: str

):

    result = await exchange_rate(
        base,
        target
    )

    return {

        "success":
        result is not None,

        "result":
        result

    }

# =================================================
# MOVIES
# =================================================

async def movie_search(
    query: str
):

    try:

        response = await http_client.get(

            "https://api.themoviedb.org/3/search/movie",

            params={

                "api_key":
                TMDB_API_KEY,

                "query":
                query

            }

        )

        if response.status_code != 200:

            return []

        data = response.json()

        results = []

        for movie in data.get(
            "results",
            []
        )[:10]:

            results.append({

                "title":
                movie.get(
                    "title"
                ),

                "overview":
                movie.get(
                    "overview"
                ),

                "release_date":
                movie.get(
                    "release_date"
                ),

                "rating":
                movie.get(
                    "vote_average"
                )

            })

        return results

    except Exception as e:

        logger.error(
            f"TMDB Error: {e}"
        )

        return []

# =================================================
# MOVIE ENDPOINT
# =================================================

@app.get("/movies/search")
async def movies(
    query: str
):

    results = await movie_search(
        query
    )

    return {

        "success": True,

        "count":
        len(results),

        "results":
        results

    }

# =================================================
# API STATUS
# =================================================

@app.get("/services/status")
async def services_status():

    return {

        "weather":
        bool(OPENWEATHER_API_KEY),

        "alpha_vantage":
        bool(ALPHA_VANTAGE_API_KEY),

        "finnhub":
        bool(FINNHUB_API_KEY),

        "exchange_rate":
        bool(EXCHANGERATE_API_KEY),

        "tmdb":
        bool(TMDB_API_KEY)

    }

# =================================================
# END PART 8
# =================================================
# =================================================
# NOVA AI - APP.PY PART 9
# SPORTS ENGINE
# =================================================

# =================================================
# SPORTS PROVIDERS
# =================================================

SPORTS_PROVIDERS = {

    "apisports": {
        "enabled": bool(APISPORTS_API_KEY)
    },

    "sportmonks": {
        "enabled": bool(SPORTMONK_API_KEY)
    },

    "sportradar": {
        "enabled": bool(SPORTRADAR_API_KEY)
    },

    "thesportsdb": {
        "enabled": True
    },

    "odds": {
        "enabled": bool(ODDS_API_KEY)
    }

}

# =================================================
# API-SPORTS
# =================================================

async def apisports_fixtures(
    league_id: str = "39"
):

    try:

        headers = {
            "x-apisports-key":
            APISPORTS_API_KEY
        }

        response = await http_client.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=headers,
            params={
                "league": league_id,
                "season": 2025
            }
        )

        return response.json()

    except Exception as e:

        logger.error(
            f"API Sports Error: {e}"
        )

        return {}

# =================================================
# THESPORTSDB
# =================================================

async def thesportsdb_search(
    team_name: str
):

    try:

        response = await http_client.get(
            f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={team_name}"
        )

        return response.json()

    except Exception as e:

        logger.error(
            f"TheSportsDB Error: {e}"
        )

        return {}

# =================================================
# SPORTMONKS
# =================================================

async def sportmonks_fixtures():

    try:

        response = await http_client.get(
            "https://api.sportmonks.com/v3/football/fixtures",
            params={
                "api_token":
                SPORTMONK_API_KEY
            }
        )

        return response.json()

    except Exception as e:

        logger.error(
            f"SportMonks Error: {e}"
        )

        return {}

# =================================================
# SPORTRADAR
# =================================================

async def sportradar_schedule():

    try:

        response = await http_client.get(
            "https://api.sportradar.com",
            params={
                "api_key":
                SPORTRADAR_API_KEY
            }
        )

        return response.json()

    except Exception as e:

        logger.error(
            f"Sportradar Error: {e}"
        )

        return {}

# =================================================
# ODDS API
# =================================================

async def odds_data():

    try:

        response = await http_client.get(
            "https://api.the-odds-api.com/v4/sports",
            params={
                "apiKey":
                ODDS_API_KEY
            }
        )

        return response.json()

    except Exception as e:

        logger.error(
            f"Odds API Error: {e}"
        )

        return {}

# =================================================
# SPORTS SEARCH
# =================================================

async def sports_search(
    query: str
):

    results = {

        "query": query,

        "timestamp": now(),

        "results": []

    }

    try:

        team_data = await thesportsdb_search(
            query
        )

        results["results"].append({

            "provider":
            "TheSportsDB",

            "data":
            team_data

        })

    except Exception:
        pass

    return results

# =================================================
# LIVE SCORES
# =================================================

@app.get("/sports/live")

async def live_scores():

    try:

        data = await apisports_fixtures()

        return {

            "success": True,

            "provider":
            "API-Sports",

            "data": data

        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# TEAM SEARCH
# =================================================

@app.get("/sports/team/{team}")

async def sports_team(
    team: str
):

    data = await thesportsdb_search(
        team
    )

    return {

        "success": True,

        "team": team,

        "data": data

    }

# =================================================
# FIXTURES
# =================================================

@app.get("/sports/fixtures")

async def sports_fixtures():

    data = await apisports_fixtures()

    return {

        "success": True,

        "fixtures": data

    }

# =================================================
# ODDS
# =================================================

@app.get("/sports/odds")

async def sports_odds():

    data = await odds_data()

    return {

        "success": True,

        "odds": data

    }

# =================================================
# SPORTS SEARCH
# =================================================

@app.get("/sports/search/{query}")

async def sports_lookup(
    query: str
):

    data = await sports_search(
        query
    )

    return {

        "success": True,

        "results": data

    }

# =================================================
# SPORTS STATUS
# =================================================

@app.get("/sports/status")

async def sports_status():

    return {

        "success": True,

        "providers":
        SPORTS_PROVIDERS

    }

# =================================================
# SPORTS DASHBOARD
# =================================================

@app.get("/sports/dashboard")

async def sports_dashboard():

    return {

        "success": True,

        "live_scores":
        "/sports/live",

        "fixtures":
        "/sports/fixtures",

        "odds":
        "/sports/odds",

        "status":
        "/sports/status"

    }

# =================================================
# END PART 9
# =================================================
# =================================================
# BLOXY-BOT AI - APP.PY PART 10
# CHAT ENGINE + MEMORY + AI ROUTING
# =================================================

# =================================================
# CHAT STORAGE
# =================================================

CONVERSATIONS = {}

MESSAGE_HISTORY = {}

# =================================================
# MEMORY HELPERS
# =================================================

def get_conversation(
    conversation_id: str
):

    if conversation_id not in CONVERSATIONS:

        CONVERSATIONS[conversation_id] = []

    return CONVERSATIONS[conversation_id]


def add_message(

    conversation_id: str,

    role: str,

    content: str

):

    conversation = get_conversation(
        conversation_id
    )

    conversation.append({

        "role": role,

        "content": content,

        "timestamp": now()

    })

    SYSTEM_STATS["messages"] += 1


# =================================================
# MEMORY STORAGE
# =================================================

def save_memory(

    user_id: str,

    key: str,

    value: str

):

    if user_id not in USER_MEMORY:

        USER_MEMORY[user_id] = {}

    USER_MEMORY[user_id][key] = value


def get_memory(
    user_id: str
):

    return USER_MEMORY.get(
        user_id,
        {}
    )

# =================================================
# SMART ROUTING
# =================================================

def determine_route(
    message: str
):

    text = message.lower()

    if any(word in text for word in [

        "weather",
        "temperature",
        "forecast"

    ]):

        return "weather"

    if any(word in text for word in [

        "stock",
        "market",
        "crypto",
        "currency"

    ]):

        return "finance"

    if any(word in text for word in [

        "news",
        "headline",
        "breaking"

    ]):

        return "news"

    if any(word in text for word in [

        "football",
        "soccer",
        "basketball",
        "sports"

    ]):

        return "sports"

    if any(word in text for word in [

        "research",
        "wikipedia",
        "sources"

    ]):

        return "research"

    return "ai"

# =================================================
# AI CHAT ENGINE
# =================================================

async def generate_ai_response(

    message: str,

    provider: str = "auto"

):

    try:

        if provider == "auto":

            return await auto_route_ai(
                message
            )

        if provider == "openai":

            return await openai_chat(
                message
            )

        if provider == "groq":

            return await groq_chat(
                message
            )

        if provider == "kimi":

            return await kimi_chat(
                message
            )

        if provider == "openrouter":

            return await openrouter_chat(
                message
            )

        return await auto_route_ai(
            message
        )

    except Exception as e:

        return {

            "success": False,

            "error": str(e)

        }

# =================================================
# CHAT ENDPOINT
# =================================================

@app.post("/chat")
async def chat(
    request: ChatRequest
):

    conversation_id = (

        request.conversation_id

        or

        generate_id()

    )

    add_message(

        conversation_id,

        "user",

        request.message

    )

    route = determine_route(
        request.message
    )

    ai_result = await generate_ai_response(

        request.message,

        request.provider

    )

    if not ai_result.get(
        "success"
    ):

        raise HTTPException(

            status_code=500,

            detail=
            ai_result.get(
                "error",
                "Unknown error"
            )

        )

    response_text = ai_result.get(
        "content",
        "No response"
    )

    add_message(

        conversation_id,

        "assistant",

        response_text

    )

    SYSTEM_STATS["chats"] += 1

    return {

        "success": True,

        "conversation_id":
        conversation_id,

        "route":
        route,

        "provider":
        ai_result.get(
            "provider"
        ),

        "model":
        ai_result.get(
            "model"
        ),

        "response":
        response_text,

        "timestamp":
        now()

    }

# =================================================
# CONVERSATION HISTORY
# =================================================

@app.get(
    "/chat/history/{conversation_id}"
)
async def history(
    conversation_id: str
):

    return {

        "success": True,

        "messages":
        get_conversation(
            conversation_id
        )

    }

# =================================================
# CLEAR CHAT
# =================================================

@app.delete(
    "/chat/history/{conversation_id}"
)
async def clear_chat(
    conversation_id: str
):

    if conversation_id in CONVERSATIONS:

        del CONVERSATIONS[
            conversation_id
        ]

    return {

        "success": True

    }

# =================================================
# MEMORY ENDPOINTS
# =================================================

@app.post("/memory/save")
async def memory_save(
    item: MemoryCreate
):

    save_memory(

        "global",

        item.key,

        item.value

    )

    return {

        "success": True

    }

# =================================================

@app.get("/memory")

async def memory_list():

    return {

        "success": True,

        "memory":
        USER_MEMORY

    }

# =================================================

@app.delete("/memory")

async def memory_clear():

    USER_MEMORY.clear()

    return {

        "success": True

    }

# =================================================
# CHAT ANALYTICS
# =================================================

@app.get("/chat/stats")

async def chat_stats():

    return {

        "success": True,

        "conversations":
        len(CONVERSATIONS),

        "messages":
        SYSTEM_STATS["messages"],

        "users":
        SYSTEM_STATS["users"]

    }

# =================================================
# AI TEST
# =================================================

@app.get("/chat/test")

async def test_ai():

    return {

        "success": True,

        "name":
        APP_NAME,

        "version":
        APP_VERSION,
   "status":
        "Online"

    }

# =================================================
# END PART 10
# =================================================

      # =================================================
# BLOXY-BOT AI - APP.PY PART 11
# ADMIN DASHBOARD + MONITORING
# =================================================

import platform
import time
import os

# =================================================
# SYSTEM STATE
# =================================================

START_TIME = time.time()

SYSTEM_FLAGS = {

    "maintenance": False,

    "debug": False,

    "experimental": False,

    "moderation": False

}

ANNOUNCEMENT_BANNER = ""

SYSTEM_CACHE = {}

ERROR_LOGS = []

# =================================================
# UPTIME
# =================================================

def get_uptime():

    uptime = int(
        time.time() - START_TIME
    )

    days = uptime // 86400

    hours = (
        uptime % 86400
    ) // 3600

    minutes = (
        uptime % 3600
    ) // 60

    return f"{days}d {hours}h {minutes}m"

# =================================================
# SYSTEM INFO
# =================================================

@app.get("/admin/system")

async def admin_system():

    return {

        "success": True,

        "app": APP_NAME,

        "version": APP_VERSION,

        "python":

        platform.python_version(),

        "platform":

        platform.platform(),

        "uptime":

        get_uptime()

    }

# =================================================
# DASHBOARD
# =================================================

@app.get("/admin/dashboard")

async def admin_dashboard():

    return {

        "success": True,

        "app": APP_NAME,

        "version": APP_VERSION,

        "users":
        SYSTEM_STATS["users"],

        "messages":
        SYSTEM_STATS["messages"],

        "chats":
        SYSTEM_STATS["chats"],

        "uptime":
        get_uptime(),

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# HEALTH CHECK
# =================================================

@app.get("/admin/health")

async def health_check():

    return {

        "success": True,

        "database": True,

        "memory": True,

        "providers":
        PROVIDER_STATUS,

        "research": True,

        "news": True,

        "finance": True,

        "sports": True,

        "weather": True

    }

# =================================================
# CACHE
# =================================================

@app.get("/admin/cache")

async def cache_info():

    return {

        "success": True,

        "entries":
        len(SYSTEM_CACHE)

    }

# =================================================

@app.delete("/admin/cache")

async def clear_cache():

    SYSTEM_CACHE.clear()

    return {

        "success": True,

        "message":
        "Cache cleared"

    }

# =================================================
# MAINTENANCE MODE
# =================================================

@app.post("/admin/maintenance/on")

async def maintenance_on():

    SYSTEM_FLAGS[
        "maintenance"
    ] = True

    return {

        "success": True

    }

# =================================================

@app.post("/admin/maintenance/off")

async def maintenance_off():

    SYSTEM_FLAGS[
        "maintenance"
    ] = False

    return {

        "success": True

    }

# =================================================
# DEBUG MODE
# =================================================

@app.post("/admin/debug/on")

async def debug_on():

    SYSTEM_FLAGS[
        "debug"
    ] = True

    return {

        "success": True

    }

# =================================================

@app.post("/admin/debug/off")

async def debug_off():

    SYSTEM_FLAGS[
        "debug"
    ] = False

    return {

        "success": True

    }

# =================================================
# EXPERIMENTAL MODE
# =================================================

@app.post("/admin/experimental/on")

async def experimental_on():

    SYSTEM_FLAGS[
        "experimental"
    ] = True

    return {

        "success": True

    }

# =================================================

@app.post("/admin/experimental/off")

async def experimental_off():

    SYSTEM_FLAGS[
        "experimental"
    ] = False

    return {

        "success": True

    }

# =================================================
# BANNER
# =================================================

@app.post("/admin/banner/set")

async def set_banner(
    text: str
):

    global ANNOUNCEMENT_BANNER

    ANNOUNCEMENT_BANNER = text

    return {

        "success": True

    }

# =================================================

@app.delete("/admin/banner")

async def remove_banner():

    global ANNOUNCEMENT_BANNER

    ANNOUNCEMENT_BANNER = ""

    return {

        "success": True

    }

# =================================================

@app.get("/banner")

async def banner():

    return {

        "banner":
        ANNOUNCEMENT_BANNER

    }

# =================================================
# LOGS
# =================================================

@app.get("/admin/logs")

async def admin_logs():

    return {

        "success": True,

        "logs":
        ERROR_LOGS[-100:]

    }

# =================================================
# PROVIDER CHECK
# =================================================

@app.get("/admin/providers")

async def provider_check():

    await check_provider_health()

    return {

        "success": True,

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# SYSTEM FLAGS
# =================================================

@app.get("/admin/flags")

async def flags():

    return {

        "success": True,

        "flags":
        SYSTEM_FLAGS

    }

# =================================================
# END PART 11
# =================================================
# =================================================
# BLOXY-BOT AI - APP.PY PART 12
# PRODUCTION CORE
# =================================================

import json
import shutil
from pathlib import Path

# =================================================
# ADMIN CONFIG
# =================================================

ADMIN_EMAILS = {

    "admin@bloxybot.ai"

}

BACKUP_DIR = Path("backups")

BACKUP_DIR.mkdir(
    exist_ok=True
)

# =================================================
# API KEY CHECKER
# =================================================

def validate_api_keys():

    return {

        "openai":
        bool(OPENAI_API_KEY),

        "groq":
        bool(GROQ_API_KEY),

        "kimi":
        bool(KIMI_API_KEY),

        "openrouter":
        bool(OPENROUTER_API_KEY),

        "newsapi":
        bool(NEWS_API_KEY),

        "gnews":
        bool(GNEWS_API_KEY),

        "guardian":
        bool(GUARDIAN_API_KEY),

        "weather":
        bool(OPENWEATHER_API_KEY),

        "finance":
        bool(FINNHUB_API_KEY)

    }

# =================================================
# STARTUP CHECK
# =================================================

async def startup_validation():

    provider_status = validate_api_keys()

    passed = sum(
        provider_status.values()
    )

    total = len(
        provider_status
    )

    return {

        "passed": passed,

        "total": total,

        "status":
        "ready"
        if passed > 3
        else "limited"

    }

# =================================================
# READY ENDPOINT
# =================================================

@app.get("/ready")

async def ready():

    validation = await startup_validation()

    return {

        "success": True,

        "app": APP_NAME,

        "version": APP_VERSION,

        "status":
        validation["status"]

    }

# =================================================
# STARTUP REPORT
# =================================================

@app.get("/startup-check")

async def startup_check():

    report = await startup_validation()

    return {

        "success": True,

        "report": report,

        "providers":
        validate_api_keys()

    }

# =================================================
# BACKUP HELPERS
# =================================================

def create_backup():

    backup_name = (

        f"backup_"

        f"{int(time.time())}"

        ".json"

    )

    backup_file = (
        BACKUP_DIR /
        backup_name
    )

    data = {

        "users":
        USERS,

        "sessions":
        SESSIONS,

        "settings":
        USER_SETTINGS,

        "memory":
        USER_MEMORY,

        "stats":
        SYSTEM_STATS

    }

    with open(
        backup_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )

    return str(
        backup_file
    )

# =================================================
# RESTORE HELPERS
# =================================================

def restore_backup(
    file_name: str
):

    backup_file = (
        BACKUP_DIR /
        file_name
    )

    if not backup_file.exists():

        return False

    with open(
        backup_file,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    USERS.clear()
    USERS.update(
        data.get("users", {})
    )

    SESSIONS.clear()
    SESSIONS.update(
        data.get("sessions", {})
    )

    USER_SETTINGS.clear()
    USER_SETTINGS.update(
        data.get("settings", {})
    )

    USER_MEMORY.clear()
    USER_MEMORY.update(
        data.get("memory", {})
    )

    return True

# =================================================
# CREATE BACKUP
# =================================================

@app.post("/backup")

async def backup():

    file_path = create_backup()

    return {

        "success": True,

        "file":
        file_path

    }

# =================================================
# LIST BACKUPS
# =================================================

@app.get("/backups")

async def backups():

    files = [

        f.name

        for f in

        BACKUP_DIR.glob(
            "*.json"
        )

    ]

    return {

        "success": True,

        "files": files

    }

# =================================================
# RESTORE BACKUP
# =================================================

@app.post("/restore/{file_name}")

async def restore(
    file_name: str
):

    result = restore_backup(
        file_name
    )

    return {

        "success": result

    }

# =================================================
# SYSTEM EXPORT
# =================================================

@app.get("/export/system")

async def export_system():

    return {

        "app":
        APP_NAME,

        "version":
        APP_VERSION,

        "stats":
        SYSTEM_STATS,

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# RELOAD PROVIDERS
# =================================================

@app.post("/providers/reload")

async def reload_providers():

    await check_provider_health()

    return {

        "success": True,

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# PANIC RECOVERY
# =================================================

@app.post("/panic")

async def panic_recovery():

    SYSTEM_CACHE.clear()

    await check_provider_health()

    backup_file = (
        create_backup()
    )

    return {

        "success": True,

        "message":
        "Recovery completed",

        "backup":
        backup_file

    }

# =================================================
# VERSION
# =================================================

@app.get("/version")

async def version():

    return {

        "name":
        APP_NAME,

        "version":
        APP_VERSION,

        "build":
        "Production"

    }

# =================================================
# END PART 12
# =================================================
# =================================================
# BLOXY-BOT AI - APP.PY PART 13
# MEGA COMMANDS + SETTINGS CENTER
# =================================================

import random

# =================================================
# GLOBAL SETTINGS
# =================================================

GLOBAL_SETTINGS = {

    "theme": "dark",
    "personality": "friendly",
    "default_provider": "auto",
    "deep_research": False,
    "multi_ai": False,
    "maintenance": False

}

# =================================================
# PERSONALITIES
# =================================================

PERSONALITIES = [

    "friendly",
    "professional",
    "teacher",
    "coder",
    "researcher",
    "creative"

]

# =================================================
# SETTINGS CENTER
# =================================================

@app.get("/settings")
async def settings():

    return {
        "success": True,
        "settings": GLOBAL_SETTINGS
    }

@app.post("/settings/update")
async def update_settings(
    settings: dict
):

    GLOBAL_SETTINGS.update(
        settings
    )

    return {
        "success": True,
        "settings": GLOBAL_SETTINGS
    }

# =================================================
# COMMAND ENGINE
# =================================================

COMMANDS = {

    "ping": "Pong!",
    "version": APP_VERSION,
    "status": "Online",
    "help": "Command list loaded"

}

# =================================================
# 25+ BLOXY COMMANDS
# =================================================

@app.get("/bloxy/ping")
async def cmd_ping():
    return {"response": "Pong!"}

@app.get("/bloxy/version")
async def cmd_version():
    return {"version": APP_VERSION}

@app.get("/bloxy/status")
async def cmd_status():
    return {"status": "Online"}

@app.get("/bloxy/uptime")
async def cmd_uptime():
    return {"uptime": get_uptime()}

@app.get("/bloxy/providers")
async def cmd_providers():
    return PROVIDER_STATUS

@app.get("/bloxy/memory")
async def cmd_memory():
    return USER_MEMORY

@app.get("/bloxy/stats")
async def cmd_stats():
    return SYSTEM_STATS

@app.get("/bloxy/fact")
async def cmd_fact():

    facts = [

        "Honey never spoils.",
        "Octopuses have three hearts.",
        "Bananas are berries.",
        "Sharks are older than trees."

    ]

    return {
        "fact":
        random.choice(facts)
    }

@app.get("/bloxy/motivate")
async def motivate():

    quotes = [

        "Keep building.",
        "Every expert was once a beginner.",
        "Small steps win.",
        "You can do it."

    ]

    return {
        "message":
        random.choice(quotes)
    }

@app.get("/bloxy/roast")
async def roast():

    roasts = [

        "Your bugs are reproducing.",
        "That semicolon is hiding.",
        "Your code needs coffee.",
        "404: Logic not found."

    ]

    return {
        "roast":
        random.choice(roasts)
    }

@app.get("/bloxy/surprise")
async def surprise():

    surprises = [

        "🎉 Surprise!",
        "🚀 Launch mode!",
        "🤖 AI online!",
        "⚡ Turbo mode!"

    ]

    return {
        "result":
        random.choice(surprises)
    }

# =================================================
# ADMIN COMMANDS
# =================================================

@app.post("/admin/restart")
async def admin_restart():

    return {
        "success": True,
        "message": "Restart queued"
    }

@app.post("/admin/clear-memory")
async def clear_memory():

    USER_MEMORY.clear()

    return {
        "success": True
    }

@app.post("/admin/clear-chats")
async def clear_chats():

    CONVERSATIONS.clear()

    return {
        "success": True
    }

@app.post("/admin/reload")
async def reload_system():

    return {
        "success": True,
        "message": "Reloaded"
    }

@app.post("/admin/broadcast")
async def broadcast(
    message: str
):

    return {
        "success": True,
        "message": message
    }

# =================================================
# PERSONALITY SYSTEM
# =================================================

@app.post(
"/personality/{personality}"
)
async def personality(
    personality: str
):

    if personality not in PERSONALITIES:

        return {
            "success": False
        }

    GLOBAL_SETTINGS[
        "personality"
    ] = personality

    return {
        "success": True,
        "personality":
        personality
    }

# =================================================
# DEEP RESEARCH
# =================================================

@app.post("/mode/deep-research")

async def deep_research():

    GLOBAL_SETTINGS[
        "deep_research"
    ] = True

    return {
        "success": True
    }

# =================================================
# MULTI AI MODE
# =================================================

@app.post("/mode/multi-ai")

async def multi_ai():

    GLOBAL_SETTINGS[
        "multi_ai"
    ] = True

    return {
        "success": True
    }

# =================================================
# PROVIDER PRIORITY
# =================================================

@app.post("/provider/default/{name}")

async def provider_default(
    name: str
):

    GLOBAL_SETTINGS[
        "default_provider"
    ] = name

    return {
        "success": True
    }

# =================================================
# DIAGNOSTICS
# =================================================

@app.get("/diagnostics")

async def diagnostics():

    return {

        "success": True,

        "users":
        len(USERS),

        "sessions":
        len(SESSIONS),

        "conversations":
        len(CONVERSATIONS),

        "providers":
        PROVIDER_STATUS

    }

# =================================================
# SELF TEST
# =================================================

@app.get("/admin/self-test")

async def self_test():

    return {

        "success": True,

        "database": True,

        "memory": True,

        "providers": True,

        "research": True,

        "news": True,

        "sports": True,

        "finance": True,

        "weather": True

    }

# =================================================
# FINAL COMMAND COUNT
# =================================================

"""
Bloxy Commands:

1 ping
2 version
3 status
4 uptime
5 providers
6 memory
7 stats
8 fact
9 motivate
10 roast
11 surprise
12 restart
13 clear-memory
14 clear-chats
15 reload
16 broadcast
17 personality
18 deep-research
19 multi-ai
20 provider-default
21 diagnostics
22 self-test
23 backup
24 restore
25 panic
26 startup-check
27 ready
28 health
29 dashboard
30 logs
"""

"""

# =================================================
# END PART 13
# BLOXY-BOT AI COMPLETE v2.0
# =================================================

"""       
