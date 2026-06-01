# =========================================================
# BLOXY-BOT X (PART 1)
# Imports + Config + Database + Models
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import hashlib
import requests
import json
import os
import time
import uuid
import uvicorn

app = FastAPI(title="Bloxy-Bot X")

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
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

SECRET_KEY = os.getenv("SECRET_KEY", "")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "bloxybot.db",
    check_same_thread=False
)

cur = conn.cursor()

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

cur.execute("""
CREATE TABLE IF NOT EXISTS conversations(
id INTEGER PRIMARY KEY AUTOINCREMENT,
conversation_id TEXT,
email TEXT,
title TEXT,
pinned INTEGER DEFAULT 0,
messages TEXT,
updated_at TEXT
)
""")

conn.commit()

# =========================================================
# REQUEST MODELS
# =========================================================

class Register(BaseModel):
    email: str
    username: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class Chat(BaseModel):
    email: str
    conversation_id: str
    message: str

# =========================================================
# HELPERS
# =========================================================

def hash_password(password: str):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# ===== END PART 1 =====

# =========================================================
# BLOXY-BOT X (PART 2)
# Authentication + Conversations
# =========================================================

class ConversationAction(BaseModel):
    email: str
    conversation_id: str

class RenameConversation(BaseModel):
    email: str
    conversation_id: str
    new_title: str

# =========================================================
# AUTH
# =========================================================

@app.post("/register")
def register(data: Register):

    try:

        cur.execute(
            """
            INSERT INTO users(
            email,
            username,
            password,
            created_at
            )
            VALUES(?,?,?,?)
            """,
            (
                data.email,
                data.username,
                hash_password(data.password),
                str(time.time())
            )
        )

        conversation_id = str(uuid.uuid4())

        cur.execute(
            """
            INSERT INTO conversations(
            conversation_id,
            email,
            title,
            messages,
            updated_at
            )
            VALUES(?,?,?,?,?)
            """,
            (
                conversation_id,
                data.email,
                "New Chat",
                "[]",
                str(time.time())
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
            "error": str(e)
        }


@app.post("/login")
def login(data: Login):

    cur.execute(
        """
        SELECT username
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
            "success": False
        }

    return {
        "success": True,
        "username": user[0]
    }

# =========================================================
# CONVERSATIONS
# =========================================================

@app.get("/conversations/{email}")
def conversations(email: str):

    cur.execute(
        """
        SELECT
        conversation_id,
        title,
        pinned
        FROM conversations
        WHERE email=?
        ORDER BY pinned DESC,
        updated_at DESC
        """,
        (email,)
    )

    rows = cur.fetchall()

    return {
        "conversations": [
            {
                "conversation_id": r[0],
                "title": r[1],
                "pinned": bool(r[2])
            }
            for r in rows
        ]
    }


@app.post("/new-chat")
def new_chat(data: ConversationAction):

    conversation_id = str(uuid.uuid4())

    cur.execute(
        """
        INSERT INTO conversations(
        conversation_id,
        email,
        title,
        messages,
        updated_at
        )
        VALUES(?,?,?,?,?)
        """,
        (
            conversation_id,
            data.email,
            "New Chat",
            "[]",
            str(time.time())
        )
    )

    conn.commit()

    return {
        "success": True,
        "conversation_id": conversation_id
    }


@app.post("/rename-chat")
def rename_chat(data: RenameConversation):

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

    return {"success": True}


@app.post("/pin-chat")
def pin_chat(data: ConversationAction):

    cur.execute(
        """
        UPDATE conversations
        SET pinned=1
        WHERE conversation_id=?
        """,
        (data.conversation_id,)
    )

    conn.commit()

    return {"success": True}


@app.post("/delete-chat")
def delete_chat(data: ConversationAction):

    cur.execute(
        """
        DELETE FROM conversations
        WHERE conversation_id=?
        """,
        (data.conversation_id,)
    )

    conn.commit()

    return {"success": True}

# ===== END PART 2 =====

# =========================================================
# BLOXY-BOT X (PART 3)
# AI + Search + Chat Engine
# =========================================================

MODELS = [
    "openai",
    "openrouter",
    "groq",
    "kimi"
]

def tavily_search(query):

    if not TAVILY_API_KEY:
        return ""

    try:

        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 5
            },
            timeout=20
        )

        data = r.json()

        return "\n".join([
            x.get("content", "")
            for x in data.get("results", [])
        ])

    except:
        return ""


def ai_reply(message, history):

    live_data = tavily_search(message)

    system_prompt = f"""
You are Bloxy-Bot X.

Use:
- Clean formatting
- Bullet points
- Concise answers
- Real-time information when available

Live Data:
{live_data}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": message
    })

    # OpenRouter fallback chain

    models = [
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct",
        "deepseek/deepseek-chat"
    ]

    for model in models:

        try:

            r = requests.post(
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
                    "max_tokens": 1000
                },
                timeout=45
            )

            data = r.json()

            return (
                data["choices"][0]
                ["message"]["content"]
            )

        except:
            continue

    return "⚠️ No AI provider responded."


@app.post("/chat")
def chat(data: Chat):

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
                history = json.loads(row[0])
            except:
                history = []

    reply = ai_reply(
        data.message,
        history[-20:]
    )

    if data.email != "guest":

        history.append({
            "role": "user",
            "content": data.message
        })

        history.append({
            "role": "assistant",
            "content": reply
        })

        cur.execute(
            """
            UPDATE conversations
            SET messages=?,
            updated_at=?
            WHERE conversation_id=?
            """,
            (
                json.dumps(history),
                str(time.time()),
                data.conversation_id
            )
        )

        conn.commit()

    return {
        "reply": reply
    }

# ===== END PART 3 =====

# =========================================================
# BLOXY-BOT X (PART 4)
# News + Sports + Weather + Finance APIs
# =========================================================

@app.get("/news")
def get_news(query: str):

    if not NEWS_API_KEY:
        return {"articles": []}

    try:

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "pageSize": 10,
                "language": "en",
                "apiKey": NEWS_API_KEY
            },
            timeout=20
        )

        return r.json()

    except:
        return {"articles": []}


@app.get("/weather")
def weather(city: str):

    try:

        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=20
        )

        return r.json()

    except:
        return {"error": "Weather unavailable"}


@app.get("/finance")
def finance(symbol: str):

    try:

        r = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": ALPHAVANTAGE_API_KEY
            },
            timeout=20
        )

        return r.json()

    # =========================================================
# BLOXY-BOT X (PART 5)
# UI + Startup
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>Bloxy-Bot X</title>

<style>
body{
    margin:0;
    background:#0b0b0b;
    color:white;
    font-family:Arial;
}

.sidebar{
    width:300px;
    position:fixed;
    left:0;
    top:0;
    bottom:0;
    background:#111;
    overflow:auto;
}

.main{
    margin-left:300px;
    height:100vh;
    display:flex;
    flex-direction:column;
}

.messages{
    flex:1;
    overflow:auto;
    padding:20px;
}

.message{
    padding:15px;
    border-radius:12px;
    margin-bottom:12px;
}

.user{background:#1f1f1f;}
.bot{
    background:#181818;
    border-left:4px solid orange;
}

.inputbar{
    display:flex;
    padding:15px;
    gap:10px;
}

textarea{
    flex:1;
    height:70px;
    background:#1c1c1c;
    color:white;
    border:none;
    border-radius:12px;
    padding:12px;
}

button{
    background:orange;
    border:none;
    color:white;
    padding:12px 20px;
    border-radius:12px;
    cursor:pointer;
}
</style>
</head>

<body>

<div class="sidebar">
<h2 style="padding:20px;">🤖 Bloxy-Bot X</h2>
<button onclick="newChat()">New Chat</button>
<div id="conversations"></div>
</div>

<div class="main">

<div id="messages" class="messages"></div>

<div class="inputbar">
<textarea id="msg"></textarea>
<button onclick="sendMessage()">Send</button>
</div>

</div>

<script>

let EMAIL="guest";
let CONVERSATION="";

async function sendMessage(){

    let msg=document.getElementById("msg").value;

    if(!msg) return;

    let box=document.getElementById("messages");

    box.innerHTML+=
    `<div class="message user">${msg}</div>`;

    document.getElementById("msg").value="";

    let r=await fetch("/chat",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            email:EMAIL,
            conversation_id:CONVERSATION,
            message:msg
        })
    });

    let d=await r.json();

    box.innerHTML+=
    `<div class="message bot">${d.reply}</div>`;

    box.scrollTop=box.scrollHeight;
}

document.getElementById("msg")
.addEventListener("keydown",function(e){

    if(e.ctrlKey && e.key==="Enter"){
        e.preventDefault();
        sendMessage();
    }
});

</script>

</body>
</html>
"""

# =========================================================
# STARTUP
# =========================================================

@app.get("/health")
def health():
    return {
        "status":"online",
        "app":"Bloxy-Bot X"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )

# =========================================================
# END PART 5
# =========================================================

    except:
        return {"error": "Finance unavailable"}


@app.get("/sports/epl")
def epl_table():

    try:

        r = requests.get(
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

        return r.json()

    except:
        return {"error": "Sports unavailable"}


@app.get("/movies")
def movies(query: str):

    try:

        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": query
            },
            timeout=20
        )

        return r.json()

    except:
        return {"results": []}


@app.get("/wolfram")
def wolfram(question: str):

    try:

        r = requests.get(
            "https://api.wolframalpha.com/v2/query",
            params={
                "appid": WOLFRAM_APP_ID,
                "input": question,
                "output": "json"
            },
            timeout=30
        )

        return r.json()

    except:
        return {"error": "Wolfram unavailable"}

# ===== END PART 4 =====
# PART 5 = Full UI + Startup + Final Merge
