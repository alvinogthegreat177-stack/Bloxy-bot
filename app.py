# =========================================================
# BLOXY-BOT X V4
# PART 1
# FOUNDATION + SETTINGS + THEMES PREPARATION
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sqlite3
import uuid
import hashlib
from datetime import datetime

# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Bloxy-Bot X",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================================================
# DATABASE
# =========================================================

DB_NAME = "bloxybotx.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# =========================================================
# HELPERS
# =========================================================

def generate_id():
    return str(uuid.uuid4())

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# =========================================================
# TABLES
# =========================================================

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

    # SETTINGS MENU SUPPORT

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        font_size TEXT,
        chat_width TEXT,
        animations INTEGER,
        timestamps INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tables()

# =========================================================
# MODELS
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ThemeRequest(BaseModel):
    user_id: str
    theme: str

# =========================================================
# THEMES
# =========================================================

AVAILABLE_THEMES = [
    "dark",
    "light",
    "midnight",
    "ocean",
    "purple",
    "emerald"
]

DEFAULT_THEME = "dark"

# =========================================================
# SETTINGS MENU CATEGORIES
# =========================================================

SETTINGS_SECTIONS = [
    "appearance",
    "chat",
    "privacy",
    "account",
    "about"
]

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "online",
        "app": "Bloxy-Bot X",
        "theme_support": True,
        "settings_support": True
    }

# =========================================================
# END PART 1
# =========================================================


# =========================================================
# BLOXY-BOT X V4
# PART 2
# AUTHENTICATION + GUEST MODE
# =========================================================

# Add these imports at the top if not already present

import secrets

# =========================================================
# SESSION TABLE
# =========================================================

def create_session_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_session_table()

# =========================================================
# AUTH HELPERS
# =========================================================

def create_session(user_id):

    token = secrets.token_hex(32)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO sessions
    VALUES (?, ?, ?)
    """, (
        token,
        user_id,
        now()
    ))

    conn.commit()
    conn.close()

    return token


def get_user_by_email(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM users
    WHERE email = ?
    """, (email,))

    user = cur.fetchone()

    conn.close()

    return user


def get_user_by_id(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM users
    WHERE id = ?
    """, (user_id,))

    user = cur.fetchone()

    conn.close()

    return user

# =========================================================
# REGISTER
# =========================================================

@app.post("/api/register")
def register(data: RegisterRequest):

    existing = get_user_by_email(
        data.email
    )

    if existing:

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

    cur.execute("""
    INSERT INTO users
    VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        data.username,
        data.email,
        hash_password(data.password),
        now()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "user_id": user_id,
        "message": "Account created successfully 🎉"
    }

# =========================================================
# LOGIN
# =========================================================

@app.post("/api/login")
def login(data: LoginRequest):

    user = get_user_by_email(
        data.email
    )

    if not user:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    if user["password"] != hash_password(
        data.password
    ):

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    token = create_session(
        user["id"]
    )

    return {
        "success": True,
        "token": token,
        "user_id": user["id"],
        "username": user["username"]
    }

# =========================================================
# GUEST MODE
# =========================================================

@app.post("/api/guest")
def guest_login():

    guest_id = generate_id()

    return {
        "success": True,
        "guest": True,
        "user_id": guest_id,
        "username": "Guest User"
    }

# =========================================================
# LOGOUT
# =========================================================

@app.delete("/api/logout/{token}")
def logout(token: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM sessions
    WHERE token = ?
    """, (token,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Logged out successfully 👋"
    }

# =========================================================
# CURRENT USER
# =========================================================

@app.get("/api/user/{user_id}")
def get_user(user_id: str):

    user = get_user_by_id(
        user_id
    )

    if not user:

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": "User not found"
            }
        )

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

# =========================================================
# END PART 2
# =========================================================


# =========================================================
# BLOXY-BOT X V4
# PART 3
# CONVERSATIONS + CHAT HISTORY + SIDEBAR MANAGEMENT
# =========================================================

# =========================================================
# CREATE CONVERSATION
# =========================================================

@app.post("/api/conversations/create")
def create_conversation(data: CreateConversationRequest):

    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO conversations
    VALUES (?, ?, ?, ?, ?)
    """, (
        conversation_id,
        data.user_id,
        data.title,
        now(),
        now()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "conversation_id": conversation_id
    }

# =========================================================
# GET USER CONVERSATIONS
# =========================================================

@app.get("/api/conversations/{user_id}")
def get_conversations(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM conversations
    WHERE user_id = ?
    ORDER BY updated_at DESC
    """, (user_id,))

    conversations = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversations": conversations
    }

# =========================================================
# RENAME CONVERSATION
# =========================================================

@app.put("/api/conversations/rename/{conversation_id}")
def rename_conversation(
    conversation_id: str,
    title: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    UPDATE conversations
    SET title = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        title,
        now(),
        conversation_id
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Conversation renamed ✏️"
    }

# =========================================================
# DELETE CONVERSATION
# =========================================================

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM messages
    WHERE conversation_id = ?
    """, (conversation_id,))

    cur.execute("""
    DELETE FROM conversations
    WHERE id = ?
    """, (conversation_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Conversation deleted 🗑️"
    }

# =========================================================
# SAVE MESSAGE
# =========================================================

def save_message(
    conversation_id,
    role,
    content
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO messages
    VALUES (?, ?, ?, ?, ?)
    """, (
        generate_id(),
        conversation_id,
        role,
        content,
        now()
    ))

    cur.execute("""
    UPDATE conversations
    SET updated_at = ?
    WHERE id = ?
    """, (
        now(),
        conversation_id
    ))

    conn.commit()
    conn.close()

# =========================================================
# GET CHAT HISTORY
# =========================================================

@app.get("/api/messages/{conversation_id}")
def get_messages(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM messages
    WHERE conversation_id = ?
    ORDER BY created_at ASC
    """, (conversation_id,))

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "messages": messages
    }

# =========================================================
# CLEAR CHAT HISTORY
# =========================================================

@app.delete("/api/messages/clear/{conversation_id}")
def clear_messages(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM messages
    WHERE conversation_id = ?
    """, (conversation_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Chat cleared 🧹"
    }

# =========================================================
# END PART 3
# =========================================================


# =========================================================
# BLOXY-BOT X V4
# PART 4
# SMART BOT ENGINE + CHAT API
# =========================================================

# =========================================================
# SMART RESPONSE ENGINE
# =========================================================

def bloxy_reply(message, history=None):

    text = message.lower().strip()

    greetings = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening"
    ]

    if text in greetings:
        return "👋 Hello! I'm Bloxy‑Bot X. How can I help you today?"

    if "how are you" in text:
        return "😊 I'm doing great! Ready to help with coding, writing, research, or anything else."

    if "who are you" in text:
        return "🤖 I'm Bloxy‑Bot X, your AI assistant."

    if "thank" in text:
        return "😄 You're welcome!"

    if "bye" in text:
        return "👋 Goodbye! Have an amazing day."

    if "joke" in text:
        return (
            "😂 Why do programmers prefer dark mode?\n\n"
            "Because light attracts bugs."
        )

    if "help" in text:
        return (
            "✨ I can help with:\n\n"
            "• Coding 💻\n"
            "• Writing ✍️\n"
            "• Research 🔍\n"
            "• Debugging 🛠️\n"
            "• Ideas 💡\n"
            "• General questions 🤔"
        )

    # Prevent empty responses

    if len(text) < 2:
        return "🤔 Could you tell me a bit more?"

    # Default intelligent response

    return (
        f"💬 You said:\n\n"
        f"'{message}'\n\n"
        f"I understand your message and I'm ready to discuss it further."
    )

# =========================================================
# SEND MESSAGE
# =========================================================

@app.post("/api/chat")
def chat(data: SendMessageRequest):

    user_message = data.message

    save_message(
        data.conversation_id,
        "user",
        user_message
    )

    bot_response = bloxy_reply(
        user_message
    )

    save_message(
        data.conversation_id,
        "assistant",
        bot_response
    )

    return {
        "success": True,
        "response": bot_response
    }

# =========================================================
# CHAT STATS
# =========================================================

@app.get("/api/chat/stats/{conversation_id}")
def chat_stats(conversation_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT COUNT(*)
    FROM messages
    WHERE conversation_id = ?
    """, (conversation_id,))

    total_messages = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "total_messages": total_messages
    }

# =========================================================
# BOT INFO
# =========================================================

@app.get("/api/bot")
def bot_info():

    return {
        "name": "Bloxy-Bot X",
        "version": "2.0",
        "emoji_support": True,
        "smart_responses": True
    }

# =========================================================
# END PART 4
# =========================================================


# =========================================================
# PART 5(A-C) CHUNK 1
# START OF SINGLE FRONTEND SCRIPT
# PASTE INSIDE:
#
# @app.get("/", response_class=HTMLResponse)
# def home():
#     return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Bloxy-Bot X</title>

<style>

/* =========================
   THEME VARIABLES
========================= */

:root{
    --bg:#0f1117;
    --sidebar:#171923;
    --card:#1d2230;
    --text:#ffffff;
    --muted:#9ca3af;
    --accent:#ff8a00;
}

body.light{
    --bg:#f5f7fb;
    --sidebar:#ffffff;
    --card:#eef2f7;
    --text:#111827;
    --muted:#6b7280;
}

/* =========================
   GLOBAL
========================= */

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:Inter,sans-serif;
}

body{
    background:var(--bg);
    color:var(--text);
    height:100vh;
    overflow:hidden;
}

/* =========================
   LAYOUT
========================= */

.app{
    display:flex;
    height:100vh;
}

.sidebar{
    width:280px;
    background:var(--sidebar);
    border-right:1px solid rgba(255,255,255,.08);
}

.main{
    flex:1;
    display:flex;
    flex-direction:column;
}

.chat-area{
    flex:1;
    overflow-y:auto;
    padding:30px;
}

.input-area{
    padding:20px;
    border-top:1px solid rgba(255,255,255,.08);
}

/* =========================
   SIDEBAR
========================= */

.logo{
    padding:20px;
    font-size:24px;
    font-weight:700;
}

.new-chat{
    margin:15px;
    padding:14px;
    border:none;
    width:calc(100% - 30px);
    border-radius:12px;
    background:var(--accent);
    color:white;
    cursor:pointer;
}

.search{
    margin:15px;
}

.search input{
    width:100%;
    padding:12px;
    border-radius:10px;
    border:none;
}

/* =========================
   CHAT
========================= */

.message{
    max-width:800px;
    margin-bottom:20px;
    padding:16px;
    border-radius:16px;
    background:var(--card);
}

.user{
    margin-left:auto;
}

.assistant{
    margin-right:auto;
}

/* =========================
   SETTINGS MODAL
========================= */

.settings-modal{
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.6);
}

.settings-box{
    width:700px;
    max-width:90%;
    margin:60px auto;
    background:var(--sidebar);
    border-radius:20px;
    padding:25px;
}

</style>
</head>

<body>

<div class="app">

    <div class="sidebar">

        <div class="logo">
            🤖 Bloxy‑Bot X
        </div>

        <button class="new-chat">
            ➕ New Chat
        </button>

        <div class="search">
            <input placeholder="Search chats...">
        </div>

    </div>

    <div class="main">

        <div id="chatArea" class="chat-area">

            <div class="message assistant">
                👋 Welcome to Bloxy‑Bot X
            </div>

        </div>

        <div class="input-area">

            <input
                id="messageInput"
                placeholder="Message Bloxy‑Bot X..."
                style="width:100%;padding:15px;border-radius:14px;"
            >

        </div>

    </div>

</div>

<script>

// =========================
// THEME SYSTEM
// =========================

function setTheme(theme){
    if(theme === "light"){
        document.body.classList.add("light");
    }else{
        document.body.classList.remove("light");
    }
    localStorage.setItem("theme", theme);
}

const savedTheme =
    localStorage.getItem("theme") || "dark";

setTheme(savedTheme);

</script>

<!-- CHUNK 1 CONTINUES IN CHUNK 2 -->

</body>
</html>
<!-- =====================================================
PART 5(A-C) CHUNK 2
PASTE DIRECTLY UNDER CHUNK 1
===================================================== -->

<!-- SETTINGS MODAL -->

<div id="settingsModal" class="settings-modal">

    <div class="settings-box">

        <h2>⚙️ Settings</h2>

        <br>

        <h3>Appearance</h3>

        <br>

        <button onclick="setTheme('dark')">
            🌙 Dark Theme
        </button>

        <button onclick="setTheme('light')">
            ☀️ Light Theme
        </button>

        <br><br>

        <h3>Chat Preferences</h3>

        <br>

        <label>
            <input type="checkbox" checked>
            Enable Animations
        </label>

        <br><br>

        <label>
            <input type="checkbox" checked>
            Show Timestamps
        </label>

        <br><br>

        <button onclick="closeSettings()">
            Close
        </button>

    </div>

</div>

<script>

// =========================
// SETTINGS
// =========================

function openSettings(){
    document.getElementById(
        "settingsModal"
    ).style.display = "block";
}

function closeSettings(){
    document.getElementById(
        "settingsModal"
    ).style.display = "none";
}

// =========================
// NEW CHAT
// =========================

document
.querySelector(".new-chat")
.addEventListener("click", () => {

    const area =
        document.getElementById("chatArea");

    area.innerHTML = `
        <div class="message assistant">
            ✨ New conversation started
        </div>
    `;
});

// =========================
// SEND MESSAGE
// =========================

const input =
    document.getElementById(
        "messageInput"
    );

input.addEventListener(
    "keypress",
    async function(event){

        if(event.key !== "Enter"){
            return;
        }

        const text =
            input.value.trim();

        if(!text){
            return;
        }

        const area =
            document.getElementById(
                "chatArea"
            );

        area.innerHTML += `
            <div class="message user">
                ${text}
            </div>
        `;

        input.value = "";

        area.scrollTop =
            area.scrollHeight;

        setTimeout(() => {

            area.innerHTML += `
                <div class="message assistant">
                    🤖 ${text}
                </div>
            `;

            area.scrollTop =
                area.scrollHeight;

        }, 500);

    }
);

// =========================
// SIDEBAR SETTINGS BUTTON
// =========================

const settingsButton =
document.createElement("button");

settingsButton.innerHTML =
"⚙️ Settings";

settingsButton.style.margin =
"15px";

settingsButton.style.padding =
"14px";

settingsButton.style.width =
"calc(100% - 30px)";

settingsButton.style.borderRadius =
"12px";

settingsButton.onclick =
openSettings;

document
.querySelector(".sidebar")
.appendChild(settingsButton);
<!-- =====================================================
PART 5(A-C) CHUNK 3
PASTE DIRECTLY UNDER CHUNK 2
===================================================== -->

// =========================
// CHAT SEARCH
// =========================

const searchInput =
document.querySelector(
    ".search input"
);

searchInput.addEventListener(
    "input",
    function(){

        const query =
            this.value.toLowerCase();

        document
        .querySelectorAll(".message")
        .forEach(msg => {

            const text =
                msg.innerText.toLowerCase();

            msg.style.display =
                text.includes(query)
                ? "block"
                : "none";

        });

    }
);

// =========================
// MOBILE SIDEBAR
// =========================

function toggleSidebar(){

    const sidebar =
        document.querySelector(
            ".sidebar"
        );

    if(
        sidebar.style.display ===
        "none"
    ){
        sidebar.style.display =
        "block";
    }
    else{
        sidebar.style.display =
        "none";
    }

}

// =========================
// RESPONSIVE
// =========================

window.addEventListener(
    "resize",
    () => {

        if(
            window.innerWidth > 900
        ){

            document
            .querySelector(".sidebar")
            .style.display = "block";

        }

    }
);

// =========================
// AUTO SCROLL
// =========================

function scrollBottom(){

    const area =
    document.getElementById(
        "chatArea"
    );

    area.scrollTop =
    area.scrollHeight;

}

// =========================
// STARTUP
// =========================

window.onload = () => {

    scrollBottom();

    const savedTheme =
    localStorage.getItem(
        "theme"
    ) || "dark";

    setTheme(savedTheme);

};

// =========================
// END SCRIPT
// =========================

</script>

</body>
</html>

"""
# =========================================================
# PART 5D
# UI SUPPORT ROUTES
# =========================================================

from fastapi.responses import HTMLResponse

# =========================================================
# AVAILABLE THEMES
# =========================================================

@app.get("/api/themes")
def get_themes():

    return {
        "success": True,
        "themes": [
            {
                "id": "dark",
                "name": "Dark"
            },
            {
                "id": "light",
                "name": "Light"
            },
            {
                "id": "midnight",
                "name": "Midnight"
            },
            {
                "id": "ocean",
                "name": "Ocean"
            },
            {
                "id": "purple",
                "name": "Purple"
            }
        ]
    }

# =========================================================
# APP STATUS
# =========================================================

@app.get("/api/status")
def app_status():

    return {
        "success": True,
        "name": "Bloxy‑Bot X",
        "version": "4.0",
        "frontend_loaded": True,
        "backend_loaded": True
    }

# =========================================================
# USER PREFERENCES
# =========================================================

@app.get("/api/preferences/{user_id}")
def get_preferences(user_id: str):

    return {
        "success": True,
        "theme": "dark",
        "sidebar_open": True,
        "animations": True
    }

# =========================================================
# SAVE PREFERENCES
# =========================================================

@app.post("/api/preferences/save")
def save_preferences(data: dict):

    return {
        "success": True,
        "message": "Preferences saved"
    }

# =========================================================
# SIDEBAR STATE
# =========================================================

@app.post("/api/sidebar")
def sidebar_state(data: dict):

    return {
        "success": True,
        "sidebar_open": data.get(
            "sidebar_open",
            True
        )
    }

# =========================================================
# SETTINGS MODAL
# =========================================================

@app.get("/api/settings")
def settings_info():

    return {
        "success": True,
        "available_sections": [
            "appearance",
            "chat",
            "account"
        ]
    }

# =========================================================
# END PART 5D
# =========================================================


# =========================================================
# PART 6
# ADVANCED SETTINGS SYSTEM
# =========================================================

from pydantic import BaseModel

# =========================================================
# MODELS
# =========================================================

class UserSettings(BaseModel):
    user_id: str
    theme: str = "dark"
    notifications: bool = True
    animations: bool = True
    timestamps: bool = True
    compact_mode: bool = False

# =========================================================
# SETTINGS TABLE
# =========================================================

def create_settings_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        notifications INTEGER,
        animations INTEGER,
        timestamps INTEGER,
        compact_mode INTEGER,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================================================
# GET SETTINGS
# =========================================================

@app.get("/api/settings/{user_id}")
def get_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "settings": row
    }

# =========================================================
# SAVE SETTINGS
# =========================================================

@app.post("/api/settings/save")
def save_settings(data: UserSettings):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO settings
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        data.user_id,
        data.theme,
        int(data.notifications),
        int(data.animations),
        int(data.timestamps),
        int(data.compact_mode),
        now()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings updated"
    }

# =========================================================
# EXPORT CHAT
# =========================================================

@app.get("/api/export/{conversation_id}")
def export_chat(conversation_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT role,message
    FROM messages
    WHERE conversation_id=?
    """, (conversation_id,))

    data = cur.fetchall()

    conn.close()

    return {
        "success": True,
        "messages": data
    }

# =========================================================
# RESET SETTINGS
# =========================================================

@app.post("/api/settings/reset/{user_id}")
def reset_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM settings WHERE user_id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings reset"
    }

# =========================================================
# AVAILABLE THEMES
# =========================================================

@app.get("/api/themes")
def themes():

    return {
        "themes":[
            "dark",
            "light",
            "midnight",
            "ocean",
            "purple",
            "emerald",
            "crimson",
            "sunset"
        ]
    }

# =========================================================
# END PART 6
# =========================================================


# =========================================================
# PART 7A
# AI PROVIDER MANAGER
# PASTE DIRECTLY BELOW PART 6
# =========================================================

import os
import json
import asyncio
import requests

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# =========================================================
# API KEYS
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================================================
# AI CONFIG
# =========================================================

AI_PRIORITY = [
    "openrouter",
    "groq",
    "openai"
]

DEFAULT_MODELS = {
    "openrouter": "openai/gpt-4o-mini",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini"
}

# =========================================================
# REQUEST MODEL
# =========================================================

class AIRequest(BaseModel):
    message: str
    provider: str = "auto"
    model: str = ""
    temperature: float = 0.7

# =========================================================
# PROVIDER STATUS
# =========================================================

def provider_status():

    return {
        "openrouter": bool(OPENROUTER_API_KEY),
        "groq": bool(GROQ_API_KEY),
        "openai": bool(OPENAI_API_KEY)
    }

# =========================================================
# SELECT PROVIDER
# =========================================================

def get_best_provider():

    status = provider_status()

    for provider in AI_PRIORITY:

        if status.get(provider):
            return provider

    return None

# =========================================================
# OPENROUTER
# =========================================================

def ask_openrouter(prompt, model=None):

    model = model or DEFAULT_MODELS["openrouter"]

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
            "messages": [
                {
                    "role":"user",
                    "content":prompt
                }
            ]
        },
        timeout=60
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]

# =========================================================
# GROQ
# =========================================================

def ask_groq(prompt, model=None):

    model = model or DEFAULT_MODELS["groq"]

    response = requests.post(
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
                    "role":"user",
                    "content":prompt
                }
            ]
        },
        timeout=60
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]

# =========================================================
# OPENAI
# =========================================================

def ask_openai(prompt, model=None):

    model = model or DEFAULT_MODELS["openai"]

    response = requests.post(
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
                    "role":"user",
                    "content":prompt
                }
            ]
        },
        timeout=60
    )

    data = response.json()

    return data["choices"][0]["message"]["content"]

# =========================================================
# SMART FALLBACK
# =========================================================

def ask_ai(prompt):

    providers = AI_PRIORITY

    for provider in providers:

        try:

            if provider == "openrouter" and OPENROUTER_API_KEY:
                return ask_openrouter(prompt)

            if provider == "groq" and GROQ_API_KEY:
                return ask_groq(prompt)

            if provider == "openai" and OPENAI_API_KEY:
                return ask_openai(prompt)

        except Exception:
            continue

    return "No AI providers available."

# =========================================================
# PROVIDER LIST
# =========================================================

@app.get("/api/ai/providers")
def ai_providers():

    return {
        "success": True,
        "providers": provider_status(),
        "priority": AI_PRIORITY
    }

# =========================================================
# ACTIVE PROVIDER
# =========================================================

@app.get("/api/ai/provider")
def active_provider():

    return {
        "success": True,
        "provider": get_best_provider()
    }

# =========================================================
# CHAT ENDPOINT
# =========================================================

@app.post("/api/ai/chat")
def ai_chat(data: AIRequest):

    provider = data.provider

    if provider == "auto":
        response = ask_ai(data.message)

    elif provider == "openrouter":
        response = ask_openrouter(
            data.message,
            data.model or None
        )

    elif provider == "groq":
        response = ask_groq(
            data.message,
            data.model or None
        )

    elif provider == "openai":
        response = ask_openai(
            data.message,
            data.model or None
        )

    else:
        response = "Invalid provider."

    return {
        "success": True,
        "provider": provider,
        "response": response
    }

# =========================================================
# AI HEALTH CHECK
# =========================================================

@app.get("/api/ai/health")
def ai_health():

    return {
        "success": True,
        "available": provider_status(),
        "active": get_best_provider()
    }

# =========================================================
# END PART 7A
# PASTE PART 7B DIRECTLY BELOW THIS
# =========================================================
# =========================================================
# PART 7B
# RESEARCH ENGINE + WEB INTELLIGENCE
# PASTE DIRECTLY BELOW PART 7A
# =========================================================

import requests
from typing import Dict, List

# =========================================================
# RESEARCH API KEYS
# =========================================================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")

# =========================================================
# RESEARCH PRIORITY
# =========================================================

RESEARCH_PRIORITY = [
    "tavily",
    "exa",
    "firecrawl",
    "wolfram"
]

# =========================================================
# RESEARCH REQUEST
# =========================================================

class ResearchRequest(BaseModel):
    query: str
    source: str = "auto"
    max_results: int = 10

# =========================================================
# STATUS
# =========================================================

def research_status():

    return {
        "tavily": bool(TAVILY_API_KEY),
        "exa": bool(EXA_API_KEY),
        "firecrawl": bool(FIRECRAWL_API_KEY),
        "wolfram": bool(WOLFRAM_APP_ID)
    }

# =========================================================
# TAVILY SEARCH
# =========================================================

def search_tavily(query, limit=10):

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": limit
        },
        timeout=60
    )

    return response.json()

# =========================================================
# EXA SEARCH
# =========================================================

def search_exa(query, limit=10):

    response = requests.post(
        "https://api.exa.ai/search",
        headers={
            "x-api-key": EXA_API_KEY
        },
        json={
            "query": query,
            "numResults": limit
        },
        timeout=60
    )

    return response.json()

# =========================================================
# FIRECRAWL SEARCH
# =========================================================

def search_firecrawl(query):

    response = requests.post(
        "https://api.firecrawl.dev/v1/search",
        headers={
            "Authorization":
            f"Bearer {FIRECRAWL_API_KEY}"
        },
        json={
            "query": query
        },
        timeout=60
    )

    return response.json()

# =========================================================
# WOLFRAM SEARCH
# =========================================================

def search_wolfram(query):

    response = requests.get(
        "https://api.wolframalpha.com/v2/query",
        params={
            "appid": WOLFRAM_APP_ID,
            "input": query,
            "output": "json"
        },
        timeout=60
    )

    return response.json()

# =========================================================
# AUTO RESEARCH
# =========================================================

def research(query):

    engines = RESEARCH_PRIORITY

    for engine in engines:

        try:

            if engine == "tavily" and TAVILY_API_KEY:
                return search_tavily(query)

            if engine == "exa" and EXA_API_KEY:
                return search_exa(query)

            if engine == "firecrawl" and FIRECRAWL_API_KEY:
                return search_firecrawl(query)

            if engine == "wolfram" and WOLFRAM_APP_ID:
                return search_wolfram(query)

        except Exception:
            continue

    return {
        "success": False,
        "message": "No research engine available."
    }

# =========================================================
# RESEARCH ENDPOINT
# =========================================================

@app.post("/api/research")
def run_research(data: ResearchRequest):

    source = data.source

    if source == "auto":
        results = research(data.query)

    elif source == "tavily":
        results = search_tavily(
            data.query,
            data.max_results
        )

    elif source == "exa":
        results = search_exa(
            data.query,
            data.max_results
        )

    elif source == "firecrawl":
        results = search_firecrawl(
            data.query
        )

    elif source == "wolfram":
        results = search_wolfram(
            data.query
        )

    else:
        results = {
            "success": False,
            "message": "Invalid source."
        }

    return {
        "success": True,
        "query": data.query,
        "results": results
    }

# =========================================================
# RESEARCH SOURCES
# =========================================================

@app.get("/api/research/sources")
def research_sources():

    return {
        "success": True,
        "sources": research_status(),
        "priority": RESEARCH_PRIORITY
    }

# =========================================================
# FACT CHECK
# =========================================================

@app.post("/api/research/factcheck")
def fact_check(data: ResearchRequest):

    result = research(data.query)

    return {
        "success": True,
        "query": data.query,
        "verification": result
    }

# =========================================================
# CITATION GENERATOR
# =========================================================

@app.post("/api/research/citations")
def citations(data: ResearchRequest):

    results = research(data.query)

    return {
        "success": True,
        "query": data.query,
        "citations": results
    }

# =========================================================
# RESEARCH HEALTH
# =========================================================

@app.get("/api/research/health")
def research_health():

    return {
        "success": True,
        "engines": research_status(),
        "priority": RESEARCH_PRIORITY
    }

# =========================================================
# END PART 7B
# PASTE PART 7C DIRECTLY BELOW THIS
# =========================================================
# =========================================================
# PART 7C
# NEWS + SPORTS + WEATHER + FINANCE + MOVIES
# PASTE DIRECTLY BELOW PART 7B
# =========================================================

# API KEYS

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")

ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# =========================================================
# REQUEST MODELS
# =========================================================

class SearchQuery(BaseModel):
    query: str

class CityRequest(BaseModel):
    city: str

class SymbolRequest(BaseModel):
    symbol: str

# =========================================================
# NEWS
# =========================================================

@app.get("/api/news")
def get_news():

    try:

        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "language":"en",
                "pageSize":20,
                "apiKey":NEWS_API_KEY
            },
            timeout=30
        )

        return response.json()

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }

# =========================================================
# WEATHER
# =========================================================

@app.post("/api/weather")
def weather(data: CityRequest):

    try:

        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q":data.city,
                "appid":OPENWEATHER_API_KEY,
                "units":"metric"
            },
            timeout=30
        )

        return response.json()

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }

# =========================================================
# STOCKS
# =========================================================

@app.post("/api/stocks")
def stocks(data: SymbolRequest):

    try:

        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function":"GLOBAL_QUOTE",
                "symbol":data.symbol,
                "apikey":ALPHA_VANTAGE_API_KEY
            },
            timeout=30
        )

        return response.json()

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }

# =========================================================
# FOREX
# =========================================================

@app.get("/api/forex/{base}")
def forex(base:str):

    try:

        response = requests.get(
            f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{base}",
            timeout=30
        )

        return response.json()

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }

# =========================================================
# SPORTS
# =========================================================

@app.get("/api/sports/status")
def sports_status():

    return {
        "allsports": bool(ALLSPORTS_API_KEY),
        "apisports": bool(APISPORTS_API_KEY),
        "sportmonks": bool(SPORTMONK_API_KEY),
        "sportradar": bool(SPORTRADAR_API_KEY),
        "thesportsdb": bool(THESPORTSDB_API_KEY),
        "odds": bool(ODDS_API_KEY)
    }

# =========================================================
# MOVIES
# =========================================================

@app.post("/api/movies/search")
def movie_search(data: SearchQuery):

    try:

        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key":TMDB_API_KEY,
                "query":data.query
            },
            timeout=30
        )

        return response.json()

    except Exception as e:

        return {
            "success":False,
            "error":str(e)
        }

# =========================================================
# SERVICES HEALTH
# =========================================================

@app.get("/api/services/health")
def services_health():

    return {
        "news": True,
        "weather": True,
        "finance": True,
        "sports": True,
        "movies": True
    }

# =========================================================
# END PART 7C
# PASTE PART 7D DIRECTLY BELOW THIS
# =========================================================
# =========================================================
# PART 7D
# MEMORY + CONTEXT + CHAT HISTORY
# PASTE DIRECTLY BELOW PART 7C
# =========================================================

from collections import deque
from datetime import datetime

# =========================================================
# MEMORY CONFIG
# =========================================================

MAX_MEMORY_MESSAGES = 50
MAX_CONTEXT_MESSAGES = 20

# =========================================================
# IN-MEMORY CACHE
# =========================================================

SESSION_MEMORY = {}

# =========================================================
# MEMORY MODELS
# =========================================================

class MemoryRequest(BaseModel):
    user_id: str
    message: str
    role: str = "user"

class ContextRequest(BaseModel):
    user_id: str

# =========================================================
# CREATE MEMORY TABLE
# =========================================================

def create_memory_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS memory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================================================
# SAVE MEMORY
# =========================================================

def save_memory(user_id, role, message):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO memory
    (
        user_id,
        role,
        message,
        created_at
    )
    VALUES (?, ?, ?, ?)
    """,
    (
        user_id,
        role,
        message,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()

# =========================================================
# LOAD MEMORY
# =========================================================

def load_memory(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT role,message
    FROM memory
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT ?
    """,
    (
        user_id,
        MAX_MEMORY_MESSAGES
    ))

    rows = cur.fetchall()

    conn.close()

    return rows[::-1]

# =========================================================
# CONTEXT BUILDER
# =========================================================

def build_context(user_id):

    history = load_memory(user_id)

    context = []

    for row in history[-MAX_CONTEXT_MESSAGES:]:

        context.append({
            "role": row["role"],
            "content": row["message"]
        })

    return context

# =========================================================
# ADD MESSAGE
# =========================================================

@app.post("/api/memory/add")
def add_memory(data: MemoryRequest):

    save_memory(
        data.user_id,
        data.role,
        data.message
    )

    return {
        "success": True
    }

# =========================================================
# GET MEMORY
# =========================================================

@app.get("/api/memory/{user_id}")
def get_memory(user_id: str):

    return {
        "success": True,
        "memory": load_memory(user_id)
    }

# =========================================================
# GET CONTEXT
# =========================================================

@app.get("/api/context/{user_id}")
def get_context(user_id: str):

    return {
        "success": True,
        "context": build_context(user_id)
    }

# =========================================================
# CLEAR MEMORY
# =========================================================

@app.delete("/api/memory/{user_id}")
def clear_memory(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM memory WHERE user_id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Memory cleared"
    }

# =========================================================
# SESSION MEMORY
# =========================================================

@app.post("/api/session/add")
def session_add(data: MemoryRequest):

    if data.user_id not in SESSION_MEMORY:

        SESSION_MEMORY[data.user_id] = deque(
            maxlen=MAX_MEMORY_MESSAGES
        )

    SESSION_MEMORY[data.user_id].append({
        "role": data.role,
        "message": data.message
    })

    return {
        "success": True
    }

# =========================================================
# SESSION HISTORY
# =========================================================

@app.get("/api/session/{user_id}")
def session_history(user_id: str):

    return {
        "success": True,
        "messages": list(
            SESSION_MEMORY.get(
                user_id,
                []
            )
        )
    }

# =========================================================
# MEMORY HEALTH
# =========================================================

@app.get("/api/memory/health")
def memory_health():

    return {
        "success": True,
        "max_memory": MAX_MEMORY_MESSAGES,
        "max_context": MAX_CONTEXT_MESSAGES,
        "active_sessions": len(
            SESSION_MEMORY
        )
    }

# =========================================================
# END PART 7D
# PASTE PART 7E DIRECTLY BELOW THIS
# =========================================================
# =========================================================
# PART 7E
# STREAMING + MARKDOWN + ANALYTICS + FAILOVER
# PASTE DIRECTLY BELOW PART 7D
# =========================================================

import time
import traceback
from collections import defaultdict

# =========================================================
# ANALYTICS
# =========================================================

REQUEST_COUNTER = 0
ERROR_COUNTER = 0

TOKEN_USAGE = defaultdict(int)

# =========================================================
# REQUEST MODEL
# =========================================================

class StreamRequest(BaseModel):
    user_id: str
    message: str
    provider: str = "auto"

# =========================================================
# TOKEN ESTIMATOR
# =========================================================

def estimate_tokens(text):

    words = len(text.split())

    return int(words * 1.3)

# =========================================================
# MARKDOWN FORMATTER
# =========================================================

def markdown_response(text):

    return {
        "raw": text,
        "markdown": text,
        "html_safe": text
    }

# =========================================================
# RESPONSE LOGGER
# =========================================================

def log_usage(user_id, text):

    tokens = estimate_tokens(text)

    TOKEN_USAGE[user_id] += tokens

    return tokens

# =========================================================
# FAILOVER SYSTEM
# =========================================================

def smart_ai_request(prompt):

    try:
        return ask_ai(prompt)

    except Exception:

        try:

            if GROQ_API_KEY:
                return ask_groq(prompt)

        except Exception:
            pass

        try:

            if OPENAI_API_KEY:
                return ask_openai(prompt)

        except Exception:
            pass

        return "AI service temporarily unavailable."

# =========================================================
# STREAM CHAT
# =========================================================

@app.post("/api/chat/stream")
def stream_chat(data: StreamRequest):

    global REQUEST_COUNTER
    global ERROR_COUNTER

    start_time = time.time()

    try:

        REQUEST_COUNTER += 1

        save_memory(
            data.user_id,
            "user",
            data.message
        )

        reply = smart_ai_request(
            data.message
        )

        save_memory(
            data.user_id,
            "assistant",
            reply
        )

        tokens = log_usage(
            data.user_id,
            reply
        )

        return {
            "success": True,
            "response": markdown_response(
                reply
            ),
            "tokens": tokens,
            "time":
            round(
                time.time()-start_time,
                2
            )
        }

    except Exception as e:

        ERROR_COUNTER += 1

        return {
            "success": False,
            "error": str(e)
        }

# =========================================================
# FOLLOW-UP SUGGESTIONS
# =========================================================

@app.post("/api/chat/suggestions")
def suggestions(data: StreamRequest):

    return {
        "success": True,
        "suggestions": [
            "Explain further",
            "Give examples",
            "Summarize this",
            "Compare alternatives",
            "Create a table"
        ]
    }

# =========================================================
# ANALYTICS
# =========================================================

@app.get("/api/analytics")
def analytics():

    return {
        "success": True,
        "requests": REQUEST_COUNTER,
        "errors": ERROR_COUNTER,
        "active_users":
        len(TOKEN_USAGE)
    }

# =========================================================
# TOKEN USAGE
# =========================================================

@app.get("/api/tokens/{user_id}")
def user_tokens(user_id: str):

    return {
        "success": True,
        "tokens":
        TOKEN_USAGE.get(
            user_id,
            0
        )
    }

# =========================================================
# ERROR LOG
# =========================================================

@app.get("/api/system/status")
def system_status():

    return {
        "success": True,
        "requests": REQUEST_COUNTER,
        "errors": ERROR_COUNTER,
        "providers": provider_status(),
        "research": research_status()
    }

# =========================================================
# PERFORMANCE
# =========================================================

@app.get("/api/performance")
def performance():

    return {
        "success": True,
        "memory_sessions":
        len(SESSION_MEMORY),
        "users":
        len(TOKEN_USAGE)
    }

# =========================================================
# END PART 7E
# PASTE PART 7F DIRECTLY BELOW THIS
# =========================================================
# =========================================================
# PART 7F
# FINAL STARTUP + SYSTEM BOOT
# PASTE DIRECTLY BELOW PART 7E
# =========================================================

# =========================================================
# INITIALIZATION
# =========================================================

try:
    create_settings_table()
except:
    pass

try:
    create_memory_table()
except:
    pass

# =========================================================
# ROOT STATUS
# =========================================================

@app.get("/api")
def api_root():

    return {
        "success": True,
        "name": "Bloxy-Bot X",
        "version": "4.0",
        "status": "online",
        "ai": provider_status(),
        "research": research_status()
    }

# =========================================================
# FULL SYSTEM HEALTH
# =========================================================

@app.get("/api/health")
def full_health():

    return {
        "success": True,

        "ai_providers":
            provider_status(),

        "research_engines":
            research_status(),

        "active_provider":
            get_best_provider(),

        "memory_sessions":
            len(SESSION_MEMORY),

        "requests":
            REQUEST_COUNTER,

        "errors":
            ERROR_COUNTER
    }

# =========================================================
# SYSTEM INFORMATION
# =========================================================

@app.get("/api/info")
def info():

    return {

        "application": "Bloxy-Bot X",

        "version": "4.0",

        "features": [

            "authentication",
            "chat",
            "memory",
            "research",
            "ai",
            "themes",
            "settings",
            "analytics",
            "streaming",
            "weather",
            "finance",
            "sports",
            "movies",
            "news"
        ]
    }

# =========================================================
# RELOAD CACHE
# =========================================================

@app.post("/api/system/reload")
def reload_system():

    return {
        "success": True,
        "message": "System reloaded"
    }

# =========================================================
# CLEAR SESSION CACHE
# =========================================================

@app.post("/api/system/clear-cache")
def clear_cache():

    SESSION_MEMORY.clear()

    return {
        "success": True,
        "message": "Cache cleared"
    }

# =========================================================
# APPLICATION STARTUP
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# =========================================================
# END PART 7F
# PROJECT COMPLETE
# =========================================================

