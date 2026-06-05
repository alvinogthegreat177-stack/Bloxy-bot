from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
import hashlib
from datetime import datetime

app = FastAPI(
    title="Bloxy-Bot X",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_NAME = "bloxybotx.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tables()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/")
def root():
    return {
        "app": "Bloxy-Bot X",
        "status": "online"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


import secrets
from fastapi.responses import JSONResponse

def get_user_by_email(email):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cur.fetchone()
    conn.close()
    return user

def create_session(user_id):
    token = secrets.token_hex(32)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sessions VALUES(?,?,?)",
        (
            token,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return token

@app.post("/api/register")
def register(data: RegisterRequest):

    if get_user_by_email(data.email):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Email already exists"
            }
        )

    user_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users VALUES(?,?,?,?,?)",
        (
            user_id,
            data.username,
            data.email,
            hash_password(data.password),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "user_id": user_id
    }

@app.post("/api/login")
def login(data: LoginRequest):

    user = get_user_by_email(data.email)

    if not user:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    if user["password"] != hash_password(data.password):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    token = create_session(user["id"])

    return {
        "success": True,
        "token": token,
        "user_id": user["id"],
        "username": user["username"]
    }

@app.post("/api/guest")
def guest_login():
    return {
        "success": True,
        "guest": True,
        "user_id": generate_id(),
        "username": "Guest"
    }

@app.delete("/api/logout/{token}")
def logout(token: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM sessions WHERE token=?",
        (token,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

@app.get("/api/user/{user_id}")
def get_user(user_id: str):

    user = get_user_by_id(user_id)

    if not user:
        return {
            "success": False
        }

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }


# =========================================================
# PART 3
# CONVERSATIONS + MESSAGES
# =========================================================

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str

class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str

def create_conversation_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_conversation_tables()


# =========================================================
# PART 4
# CONVERSATION ROUTES
# =========================================================

@app.post("/api/conversations/create")
def create_conversation(data: CreateConversationRequest):
    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO conversations VALUES(?,?,?,?,?)",
        (
            conversation_id,
            data.user_id,
            data.title,
            now(),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "conversation_id": conversation_id
    }


@app.get("/api/conversations/{user_id}")
def get_conversations(user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC",
        (user_id,)
    )

    data = [dict(row) for row in cur.fetchall()]

    conn.close()

    return {
        "success": True,
        "conversations": data
    }


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM messages WHERE conversation_id=?",
        (conversation_id,)
    )

    cur.execute(
        "DELETE FROM conversations WHERE id=?",
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {"success": True}


# =========================================================
# PART 5 (A-D)
# FRONTEND UI
# PASTE BELOW PART 4
# =========================================================

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>Bloxy-Bot X</title>

<style>
body{
    margin:0;
    font-family:Arial,sans-serif;
    background:#0f1117;
    color:white;
    height:100vh;
}

.app{
    display:flex;
    height:100vh;
}

.sidebar{
    width:250px;
    background:#171923;
    padding:20px;
}

.main{
    flex:1;
    display:flex;
    flex-direction:column;
}

.chat{
    flex:1;
    padding:20px;
    overflow-y:auto;
}

.input-area{
    padding:20px;
    border-top:1px solid #333;
}

input{
    width:100%;
    padding:12px;
}
</style>
</head>

<body>

<div class="app">

    <div class="sidebar">
        <h2>🤖 Bloxy-Bot X</h2>

        <button onclick="newChat()">
            New Chat
        </button>

        <button onclick="openSettings()">
            Settings
        </button>
    </div>

    <div class="main">

        <div id="chat" class="chat">
            <p>👋 Welcome to Bloxy-Bot X</p>
        </div>

        <div class="input-area">
            <input
                id="message"
                placeholder="Type a message..."
            >
        </div>

    </div>

</div>

<div
    id="settings"
    style="
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.7);
    "
>
    <div
        style="
        background:#171923;
        width:400px;
        margin:80px auto;
        padding:20px;
        "
    >
        <h2>Settings</h2>

        <button onclick="darkTheme()">
            Dark
        </button>

        <button onclick="lightTheme()">
            Light
        </button>

        <button onclick="closeSettings()">
            Close
        </button>
    </div>
</div>

<script>

function newChat(){
    document.getElementById("chat").innerHTML =
    "<p>✨ New conversation started</p>";
}

function openSettings(){
    document.getElementById("settings").style.display="block";
}

function closeSettings(){
    document.getElementById("settings").style.display="none";
}

function darkTheme(){
    document.body.style.background="#0f1117";
    document.body.style.color="white";
}

function lightTheme(){
    document.body.style.background="white";
    document.body.style.color="black";
}

document
.getElementById("message")
.addEventListener("keypress", function(e){

    if(e.key !== "Enter"){
        return;
    }

    const text = this.value.trim();

    if(!text){
        return;
    }

    const chat =
    document.getElementById("chat");

    chat.innerHTML +=
    "<p><b>You:</b> " + text + "</p>";

    this.value = "";

    setTimeout(() => {

        chat.innerHTML +=
        "<p><b>Bot:</b> " + text + "</p>";

        chat.scrollTop =
        chat.scrollHeight;

    }, 300);

});

</script>

</body>
</html>
"""


# =========================================================
# PART 6A
# USER SETTINGS DATABASE
# Paste below Part 5
# =========================================================

class UserSettings(BaseModel):
    user_id: str
    theme: str = "dark"
    ai_model: str = "gpt"
    temperature: float = 0.7
    system_prompt: str = ""
    chat_memory: bool = True

def create_settings_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        ai_model TEXT,
        temperature REAL,
        system_prompt TEXT,
        chat_memory INTEGER,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_settings_table()


# =========================================================
# PART 6B
# THEME MANAGEMENT
# Paste directly below Part 6A
# =========================================================

@app.get("/api/themes")
def get_themes():

    return {
        "success": True,
        "themes": [
            "dark",
            "light",
            "midnight",
            "ocean",
            "emerald",
            "purple",
            "crimson",
            "sunset"
        ]
    }

@app.get("/api/settings/{user_id}")
def get_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (user_id,)
    )

    data = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "settings": dict(data) if data else None
    }

@app.post("/api/settings/save")
def save_settings(data: UserSettings):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO settings
    VALUES(?,?,?,?,?,?,?)
    """,
    (
        data.user_id,
        data.theme,
        data.ai_model,
        data.temperature,
        data.system_prompt,
        int(data.chat_memory),
        now()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings saved"
    }


# =========================================================
# PART 6C
# CHAT PREFERENCES
# =========================================================

def create_chat_preferences_table():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_preferences(
        user_id TEXT PRIMARY KEY,
        ai_model TEXT DEFAULT 'gpt-5.5',
        temperature REAL DEFAULT 0.7,
        system_prompt TEXT DEFAULT '',
        memory_enabled INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()

create_chat_preferences_table()
)
""")

class ChatPreferencesRequest(BaseModel):
    user_id: str
    ai_model: str
    temperature: float
    system_prompt: str
    memory_enabled: bool

@app.post("/api/preferences/chat")
def save_chat_preferences(data: ChatPreferencesRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO chat_preferences
    (user_id, ai_model, temperature, system_prompt, memory_enabled)
    VALUES(?,?,?,?,?)
    """, (
        data.user_id,
        data.ai_model,
        data.temperature,
        data.system_prompt,
        int(data.memory_enabled)
    ))

    conn.commit()
    conn.close()

    return {"success": True}


# =========================================================
# PART 6D
# ACCOUNT SETTINGS
# =========================================================

class ChangeUsernameRequest(BaseModel):
    user_id: str
    username: str

class ChangeEmailRequest(BaseModel):
    user_id: str
    email: str

class ChangePasswordRequest(BaseModel):
    user_id: str
    password: str

@app.put("/api/account/username")
def change_username(data: ChangeUsernameRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET username=? WHERE id=?",
        (data.username, data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.put("/api/account/email")
def change_email(data: ChangeEmailRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET email=? WHERE id=?",
        (data.email, data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.put("/api/account/password")
def change_password(data: ChangePasswordRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET password=? WHERE id=?",
        (hash_password(data.password), data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}


# =========================
# PART 6E
# Export / Import Settings
# =========================

import json

@app.get("/api/settings/export/{user_id}")
def export_settings(user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM user_settings WHERE user_id=?",
        (user_id,)
    )

    settings = cur.fetchone()
    conn.close()

    if not settings:
        return {"success": False}

    return {
        "success": True,
        "settings": dict(settings)
    }


# =========================================================
# PART 7
# AI ENGINE + API SOURCES
# Paste below Part 6F
# =========================================================

import os
import requests
from pydantic import BaseModel

# ---------- API KEYS ----------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# ---------- REQUEST MODEL ----------

class AIChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str
    model: str = "openrouter"

# ---------- AI ROUTER ----------

def ask_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    r = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    return r.json()["choices"][0]["message"]["content"]

# ---------- WEB SEARCH ----------

def tavily_search(query):
    if not TAVILY_API_KEY:
        return None

    r = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query
        }
    )

    return r.json()

# ---------- WEATHER ----------

def get_weather(city):
    if not OPENWEATHER_API_KEY:
        return None

    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
    )

    return r.json()

# ---------- STOCKS ----------

def stock_price(symbol):
    if not ALPHA_VANTAGE_API_KEY:
        return None

    r = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
    )

    return r.json()

# ---------- SPORTS ----------

def sports_scores():
    if not ALLSPORTS_API_KEY:
        return None

    r = requests.get(
        "https://apiv2.allsportsapi.com/football/",
        params={
            "met": "Livescore",
            "APIkey": ALLSPORTS_API_KEY
        }
    )

    return r.json()

# ---------- MAIN AI ENDPOINT ----------

@app.post("/api/ai/chat")
def ai_chat(data: AIChatRequest):

    user_message = data.message.lower()

    if user_message.startswith("weather "):
        city = data.message.replace("weather ", "")
        return {
            "success": True,
            "source": "openweather",
            "response": get_weather(city)
        }

    if user_message.startswith("stock "):
        symbol = data.message.replace("stock ", "")
        return {
            "success": True,
            "source": "alpha_vantage",
            "response": stock_price(symbol)
        }

    if user_message.startswith("sports"):
        return {
            "success": True,
            "source": "allsports",
            "response": sports_scores()
        }

    if user_message.startswith("search "):
        query = data.message.replace("search ", "")
        return {
            "success": True,
            "source": "tavily",
            "response": tavily_search(query)
        }

    ai_response = ask_openrouter(data.message)

    return {
        "success": True,
        "provider": "openrouter",
        "response": ai_response
    }

@app.post("/api/settings/import/{user_id}")
def import_settings(user_id: str, settings: dict):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE user_settings
        SET
        theme=?,
        ai_model=?,
        temperature=?,
        system_prompt=?,
        memory_enabled=?
        WHERE user_id=?
        """,
        (
            settings["theme"],
            settings["ai_model"],
            settings["temperature"],
            settings["system_prompt"],
            settings["memory_enabled"],
            user_id
        )
    )

    conn.commit()
    conn.close()

    return {"success": True}


# =========================
# PART 6F
# Reset Settings
# =========================

@app.post("/api/settings/reset/{user_id}")
def reset_settings(user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE user_settings
        SET
        theme='dark',
        ai_model='gpt-5.5',
        temperature=0.7,
        system_prompt='You are a helpful AI assistant.',
        memory_enabled=1
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings reset"
    }


