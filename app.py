# =========================================================
# BLOXY-BOT X (PART 1)
# Imports + Config + FastAPI + Database + Models
# Syntax-Safe Version
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

import os
import json
import time
import uuid
import sqlite3
import hashlib
import requests

# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Bloxy-Bot X",
    version="2.0.0"
)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY", "")

APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY", "")

SECRET_KEY = os.getenv("SECRET_KEY", "bloxy-secret")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "bloxybot.db",
    check_same_thread=False
)

cur = conn.cursor()

# =========================================================
# USERS
# =========================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    username TEXT,
    password TEXT,
    verified INTEGER DEFAULT 0,
    created_at TEXT
)
""")

# =========================================================
# CONVERSATIONS
# =========================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT UNIQUE,
    email TEXT,
    title TEXT,
    pinned INTEGER DEFAULT 0,
    messages TEXT,
    updated_at TEXT
)
""")

# =========================================================
# DRAFTS
# =========================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS drafts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    draft TEXT
)
""")

# =========================================================
# SETTINGS
# =========================================================

cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    theme TEXT DEFAULT 'dark',
    model TEXT DEFAULT 'auto'
)
""")

conn.commit()

# =========================================================
# HELPERS
# =========================================================

def now() -> str:
    return str(time.time())


def generate_id() -> str:
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# PYDANTIC MODELS
# =========================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChatRequest(BaseModel):
    email: str
    conversation_id: str
    message: str


class ConversationRequest(BaseModel):
    email: str
    conversation_id: str


class RenameRequest(BaseModel):
    email: str
    conversation_id: str
    new_title: str


# =========================================================
# ROOT HEALTH CHECK
# =========================================================

@app.get("/api-status")
def api_status():
    return {
        "status": "online",
        "service": "Bloxy-Bot X",
        "version": "2.0.0"
    }

# =========================================================
# END PART 1
# =========================================================


# =========================================================
# BLOXY-BOT X (PART 2)
# Authentication + Conversation Management
# =========================================================

@app.post("/register")
def register(data: RegisterRequest):
    try:
        cur.execute(
            """
            INSERT INTO users(
                email,
                username,
                password,
                verified,
                created_at
            )
            VALUES(?,?,?,?,?)
            """,
            (
                data.email,
                data.username,
                hash_password(data.password),
                0,
                now()
            )
        )

        conversation_id = generate_id()

        cur.execute(
            """
            INSERT INTO conversations(
                conversation_id,
                email,
                title,
                pinned,
                messages,
                updated_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                conversation_id,
                data.email,
                "New Chat",
                0,
                "[]",
                now()
            )
        )

        conn.commit()

        return {
            "success": True,
            "conversation_id": conversation_id
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@app.post("/login")
def login(data: LoginRequest):

    cur.execute(
        """
        SELECT username, verified
        FROM users
        WHERE email=? AND password=?
        """,
        (
            data.email,
            hash_password(data.password)
        )
    )

    user = cur.fetchone()

    if not user:
        return {
            "success": False,
            "message": "Invalid credentials"
        }

    return {
        "success": True,
        "username": user[0],
        "verified": bool(user[1])
    }


@app.get("/conversations/{email}")
def get_conversations(email: str):

    cur.execute(
        """
        SELECT
            conversation_id,
            title,
            pinned,
            updated_at
        FROM conversations
        WHERE email=?
        ORDER BY pinned DESC,
                 updated_at DESC
        """,
        (email,)
    )

    rows = cur.fetchall()

    conversations = []

    for row in rows:
        conversations.append(
            {
                "conversation_id": row[0],
                "title": row[1],
                "pinned": bool(row[2]),
                "updated_at": row[3]
            }
        )

    return {
        "success": True,
        "conversations": conversations
    }


@app.post("/new-chat")
def new_chat(data: ConversationRequest):

    conversation_id = generate_id()

    cur.execute(
        """
        INSERT INTO conversations(
            conversation_id,
            email,
            title,
            pinned,
            messages,
            updated_at
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            conversation_id,
            data.email,
            "New Chat",
            0,
            "[]",
            now()
        )
    )

    conn.commit()

    return {
        "success": True,
        "conversation_id": conversation_id
    }


@app.post("/rename-chat")
def rename_chat(data: RenameRequest):

    cur.execute(
        """
        UPDATE conversations
        SET title=?
        WHERE conversation_id=?
        """,
        (
            data.new_title,
            data.conversation_id
        )
    )

    conn.commit()

    return {
        "success": True
    }


@app.post("/pin-chat")
def pin_chat(data: ConversationRequest):

    cur.execute(
        """
        UPDATE conversations
        SET pinned=1
        WHERE conversation_id=?
        """,
        (data.conversation_id,)
    )

    conn.commit()

    return {
        "success": True
    }


@app.post("/unpin-chat")
def unpin_chat(data: ConversationRequest):

    cur.execute(
        """
        UPDATE conversations
        SET pinned=0
        WHERE conversation_id=?
        """,
        (data.conversation_id,)
    )

    conn.commit()

    return {
        "success": True
    }


@app.post("/delete-chat")
def delete_chat(data: ConversationRequest):

    cur.execute(
        """
        DELETE FROM conversations
        WHERE conversation_id=?
        """,
        (data.conversation_id,)
    )

    conn.commit()

    return {
        "success": True
    }


@app.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: str):

    cur.execute(
        """
        SELECT messages
        FROM conversations
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    row = cur.fetchone()

    if not row:
        return {
            "success": False,
            "messages": []
        }

    try:
        messages = json.loads(row[0])
    except Exception:
        messages = []

    return {
        "success": True,
        "messages": messages
    }

# =========================================================
# END PART 2
# =========================================================


# =========================================================
# BLOXY-BOT X (PART 3)
# AI Engine + Search + Chat Logic
# =========================================================

MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat",
    "mistralai/mistral-small-3.2-24b-instruct"
]


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {}


def tavily_search(query: str) -> str:

    if not TAVILY_API_KEY:
        return ""

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5
            },
            timeout=20
        )

        data = safe_json(response)

        results = []

        for item in data.get("results", []):
            content = item.get("content", "")
            if content:
                results.append(content)

        return "\n".join(results)

    except Exception:
        return ""


def news_context(query: str) -> str:

    if not NEWS_API_KEY:
        return ""

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "pageSize": 5,
                "language": "en",
                "apiKey": NEWS_API_KEY
            },
            timeout=20
        )

        data = safe_json(response)

        headlines = []

        for article in data.get("articles", []):
            title = article.get("title", "")
            if title:
                headlines.append(title)

        return "\n".join(headlines)

    except Exception:
        return ""


def build_system_prompt(
    search_data: str,
    news_data: str
) -> str:

    return f"""
You are Bloxy-Bot X.

Rules:
- Be helpful.
- Be accurate.
- Use bullet points when useful.
- Keep formatting clean.
- Explain technical topics clearly.

SEARCH DATA:
{search_data}

NEWS DATA:
{news_data}
"""


def format_response(text: str) -> str:

    if not text:
        return "No response generated."

    cleaned = []

    for line in text.split("\n"):
        line = line.strip()

        if line:
            cleaned.append(line)

    return "\n".join(cleaned)


def call_openrouter(
    model: str,
    messages: list
):

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type":
            "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200
        },
        timeout=90
    )

    data = safe_json(response)

    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )


def ai_reply(
    user_message: str,
    history: list
) -> str:

    search_data = tavily_search(
        user_message
    )

    news_data = news_context(
        user_message
    )

    system_prompt = build_system_prompt(
        search_data,
        news_data
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    for model in MODELS:

        try:

            reply = call_openrouter(
                model,
                messages
            )

            if reply:
                return format_response(
                    reply
                )

        except Exception:
            continue

    return "All configured AI providers failed."


@app.post("/chat")
def chat(data: ChatRequest):

    history = []

    if data.email != "guest":

        cur.execute(
            """
            SELECT messages
            FROM conversations
            WHERE conversation_id=?
            """,
            (data.conversation_id,)
        )

        row = cur.fetchone()

        if row:

            try:
                history = json.loads(
                    row[0]
                )
            except Exception:
                history = []

    reply = ai_reply(
        data.message,
        history[-20:]
    )

    if data.email != "guest":

        history.append(
            {
                "role": "user",
                "content": data.message
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        cur.execute(
            """
            UPDATE conversations
            SET messages=?,
                updated_at=?
            WHERE conversation_id=?
            """,
            (
                json.dumps(history),
                now(),
                data.conversation_id
            )
        )

        conn.commit()

    return {
        "success": True,
        "reply": reply
    }


# =========================================================
# END PART 3
# =========================================================


# =========================================================
# BLOXY-BOT X (PART 4)
# News + Weather + Finance + Movies + Sports + Wolfram
# =========================================================

@app.get("/news")
def get_news(query: str):

    if not NEWS_API_KEY:
        return {
            "success": False,
            "message": "NEWS_API_KEY missing",
            "articles": []
        }

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "pageSize": 10,
                "sortBy": "publishedAt",
                "apiKey": NEWS_API_KEY
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/weather")
def weather(city: str):

    if not OPENWEATHER_API_KEY:
        return {
            "success": False,
            "message": "OPENWEATHER_API_KEY missing"
        }

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/finance")
def finance(symbol: str):

    if not ALPHAVANTAGE_API_KEY:
        return {
            "success": False,
            "message": "ALPHAVANTAGE_API_KEY missing"
        }

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": ALPHAVANTAGE_API_KEY
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/finnhub")
def finnhub_quote(symbol: str):

    if not FINNHUB_API_KEY:
        return {
            "success": False,
            "message": "FINNHUB_API_KEY missing"
        }

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={
                "symbol": symbol,
                "token": FINNHUB_API_KEY
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/exchange-rate")
def exchange_rate(base: str):

    if not EXCHANGERATE_API_KEY:
        return {
            "success": False,
            "message": "EXCHANGERATE_API_KEY missing"
        }

    try:
        response = requests.get(
            f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{base}",
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/movies")
def search_movies(query: str):

    if not TMDB_API_KEY:
        return {
            "success": False,
            "message": "TMDB_API_KEY missing"
        }

    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": query
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/sports/epl")
def epl_standings():

    if not APISPORTS_API_KEY:
        return {
            "success": False,
            "message": "APISPORTS_API_KEY missing"
        }

    try:
        response = requests.get(
            "https://v3.football.api-sports.io/standings",
            headers={
                "x-apisports-key":
                APISPORTS_API_KEY
            },
            params={
                "league": 39,
                "season": 2025
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/odds")
def sports_odds(
    sport: str = "soccer_epl"
):

    if not ODDS_API_KEY:
        return {
            "success": False,
            "message": "ODDS_API_KEY missing"
        }

    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
            params={
                "apiKey": ODDS_API_KEY
            },
            timeout=20
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/wolfram")
def wolfram(question: str):

    if not WOLFRAM_APP_ID:
        return {
            "success": False,
            "message": "WOLFRAM_APP_ID missing"
        }

    try:
        response = requests.get(
            "https://api.wolframalpha.com/v2/query",
            params={
                "appid": WOLFRAM_APP_ID,
                "input": question,
                "output": "json"
            },
            timeout=30
        )

        return response.json()

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/system-info")
def system_info():

    return {
        "app": "Bloxy-Bot X",
        "version": "2.0.0",
        "database": "SQLite",
        "openrouter_enabled": bool(OPENROUTER_API_KEY),
        "news_enabled": bool(NEWS_API_KEY),
        "weather_enabled": bool(OPENWEATHER_API_KEY),
        "finance_enabled": bool(ALPHAVANTAGE_API_KEY),
        "movies_enabled": bool(TMDB_API_KEY),
        "wolfram_enabled": bool(WOLFRAM_APP_ID)
    }

# =========================================================
# END PART 4
# =========================================================


# =========================================================
# PART 5A + 5B + 5C
# =========================================================


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Bloxy-Bot X</title>

<style>
body{
    font-family:Arial,sans-serif;
    background:#0f172a;
    color:white;
    margin:0;
}

.container{
    padding:20px;
}

textarea{
    width:100%;
    height:120px;
}

button{
    padding:10px 20px;
}
</style>

</head>

<body>

<div class="container">
    <h1>Bloxy-Bot X</h1>

    <textarea id="messageInput"></textarea>

    <br><br>

    <button onclick="sendMessage()">
        Send
    </button>

    <div id="messages"></div>
</div>

<script>

async function sendMessage(){

    const text =
        document.getElementById(
            "messageInput"
        ).value;

    const response =
        await fetch(
            "/chat",
            {
                method:"POST",
                headers:{
                    "Content-Type":
                    "application/json"
                },
                body:JSON.stringify({
                    email:"guest",
                    conversation_id:"guest",
                    message:text
                })
            }
        );

    const data =
        await response.json();

    document.getElementById(
        "messages"
    ).innerHTML +=
    "<p>" +
    data.reply +
    "</p>";
}

</script>

</body>
</html>
"""

@app.get("/ping")
def ping():
    return {"message":"pong"}

@app.on_event("startup")
def startup_event():
    print("Bloxy-Bot X Starting...")

@app.on_event("shutdown")
def shutdown_event():
    print("Bloxy-Bot X Shutdown")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000
    )
