# =========================================================
# BLOXY-BOT X (PART 1)
# Imports + App + Environment + Database + Models
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import sqlite3
import hashlib
import requests
import json
import os
import time
import uuid

# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Bloxy-Bot X",
    version="1.0"
)

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

# AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")

# Search / Research
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# News
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY", "")

# Sports
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
SPORTMONKS_API_KEY = os.getenv("SPORTMONKS_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

# Finance
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")

# Weather
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Movies
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

# Knowledge
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY", "")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect(
    "bloxybot.db",
    check_same_thread=False
)

cur = conn.cursor()

# Users

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

# Conversations

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

# Drafts

cur.execute("""
CREATE TABLE IF NOT EXISTS drafts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    draft TEXT
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

class ConversationAction(BaseModel):
    email: str
    conversation_id: str

class RenameConversation(BaseModel):
    email: str
    conversation_id: str
    new_title: str

# =========================================================
# HELPERS
# =========================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

def now():
    return str(time.time())

def generate_id():
    return str(uuid.uuid4())

# =========================================================
# END PART 1
# =========================================================

# =========================================================
# BLOXY-BOT X (PART 2)
# Authentication + Conversation Management
# =========================================================

@app.post("/register")
def register(data: Register):

    if "@" not in data.email:
        return {"success": False, "message": "Invalid email"}

    if len(data.password) < 6:
        return {"success": False, "message": "Password too short"}

    try:

        conversation_id = generate_id()

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
def login(data: Login):

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
        return {"success": False}

    return {
        "success": True,
        "username": user[0],
        "verified": bool(user[1])
    }


@app.get("/conversations/{email}")
def get_conversations(email: str):

    cur.execute(
        """
        SELECT conversation_id,title,pinned
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

    conversation_id = generate_id()

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
            now()
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

        results = []

        for item in data.get("results", []):
            results.append(
                item.get("content", "")
            )

        return "\n".join(results)

    except Exception:
        return ""


def news_context(query):

    if not NEWS_API_KEY:
        return ""

    try:

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "pageSize": 5,
                "language": "en",
                "apiKey": NEWS_API_KEY
            },
            timeout=20
        )

        data = r.json()

        articles = []

        for a in data.get("articles", []):

            title = a.get("title", "")

            if title:
                articles.append(title)

        return "\n".join(articles)

    except Exception:
        return ""


def format_response(text):

    if not text:
        return "⚠️ Empty response."

    lines = text.split("\n")

    output = []

    for line in lines:

        line = line.strip()

        if line:
            output.append(line)

    return "\n".join(output)


def ai_reply(message, history):

    live_search = tavily_search(message)

    live_news = news_context(message)

    system_prompt = f"""
You are Bloxy-Bot X.

Rules:
- Be helpful.
- Use clean formatting.
- Use bullet points when useful.
- Keep answers concise.

SEARCH DATA:
{live_search}

NEWS DATA:
{live_news}
"""

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
            "content": message
        }
    )

    for model in MODELS:

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
                    "max_tokens": 1200
                },
                timeout=60
            )

            data = r.json()

            reply = (
                data["choices"][0]
                ["message"]["content"]
            )

            return format_response(reply)

        except Exception:
            continue

    return "⚠️ All AI providers failed."


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
            except Exception:
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
                now(),
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
# News + Sports + Weather + Finance + Movies + Wolfram
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
                "language": "en",
                "pageSize": 10,
                "apiKey": NEWS_API_KEY
            },
            timeout=20
        )

        return r.json()

    except Exception as e:

        return {
            "error": str(e),
            "articles": []
        }


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

    except Exception as e:

        return {
            "error": str(e)
        }


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

    except Exception as e:

        return {
            "error": str(e)
        }


@app.get("/finnhub")
def finnhub_stock(symbol: str):

    try:

        r = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={
                "symbol": symbol,
                "token": FINNHUB_API_KEY
            },
            timeout=20
        )

        return r.json()

    except Exception as e:

        return {
            "error": str(e)
        }


@app.get("/exchange-rate")
def exchange_rate(base: str):

    try:

        r = requests.get(
            f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{base}",
            timeout=20
        )

        return r.json()

    except Exception as e:

        return {
            "error": str(e)
        }


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

    except Exception as e:

        return {
            "error": str(e)
        }


@app.get("/odds")
def odds(sport: str = "soccer_epl"):

    try:

        r = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
            params={
                "apiKey": ODDS_API_KEY
            },
            timeout=20
        )

        return r.json()

    except Exception as e:

        return {
            "error": str(e)
        }


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

    except Exception as e:

        return {
            "error": str(e),
            "results": []
        }


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

    except Exception as e:

        return {
            "error": str(e)
        }


@app.get("/health")
def health():

    return {
        "status": "online",
        "service": "Bloxy-Bot X",
        "time": now()
    }

# =========================================================
# END PART 4
# PART 5 = FULL UI + HTML + CSS + JAVASCRIPT + STARTUP
# =========================================================

<!-- ===================================================== -->

<!-- HTML LAYOUT ONLY -->
<!-- Place inside return """ ... """ -->
<!-- ===================================================== -->

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bloxy-Bot X</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">



</head>

<body>

<div class="app">

    <!-- SIDEBAR -->

    <aside class="sidebar">

        <div class="logo-section">
           
        </div>

        <div class="sidebar-actions">

            <button id="newChatBtn">
                + New Chat
            </button>

        </div>

        <div
            id="conversationList"
            class="conversation-list">
        </div>

    </aside>

    <!-- MAIN -->

    <main class="main">

        <!-- TOPBAR -->

        <header class="topbar">

            <div class="topbar-left">
                <span id="chatTitle">
                    New Chat
                </span>
            </div>

            <div class="topbar-right">

                <button id="clearBtn">
                    Clear
                </button>

                <button id="logoutBtn">
                    Logout
                </button>

            </div>

        </header>

        <!-- CHAT AREA -->

        <section
            id="messages"
            class="messages">
        </section>

        <!-- INPUT -->

        <section class="input-section">

            <div class="input-wrapper">

                <textarea
                    id="messageInput"
                    placeholder="Message Bloxy‑Bot..."
                ></textarea>

                <button id="sendBtn">
                    Send
                </button>

            </div>

            <div class="input-footer">

                <span>
                    Ctrl + Enter to send
                </span>

            </div>

        </section>

    </main>

</div>

<!-- LOGIN MODAL -->

<div
    id="loginModal"
    class="modal">

    <div class="modal-content">

        <h2>Login</h2>

        <input
            id="loginEmail"
            type="email"
            placeholder="Email">

        <input
            id="loginPassword"
            type="password"
            placeholder="Password">

        <button id="loginBtn">
            Login
        </button>

        <button id="showRegisterBtn">
            Create Account
        </button>

        <button id="guestBtn">
            Continue as Guest
        </button>

    </div>

</div>

<!-- REGISTER MODAL -->

<div
    id="registerModal"
    class="modal">

    <div class="modal-content">

        <h2>Create Account</h2>

        <input
            id="registerUsername"
            placeholder="Username">

        <input
            id="registerEmail"
            type="email"
            placeholder="Email">

        <input
            id="registerPassword"
            type="password"
            placeholder="Password">

        <button id="registerBtn">
            Register
        </button>

        <button id="backLoginBtn">
            Back
        </button>

    </div>

</div>

<script>
/* PART 5C JAVASCRIPT GOES HERE */
</script>

</body>
</html>

<!-- ========================= -->
<!-- END PART 5A -->
<!-- ========================= -->

/* ===================================================== */
/* BLOXY-BOT X (PART 5B) */
/* CSS STYLING */
/* ===================================================== */

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

body{
    font-family:'Inter',sans-serif;
    background:#0b0f17;
    color:#ffffff;
    height:100vh;
    overflow:hidden;
}

.app{
    display:flex;
    width:100%;
    height:100vh;
}

/* SIDEBAR */

.sidebar{
    width:280px;
    background:#111827;
    border-right:1px solid #1f2937;
    display:flex;
    flex-direction:column;
}

.logo-section{
    padding:20px;
    border-bottom:1px solid #1f2937;
}

.sidebar-actions{
    padding:15px;
}

#newChatBtn{
    width:100%;
    padding:12px;
    border:none;
    border-radius:10px;
    background:#2563eb;
    color:white;
    cursor:pointer;
}

#newChatBtn:hover{
    background:#1d4ed8;
}

.conversation-list{
    flex:1;
    overflow-y:auto;
    padding:10px;
}

.conversation-item{
    padding:12px;
    margin-bottom:8px;
    background:#1f2937;
    border-radius:10px;
    cursor:pointer;
}

.conversation-item:hover{
    background:#374151;
}

/* MAIN */

.main{
    flex:1;
    display:flex;
    flex-direction:column;
}

.topbar{
    height:70px;
    border-bottom:1px solid #1f2937;
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:0 20px;
}

.topbar-right{
    display:flex;
    gap:10px;
}

.topbar button{
    padding:10px 14px;
    border:none;
    border-radius:8px;
    cursor:pointer;
    background:#2563eb;
    color:white;
}

.messages{
    flex:1;
    overflow-y:auto;
    padding:25px;
    display:flex;
    flex-direction:column;
    gap:15px;
}

.message{
    max-width:80%;
    padding:14px;
    border-radius:14px;
    line-height:1.5;
    word-wrap:break-word;
}

.user-message{
    align-self:flex-end;
    background:#2563eb;
}

.bot-message{
    align-self:flex-start;
    background:#1f2937;
}

.input-section{
    border-top:1px solid #1f2937;
    padding:15px;
}

.input-wrapper{
    display:flex;
    gap:10px;
}

#messageInput{
    flex:1;
    resize:none;
    min-height:70px;
    max-height:200px;
    padding:12px;
    border:none;
    border-radius:12px;
    background:#1f2937;
    color:white;
}

#sendBtn{
    width:120px;
    border:none;
    border-radius:12px;
    background:#10b981;
    color:white;
    cursor:pointer;
}

#sendBtn:hover{
    background:#059669;
}

.input-footer{
    margin-top:8px;
    font-size:12px;
    color:#9ca3af;
}

/* MODALS */

.modal{
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.7);
    display:none;
    justify-content:center;
    align-items:center;
}

.modal-content{
    width:400px;
    background:#111827;
    padding:25px;
    border-radius:16px;
    display:flex;
    flex-direction:column;
    gap:12px;
}

.modal-content input{
    padding:12px;
    border:none;
    border-radius:10px;
    background:#1f2937;
    color:white;
}

.modal-content button{
    padding:12px;
    border:none;
    border-radius:10px;
    background:#2563eb;
    color:white;
    cursor:pointer;
}

/* MOBILE */

@media(max-width:768px){

    .sidebar{
        width:220px;
    }

    .message{
        max-width:95%;
    }

    .topbar{
        padding:0 10px;
    }

    #sendBtn{
        width:90px;
    }
}

/* ===================================================== */
/* END PART 5B */
/* ===================================================== */

/* ===================================================== */
/* BLOXY-BOT X (PART 5C)
   JAVASCRIPT CHAT LOGIC
/* ===================================================== */

let EMAIL = "guest";
let USERNAME = "Guest";
let CURRENT_CHAT = "";
let conversations = [];

/* -------------------------
   HELPERS
------------------------- */

function $(id){
    return document.getElementById(id);
}

function scrollBottom(){
    const box = $("messages");
    box.scrollTop = box.scrollHeight;
}

function saveDraft(){
    localStorage.setItem(
        "bloxy_draft",
        $("messageInput").value
    );
}

function loadDraft(){

    const draft =
        localStorage.getItem(
            "bloxy_draft"
        );

    if(draft){
        $("messageInput").value = draft;
    }
}

/* -------------------------
   MESSAGE RENDERING
------------------------- */

function addUserMessage(text){

    const div =
        document.createElement("div");

    div.className =
        "message user-message";

    div.textContent = text;

    $("messages")
        .appendChild(div);

    scrollBottom();
}

function addBotMessage(text){

    const div =
        document.createElement("div");

    div.className =
        "message bot-message";

    div.textContent = text;

    $("messages")
        .appendChild(div);

    scrollBottom();
}

function clearMessages(){

    $("messages").innerHTML = "";
}

/* -------------------------
   CHAT
------------------------- */

async function sendMessage(){

    const input =
        $("messageInput");

    const text =
        input.value.trim();

    if(!text){
        return;
    }

    addUserMessage(text);

    input.value = "";

    saveDraft();

    try{

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
                        email:EMAIL,
                        conversation_id:
                        CURRENT_CHAT,
                        message:text
                    })
                }
            );

        const data =
            await response.json();

        addBotMessage(
            data.reply ||
            "No response."
        );

    }catch(error){

        addBotMessage(
            "Connection error."
        );

        console.error(error);
    }
}

/* -------------------------
   CONVERSATIONS
------------------------- */

async function loadConversations(){

    if(
        EMAIL === "guest"
    ){
        return;
    }

    try{

        const response =
            await fetch(
                `/conversations/${EMAIL}`
            );

        const data =
            await response.json();

        conversations =
            data.conversations || [];

        renderConversations();

    }catch(error){

        console.error(error);
    }
}

function renderConversations(){

    const list =
        $("conversationList");

    list.innerHTML = "";

    conversations.forEach(
        conversation => {

        const item =
            document.createElement("div");

        item.className =
            "conversation-item";

        item.textContent =
            conversation.title;

        item.onclick = () => {

            CURRENT_CHAT =
            conversation.conversation_id;

            $("chatTitle")
                .textContent =
                conversation.title;

            clearMessages();
        };

        list.appendChild(item);
    });
}

async function createChat(){

    if(
        EMAIL === "guest"
    ){
        return;
    }

    try{

        const response =
            await fetch(
                "/new-chat",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                        "application/json"
                    },
                    body:JSON.stringify({
                        email:EMAIL,
                        conversation_id:""
                    })
                }
            );

        const data =
            await response.json();

        CURRENT_CHAT =
            data.conversation_id;

        await loadConversations();

    }catch(error){

        console.error(error);
    }
}

/* -------------------------
   LOGIN
------------------------- */

async function login(){

    try{

        const response =
            await fetch(
                "/login",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                        "application/json"
                    },
                    body:JSON.stringify({
                        email:
                        $("loginEmail").value,

                        password:
                        $("loginPassword").value
                    })
                }
            );

        const data =
            await response.json();

        if(!data.success){

            alert(
                "Login failed"
            );

            return;
        }

        EMAIL =
            $("loginEmail").value;

        USERNAME =
            data.username;

        $("loginModal")
            .style.display =
            "none";

        loadConversations();

    }catch(error){

        console.error(error);
    }
}

/* -------------------------
   REGISTER
------------------------- */

async function register(){

    try{

        const response =
            await fetch(
                "/register",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                        "application/json"
                    },
                    body:JSON.stringify({
                        username:
                        $("registerUsername").value,

                        email:
                        $("registerEmail").value,

                        password:
                        $("registerPassword").value
                    })
                }
            );

        const data =
            await response.json();

        if(!data.success){

            alert(
                "Registration failed"
            );

            return;
        }

        EMAIL =
            $("registerEmail").value;

        CURRENT_CHAT =
            data.conversation_id;

        $("registerModal")
            .style.display =
            "none";

        await loadConversations();

    }catch(error){

        console.error(error);
    }
}

/* -------------------------
   GUEST MODE
------------------------- */

function guestMode(){

    EMAIL = "guest";

    USERNAME = "Guest";

    $("loginModal")
        .style.display =
        "none";
}

/* -------------------------
   EVENTS
------------------------- */

$("sendBtn")
?.addEventListener(
    "click",
    sendMessage
);

$("newChatBtn")
?.addEventListener(
    "click",
    createChat
);

$("loginBtn")
?.addEventListener(
    "click",
    login
);

$("registerBtn")
?.addEventListener(
    "click",
    register
);

$("guestBtn")
?.addEventListener(
    "click",
    guestMode
);

$("showRegisterBtn")
?.addEventListener(
    "click",
    () => {

    $("loginModal")
        .style.display =
        "none";

    $("registerModal")
        .style.display =
        "flex";
});

$("backLoginBtn")
?.addEventListener(
    "click",
    () => {

    $("registerModal")
        .style.display =
        "none";

    $("loginModal")
        .style.display =
        "flex";
});

$("messageInput")
?.addEventListener(
    "keydown",
    function(e){

    saveDraft();

    if(
        e.ctrlKey &&
        e.key === "Enter"
    ){

        e.preventDefault();

        sendMessage();
    }
});

/* -------------------------
   STARTUP
------------------------- */

window.onload = () => {

    loadDraft();

    $("loginModal")
        .style.display =
        "flex";
};

/* ===================================================== */
/* END PART 5C */
/* ===================================================== */

# =========================================================
# BLOXY-BOT X (PART 5D)
# FASTAPI UI ROUTE + STARTUP
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body>
    <h1>Bloxy Bot Working</h1>
    </body>
    </html>
    """
    
# =========================================================
# EXTRA ROUTES
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "service": "Bloxy-Bot X",
        "version": "1.0"
    }


@app.get("/ping")
def ping():

    return {
        "message": "pong"
    }


# =========================================================
# DATABASE SAFETY
# =========================================================

def close_database():

    try:
        conn.commit()
        conn.close()

    except Exception:
        pass


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    print("================================")
    print("Bloxy-Bot X Starting...")
    print("================================")


@app.on_event("shutdown")
def shutdown_event():

    close_database()

    print("================================")
    print("Bloxy-Bot X Shutdown")
    print("================================")


# =========================================================
# MAIN ENTRY
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                8000
            )
        ),
        reload=False
    )

# =========================================================
# END PART 5D
# END OF FILE
# =========================================================
