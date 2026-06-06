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
# PART 5A
# COMPLETE UI FOUNDATION
# =========================================================

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Bloxy-Bot X</title>

<link
rel="stylesheet"
href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

body{
    font-family:Arial,sans-serif;
    background:#0f1117;
    color:white;
    height:100vh;
    overflow:hidden;
}

.app{
    display:flex;
    height:100vh;
}

.sidebar{
    width:280px;
    background:#171923;
    border-right:1px solid #2a2d36;
    display:flex;
    flex-direction:column;
}

.logo{
    padding:20px;
    font-size:22px;
    font-weight:bold;
    border-bottom:1px solid #2a2d36;
}

.new-chat{
    margin:15px;
    padding:12px;
    border:none;
    border-radius:10px;
    background:#2563eb;
    color:white;
    cursor:pointer;
}

.search-box{
    margin:0 15px 15px;
}

.search-box input{
    width:100%;
    padding:10px;
    border:none;
    border-radius:8px;
    background:#222733;
    color:white;
}

.conversations{
    flex:1;
    overflow-y:auto;
}

.chat-item{
    padding:12px 15px;
    cursor:pointer;
    border-bottom:1px solid #222;
}

.chat-item:hover{
    background:#222733;
}

.bottom-menu{
    border-top:1px solid #2a2d36;
    padding:15px;
}

.menu-btn{
    width:100%;
    margin-bottom:10px;
    padding:10px;
    border:none;
    border-radius:8px;
    background:#222733;
    color:white;
    cursor:pointer;
}

.main{
    flex:1;
    display:flex;
    flex-direction:column;
}

.topbar{
    height:60px;
    border-bottom:1px solid #2a2d36;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 20px;
}

.chat-area{
    flex:1;
    overflow-y:auto;
    padding:20px;
}

.welcome{
    max-width:800px;
    margin:auto;
    text-align:center;
    padding-top:100px;
}

.input-area{
    padding:20px;
    border-top:1px solid #2a2d36;
}

.input-wrapper{
    max-width:900px;
    margin:auto;
    display:flex;
    gap:10px;
}

.input-wrapper input{
    flex:1;
    padding:14px;
    border:none;
    border-radius:12px;
    background:#222733;
    color:white;
}

.send-btn{
    width:55px;
    border:none;
    border-radius:12px;
    background:#2563eb;
    color:white;
    cursor:pointer;
}

.settings-modal{
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,.7);
}

.settings-content{
    width:600px;
    max-width:95%;
    margin:50px auto;
    background:#171923;
    border-radius:15px;
    padding:25px;
}

.settings-title{
    font-size:22px;
    margin-bottom:20px;
}

.close-btn{
    margin-top:20px;
    padding:10px 15px;
    border:none;
    border-radius:8px;
    background:#ef4444;
    color:white;
    cursor:pointer;
}

@media(max-width:768px){

.sidebar{
    width:80px;
}

.logo{
    font-size:16px;
}

.search-box{
    display:none;
}

}

</style>

</head>

<body>

<div class="app">

<div class="sidebar">

<div class="logo">
🤖 Bloxy-Bot X
</div>

<button
class="new-chat"
onclick="newChat()">
+ New Chat
</button>

<div class="search-box">
<input
type="text"
placeholder="Search chats">
</div>

<div
id="conversationList"
class="conversations">

<div class="chat-item">
Welcome Chat
</div>

</div>

<div class="bottom-menu">

<button
class="menu-btn"
onclick="openSettings()">
⚙ Settings
</button>

<button
class="menu-btn">
👤 Account
</button>

</div>

</div>

<div class="main">

<div class="topbar">

<div>
Bloxy-Bot X
</div>

<div>
GPT Model
</div>

</div>

<div
id="chatArea"
class="chat-area">

<div class="welcome">

<h1>
Welcome to Bloxy-Bot X
</h1>

<br>

<p>
Ask anything...
</p>

</div>

</div>

<div class="input-area">

<div class="input-wrapper">

<input
id="messageInput"
placeholder="Message Bloxy-Bot X">

<button
class="send-btn"
onclick="sendMessage()">
➤
</button>

</div>

</div>

</div>

</div>

<div
id="settingsModal"
class="settings-modal">

<div class="settings-content">

<div class="settings-title">
Settings
</div>

<p>Theme</p>
<br>

<select>
<option>Dark</option>
<option>Light</option>
<option>Ocean</option>
<option>Midnight</option>
</select>

<br><br>

<p>Model</p>
<br>

<select>
<option>OpenRouter</option>
<option>OpenAI</option>
<option>Groq</option>
<option>Kimi</option>
</select>

<br><br>

<button
class="close-btn"
onclick="closeSettings()">
Close
</button>

</div>

</div>

<script>

function openSettings(){
    document
    .getElementById(
        "settingsModal"
    ).style.display="block";
}

function closeSettings(){
    document
    .getElementById(
        "settingsModal"
    ).style.display="none";
}

function newChat(){

    const list =
    document.getElementById(
        "conversationList"
    );

    list.innerHTML +=
    '<div class="chat-item">New Chat</div>';
}

function sendMessage(){

    const input =
    document.getElementById(
        "messageInput"
    );

    const text =
    input.value.trim();

    if(!text){
        return;
    }

    const area =
    document.getElementById(
        "chatArea"
    );

    area.innerHTML +=
    '<div style="text-align:right;margin:10px;"><b>You:</b> '
    + text +
    '</div>';

    input.value = "";
}

</script>

</body>
</html>
"""


# =========================================================
# PART 5B
# ADVANCED CHAT UI FEATURES
# PASTE BELOW PART 5A
# =========================================================

class MessageBubble:

    @staticmethod
    def user(content):
        return f"""
        <div
        style="
        display:flex;
        justify-content:flex-end;
        margin:15px 0;
        ">
            <div
            style="
            max-width:75%;
            background:#2563eb;
            padding:12px;
            border-radius:15px;
            ">
                {content}
            </div>
        </div>
        """

    @staticmethod
    def assistant(content):
        return f"""
        <div
        style="
        display:flex;
        justify-content:flex-start;
        margin:15px 0;
        ">
            <div
            style="
            max-width:75%;
            background:#1e293b;
            padding:12px;
            border-radius:15px;
            ">
                {content}
            </div>
        </div>
        """

# =========================================================
# CHAT STREAMING PLACEHOLDER
# =========================================================

@app.get("/api/ui/config")
def ui_config():
    return {
        "success": True,
        "features": {
            "markdown": True,
            "code_blocks": True,
            "copy_button": True,
            "attachments": True,
            "voice_input": True,
            "voice_output": True,
            "streaming": True
        }
    }

# =========================================================
# MARKDOWN SUPPORT
# =========================================================

MARKDOWN_JS = """
<script src='https://cdn.jsdelivr.net/npm/marked/marked.min.js'></script>
"""

# =========================================================
# CODE HIGHLIGHTING
# =========================================================

HIGHLIGHT_JS = """
<link
rel='stylesheet'
href='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css'>

<script src='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js'></script>

<script>
hljs.highlightAll();
</script>
"""

# =========================================================
# CHAT ACTIONS
# =========================================================

@app.get("/api/chat/actions")
def chat_actions():
    return {
        "success": True,
        "actions": [
            "copy",
            "edit",
            "regenerate",
            "delete",
            "share"
        ]
    }

# =========================================================
# TYPING INDICATOR
# =========================================================

@app.get("/api/chat/typing")
def typing_indicator():
    return {
        "success": True,
        "typing": True,
        "message": "AI is thinking..."
    }

# =========================================================
# AUTO SCROLL CONFIG
# =========================================================

@app.get("/api/chat/autoscroll")
def autoscroll():
    return {
        "success": True,
        "enabled": True
    }

# =========================================================
# MESSAGE TIMESTAMPS
# =========================================================

@app.get("/api/chat/timestamps")
def timestamps():
    return {
        "success": True,
        "format": "HH:MM"
    }

# =========================================================
# COPY CODE FEATURE
# =========================================================

COPY_CODE_JS = """
<script>

function copyCode(btn){

    const code =
    btn.previousElementSibling.innerText;

    navigator.clipboard.writeText(code);

    btn.innerText = "Copied";

    setTimeout(() => {

        btn.innerText = "Copy";

    },1500);
}

</script>
"""

# =========================================================
# MESSAGE SEARCH
# =========================================================

@app.get("/api/chat/search/{conversation_id}")
def search_messages(
    conversation_id: str,
    query: str = ""
):
    return {
        "success": True,
        "conversation_id": conversation_id,
        "query": query
    }

# =========================================================
# PINNED MESSAGES
# =========================================================

@app.get("/api/chat/pinned/{conversation_id}")
def pinned_messages(
    conversation_id: str
):
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": []
    }

# =========================================================
# CHAT EXPORT
# =========================================================

@app.get("/api/chat/export/{conversation_id}")
def export_chat(
    conversation_id: str
):
    return {
        "success": True,
        "conversation_id": conversation_id,
        "format": "json"
    }

# =========================================================
# READY FOR PART 5C
# Conversation Management
# Sidebar Features
# Rename/Delete/Search Chats
# =========================================================


# =========================================================
# PART 5C
# CONVERSATION MANAGEMENT
# PASTE BELOW PART 5B
# =========================================================

class ConversationRequest(BaseModel):
    user_id: str
    title: str

# =========================================================
# CREATE CONVERSATION
# =========================================================

@app.post("/api/chat/new")
def create_new_chat(
    data: ConversationRequest
):

    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversations
        VALUES(?,?,?,?,?)
        """,
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

# =========================================================
# GET CONVERSATIONS
# =========================================================

@app.get("/api/chat/list/{user_id}")
def chat_list(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=?
        ORDER BY updated_at DESC
        """,
        (user_id,)
    )

    rows = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversations": rows
    }

# =========================================================
# RENAME CHAT
# =========================================================

class RenameChatRequest(BaseModel):
    conversation_id: str
    title: str

@app.put("/api/chat/rename")
def rename_chat(
    data: RenameChatRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE conversations
        SET title=?,
        updated_at=?
        WHERE id=?
        """,
        (
            data.title,
            now(),
            data.conversation_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# DELETE CHAT
# =========================================================

@app.delete(
"/api/chat/delete/{conversation_id}"
)
def delete_chat(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    cur.execute(
        """
        DELETE FROM conversations
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# SEARCH CHATS
# =========================================================

@app.get("/api/chat/search")
def search_chats(
    user_id: str,
    query: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=?
        AND title LIKE ?
        """,
        (
            user_id,
            f"%{query}%"
        )
    )

    results = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "results": results
    }

# =========================================================
# FAVORITE CHATS
# =========================================================

def create_favorites_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites(
        conversation_id TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_favorites_table()

@app.post(
"/api/chat/favorite/{conversation_id}"
)
def favorite_chat(
    conversation_id: str,
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE
        INTO favorites
        VALUES(?,?,?)
        """,
        (
            conversation_id,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# CHAT ARCHIVE
# =========================================================

def create_archive_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS archived_chats(
        conversation_id TEXT PRIMARY KEY,
        user_id TEXT,
        archived_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_archive_table()

@app.post(
"/api/chat/archive/{conversation_id}"
)
def archive_chat(
    conversation_id: str,
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE
        INTO archived_chats
        VALUES(?,?,?)
        """,
        (
            conversation_id,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# CHAT STATISTICS
# =========================================================

@app.get("/api/chat/stats/{user_id}")
def chat_stats(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM conversations
        WHERE user_id=?
        """,
        (user_id,)
    )

    total = cur.fetchone()[0]
  

    conn.close()

    return {
        "success": True,
        "total_chats": total
    }

# =========================================================
# END OF PART 5C
# NEXT = PART 5D
# SETTINGS PANEL + USER PREFERENCES UI
# =========================================================


# =========================================================
# PART 5D
# SETTINGS PANEL + USER PREFERENCES UI
# PASTE BELOW PART 5C
# =========================================================

class SettingsRequest(BaseModel):
    user_id: str
    theme: str
    ai_model: str
    temperature: float

# =========================================================
# SETTINGS TABLE
# =========================================================

def create_ui_settings_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ui_settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        ai_model TEXT,
        temperature REAL,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_ui_settings_table()

# =========================================================
# SAVE SETTINGS
# =========================================================

@app.post("/api/ui/settings/save")
def save_ui_settings(
    data: SettingsRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO ui_settings
        VALUES(?,?,?,?,?)
        """,
        (
            data.user_id,
            data.theme,
            data.ai_model,
            data.temperature,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# LOAD SETTINGS
# =========================================================

@app.get("/api/ui/settings/{user_id}")
def load_ui_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM ui_settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "settings":
        dict(row) if row else None
    }

# =========================================================
# AVAILABLE THEMES
# =========================================================

@app.get("/api/ui/themes")
def themes():

    return {
        "success": True,
        "themes":[
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

# =========================================================
# AVAILABLE MODELS
# =========================================================

@app.get("/api/ui/models")
def models():

    return {
        "success": True,
        "models":[
            "openrouter",
            "openai",
            "groq",
            "kimi",
            "deepseek",
            "claude"
        ]
    }

# =========================================================
# RESET SETTINGS
# =========================================================

@app.post("/api/ui/settings/reset/{user_id}")
def reset_ui_settings(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM ui_settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# SIDEBAR SETTINGS DATA
# =========================================================

@app.get("/api/ui/sidebar")
def sidebar_settings():

    return {
        "success": True,
        "items":[
            "New Chat",
            "Search",
            "Favorites",
            "Archived",
            "Settings",
            "Account"
        ]
    }

# =========================================================
# END OF PART 5D
# NEXT = PART 5E
# FILE UPLOADS + ATTACHMENTS
# =========================================================


# =========================================================
# PART 5E
# FILE UPLOADS + ATTACHMENTS
# PASTE BELOW PART 5D
# =========================================================

class FileUploadRequest(BaseModel):
    conversation_id: str
    filename: str
    file_type: str
    file_size: int

# =========================================================
# ATTACHMENTS TABLE
# =========================================================

def create_attachments_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attachments(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        filename TEXT,
        file_type TEXT,
        file_size INTEGER,
        uploaded_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_attachments_table()

# =========================================================
# UPLOAD FILE
# =========================================================

@app.post("/api/files/upload")
def upload_file(
    data: FileUploadRequest
):

    file_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO attachments
        VALUES(?,?,?,?,?,?)
        """,
        (
            file_id,
            data.conversation_id,
            data.filename,
            data.file_type,
            data.file_size,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "file_id": file_id
    }

# =========================================================
# GET FILES
# =========================================================

@app.get("/api/files/{conversation_id}")
def get_files(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM attachments
        WHERE conversation_id=?
        ORDER BY uploaded_at DESC
        """,
        (conversation_id,)
    )

    files = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "files": files
    }

# =========================================================
# DELETE FILE
# =========================================================

@app.delete("/api/files/delete/{file_id}")
def delete_file(file_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM attachments
        WHERE id=?
        """,
        (file_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# FILE TYPES
# =========================================================

@app.get("/api/files/types")
def supported_file_types():

    return {
        "success": True,
        "types":[
            "pdf",
            "docx",
            "txt",
            "csv",
            "xlsx",
            "png",
            "jpg",
            "jpeg",
            "gif",
            "webp",
            "mp3",
            "wav",
            "mp4"
        ]
    }

# =========================================================
# STORAGE INFO
# =========================================================

@app.get("/api/files/storage")
def storage_info():

    return {
        "success": True,
        "max_upload_mb": 100,
        "allowed": True
    }

# =========================================================
# END OF PART 5E
# NEXT = PART 5F
# VOICE + SPEECH FEATURES
# =========================================================

# =========================================================
# PART 5F
# RESERVED FOR FUTURE FEATURES
# =========================================================

@app.get("/api/features")
def feature_status():

    return {
        "success": True,
        "enabled": {
            "chat": True,
            "conversations": True,
            "settings": True,
            "themes": True,
            "attachments": True,
            "voice": False,
            "speech_to_text": False,
            "text_to_speech": False
        }
    }

# =========================================================
# END OF PART 5F
# NEXT = PART 5G
# IMAGE GENERATION + IMAGE UPLOADS
# =========================================================


# =========================================================
# PART 5G
# CHAT UTILITIES
# PASTE BELOW PART 5F
# =========================================================

# =========================================================
# BOOKMARKED MESSAGES
# =========================================================

def create_bookmarks_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        message_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_bookmarks_table()

@app.post("/api/bookmarks/add")
def add_bookmark(
    user_id: str,
    message_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO bookmarks
        VALUES(?,?,?,?)
        """,
        (
            generate_id(),
            user_id,
            message_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {"success": True}

# =========================================================
# RECENT SEARCHES
# =========================================================

def create_search_history_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS search_history(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        query TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_search_history_table()

@app.get("/api/search/history/{user_id}")
def search_history(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM search_history
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (user_id,)
    )

    results = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "history": results
    }

# =========================================================
# CLEAR CHAT
# =========================================================

@app.delete(
"/api/chat/clear/{conversation_id}"
)
def clear_chat(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# CHAT SHARING
# =========================================================

@app.get(
"/api/chat/share/{conversation_id}"
)
def share_chat(
    conversation_id: str
):

    return {
        "success": True,
        "share_url":
        f"/shared/{conversation_id}"
    }

# =========================================================
# CHAT SUMMARY
# =========================================================

@app.get(
"/api/chat/summary/{conversation_id}"
)
def chat_summary(
    conversation_id: str
):

    return {
        "success": True,
        "summary":
        "Conversation summary placeholder"
    }

# =========================================================
# USER DASHBOARD
# =========================================================

@app.get("/api/dashboard/{user_id}")
def dashboard(
    user_id: str
):

    return {
        "success": True,
        "user_id": user_id,
        "features": [
            "recent_chats",
            "favorites",
            "bookmarks",
            "settings"
        ]
    }

# =========================================================
# END OF PART 5G
# NEXT = PART 5H
# WEB SEARCH + EXTERNAL TOOLS
# =========================================================


# =========================================================
# PART 5H
# WEB SEARCH + EXTERNAL TOOLS
# PASTE BELOW PART 5G
# =========================================================

import os

# =========================================================
# API PROVIDERS
# =========================================================

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
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")

# =========================================================
# TOOL REGISTRY
# =========================================================

@app.get("/api/tools")
def available_tools():

    return {
        "success": True,
        "tools": {
            "ai": True,
            "web_search": True,
            "news": True,
            "weather": True,
            "finance": True,
            "movies": True,
            "sports": True,
            "calculator": True
        }
    }

# =========================================================
# WEB SEARCH
# =========================================================

@app.get("/api/search")
def web_search(query: str):

    return {
        "success": True,
        "provider": "tavily/exa/firecrawl",
        "query": query,
        "results": []
    }

# =========================================================
# NEWS SEARCH
# =========================================================

@app.get("/api/news")
def news(query: str):

    return {
        "success": True,
        "query": query,
        "provider": "newsapi/gnews/guardian",
        "articles": []
    }

# =========================================================
# WEATHER
# =========================================================

@app.get("/api/weather")
def weather(city: str):

    return {
        "success": True,
        "city": city,
        "provider": "openweather"
    }

# =========================================================
# FINANCE
# =========================================================

@app.get("/api/stocks")
def stocks(symbol: str):

    return {
        "success": True,
        "symbol": symbol,
        "provider": "alphavantage/finnhub"
    }

# =========================================================
# SPORTS
# =========================================================

@app.get("/api/sports")
def sports(team: str):

    return {
        "success": True,
        "team": team,
        "provider":
        "sportmonks/sportradar/thesportsdb"
    }

# =========================================================
# MOVIES
# =========================================================

@app.get("/api/movies")
def movies(title: str):

    return {
        "success": True,
        "title": title,
        "provider": "tmdb"
    }

# =========================================================
# CALCULATOR
# =========================================================

@app.get("/api/calculate")
def calculate(a: float, b: float):

    return {
        "success": True,
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None
    }

# =========================================================
# FEATURE FLAGS
# =========================================================

@app.get("/api/capabilities")
def capabilities():

    return {
        "success": True,
        "chat": True,
        "attachments": True,
        "web_search": True,
        "news": True,
        "weather": True,
        "finance": True,
        "sports": True,
        "movies": True,
        "settings": True
    }

# =========================================================
# END OF PART 5H
# NEXT = PART 5I
# NOTIFICATIONS + ALERTS
# =========================================================


# =========================================================
# PART 5I
# NOTIFICATIONS + ALERTS
# PASTE BELOW PART 5H
# =========================================================

class NotificationRequest(BaseModel):
    user_id: str
    title: str
    message: str

# =========================================================
# NOTIFICATIONS TABLE
# =========================================================

def create_notifications_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_notifications_table()

# =========================================================
# CREATE NOTIFICATION
# =========================================================

@app.post("/api/notifications/create")
def create_notification(
    data: NotificationRequest
):

    notification_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO notifications
        VALUES(?,?,?,?,?,?)
        """,
        (
            notification_id,
            data.user_id,
            data.title,
            data.message,
            0,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "notification_id": notification_id
    }

# =========================================================
# GET NOTIFICATIONS
# =========================================================

@app.get("/api/notifications/{user_id}")
def get_notifications(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM notifications
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    notifications = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "notifications": notifications
    }

# =========================================================
# MARK AS READ
# =========================================================

@app.put(
"/api/notifications/read/{notification_id}"
)
def mark_notification_read(
    notification_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE notifications
        SET is_read=1
        WHERE id=?
        """,
        (notification_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# DELETE NOTIFICATION
# =========================================================

@app.delete(
"/api/notifications/delete/{notification_id}"
)
def delete_notification(
    notification_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM notifications
        WHERE id=?
        """,
        (notification_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# UNREAD COUNT
# =========================================================

@app.get(
"/api/notifications/unread/{user_id}"
)
def unread_notifications(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM notifications
        WHERE user_id=?
        AND is_read=0
        """,
        (user_id,)
    )

    count = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "unread": count
    }

# =========================================================
# SYSTEM ALERTS
# =========================================================

@app.get("/api/system/alerts")
def system_alerts():

    return {
        "success": True,
        "alerts": [
            {
                "type": "info",
                "message": "System operational"
            }
        ]
    }

# =========================================================
# END OF PART 5I
# NEXT = PART 5J
# ADMIN PANEL
# =========================================================


# =========================================================
# PART 5J
# ADMIN PANEL
# PASTE BELOW PART 5I
# =========================================================

# =========================================================
# ADMIN USERS TABLE
# =========================================================

def create_admin_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        user_id TEXT PRIMARY KEY,
        role TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_admin_table()

# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.get("/api/admin/dashboard")
def admin_dashboard():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM conversations"
    )
    conversations = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM messages"
    )
    messages = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "stats": {
            "users": users,
            "conversations": conversations,
            "messages": messages
        }
    }

# =========================================================
# GET ALL USERS
# =========================================================

@app.get("/api/admin/users")
def admin_users():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT
    id,
    username,
    email,
    created_at
    FROM users
    ORDER BY created_at DESC
    """)

    users = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "users": users
    }

# =========================================================
# DELETE USER
# =========================================================

@app.delete("/api/admin/user/{user_id}")
def admin_delete_user(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# SYSTEM STATUS
# =========================================================

@app.get("/api/admin/status")
def admin_status():

    return {
        "success": True,
        "server": "online",
        "database": "connected",
        "api": "running"
    }

# =========================================================
# END OF PART 5J
# NEXT = PART 5K
# ANALYTICS + USAGE STATISTICS
# =========================================================


# =========================================================
# PART 5K
# ANALYTICS + USAGE STATISTICS
# PASTE BELOW PART 5J
# =========================================================

# =========================================================
# ANALYTICS TABLE
# =========================================================

def create_analytics_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        event_type TEXT,
        event_value TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_analytics_table()

# =========================================================
# LOG EVENT
# =========================================================

@app.post("/api/analytics/log")
def log_event(
    user_id: str,
    event_type: str,
    event_value: str = ""
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO analytics
        VALUES(?,?,?,?,?)
        """,
        (
            generate_id(),
            user_id,
            event_type,
            event_value,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# USER STATS
# =========================================================

@app.get("/api/analytics/user/{user_id}")
def user_analytics(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM conversations
        WHERE user_id=?
        """,
        (user_id,)
    )

    conversations = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM analytics
        WHERE user_id=?
        """,
        (user_id,)
    )

    events = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "stats": {
            "conversations": conversations,
            "events": events
        }
    }

# =========================================================
# PLATFORM STATS
# =========================================================

@app.get("/api/analytics/platform")
def platform_analytics():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM conversations"
    )
    conversations = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM messages"
    )
    messages = cur.fetchone()[0]

    conn.close()

    return {
        "success": True,
        "users": users,
        "conversations": conversations,
        "messages": messages
    }

# =========================================================
# MOST USED MODELS
# =========================================================

@app.get("/api/analytics/models")
def model_analytics():

    return {
        "success": True,
        "models": [
            "openrouter",
            "openai",
            "groq",
            "kimi"
        ]
    }

# =========================================================
# DAILY ACTIVITY
# =========================================================

@app.get("/api/analytics/activity")
def activity():

    return {
        "success": True,
        "daily_activity": []
    }

# =========================================================
# END OF PART 5K
# NEXT = PART 5L
# FRONTEND INTEGRATION + UI FINALIZATION
# =========================================================


# =========================================================
# PART 5L
# FRONTEND INTEGRATION + UI FINALIZATION
# PASTE BELOW PART 5K
# =========================================================

# =========================================================
# UI SETTINGS TABLE
# =========================================================

def create_ui_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ui_settings(
        user_id TEXT PRIMARY KEY,
        sidebar_open INTEGER DEFAULT 1,
        compact_mode INTEGER DEFAULT 0,
        show_timestamps INTEGER DEFAULT 1,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_ui_table()

# =========================================================
# SAVE UI SETTINGS
# =========================================================

class UISettingsRequest(BaseModel):
    user_id: str
    sidebar_open: bool
    compact_mode: bool
    show_timestamps: bool

@app.post("/api/ui/save")
def save_ui(data: UISettingsRequest):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO ui_settings
        VALUES(?,?,?,?,?)
        """,
        (
            data.user_id,
            int(data.sidebar_open),
            int(data.compact_mode),
            int(data.show_timestamps),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# LOAD UI SETTINGS
# =========================================================

@app.get("/api/ui/{user_id}")
def load_ui(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM ui_settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "settings":
        dict(row) if row else None
    }

# =========================================================
# SIDEBAR DATA
# =========================================================

@app.get("/api/sidebar/{user_id}")
def sidebar_data(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=?
        ORDER BY updated_at DESC
        LIMIT 50
        """,
        (user_id,)
    )

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
# QUICK ACTIONS
# =========================================================

@app.get("/api/ui/actions")
def quick_actions():

    return {
        "success": True,
        "actions": [
            "new_chat",
            "search",
            "settings",
            "clear_chat",
            "export_chat",
            "delete_chat"
        ]
    }

# =========================================================
# APPLICATION VERSION
# =========================================================

@app.get("/api/version")
def version():

    return {
        "success": True,
        "app": "Bloxy-Bot X",
        "version": "1.0.0"
    }

# =========================================================
# UI STATUS
# =========================================================

@app.get("/api/ui/status")
def ui_status():

    return {
        "success": True,
        "features": {
            "sidebar": True,
            "themes": True,
            "attachments": True,
            "notifications": True,
            "search": True,
            "settings": True,
            "drafts": False
        }
    }

# =========================================================
# END OF PART 5L
# NEXT = PART 5M
# DRAFT SAVING + AUTO RECOVERY
# =========================================================


# =========================================================
# PART 5M
# DRAFT SAVING + AUTO RECOVERY
# PASTE BELOW PART 5L
# =========================================================

# =========================================================
# DRAFTS TABLE
# =========================================================

def create_drafts_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drafts(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        conversation_id TEXT,
        content TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_drafts_table()

# =========================================================
# DRAFT MODEL
# =========================================================

class DraftRequest(BaseModel):
    user_id: str
    conversation_id: str
    content: str

# =========================================================
# SAVE DRAFT
# =========================================================

@app.post("/api/drafts/save")
def save_draft(data: DraftRequest):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO drafts
        (
            id,
            user_id,
            conversation_id,
            content,
            updated_at
        )
        VALUES(?,?,?,?,?)
        """,
        (
            data.conversation_id,
            data.user_id,
            data.conversation_id,
            data.content,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Draft saved"
    }

# =========================================================
# LOAD DRAFT
# =========================================================

@app.get("/api/drafts/{conversation_id}")
def load_draft(conversation_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM drafts
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    draft = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "draft":
        dict(draft) if draft else None
    }

# =========================================================
# DELETE DRAFT
# =========================================================

@app.delete("/api/drafts/{conversation_id}")
def delete_draft(conversation_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM drafts
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

# =========================================================
# GET USER DRAFTS
# =========================================================

@app.get("/api/drafts/user/{user_id}")
def get_user_drafts(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM drafts
        WHERE user_id=?
        ORDER BY updated_at DESC
        """,
        (user_id,)
    )

    drafts = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "drafts": drafts
    }

# =========================================================
# AUTO SAVE STATUS
# =========================================================

@app.get("/api/drafts/autosave")
def autosave_status():

    return {
        "success": True,
        "enabled": True,
        "interval_seconds": 10
    }

# =========================================================
# RECOVER UNSENT MESSAGE
# =========================================================

@app.get(
"/api/drafts/recover/{conversation_id}"
)
def recover_draft(conversation_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT content
        FROM drafts
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    draft = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "recovered":
        draft["content"] if draft else ""
    }

# =========================================================
# END OF PART 5M
# PART 5 COMPLETE
#
# NEXT:
# PART 6 = SETTINGS SYSTEM
# PART 7 = AI ENGINE + API PROVIDERS
# =========================================================


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
# AI ENGINE + API PROVIDERS + MODEL ROUTER
# PASTE BELOW PART 6F
# =========================================================

import os
import requests

# =========================================================
# API KEYS
# =========================================================

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
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# =========================================================
# AI REQUEST MODEL
# =========================================================

class AIChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str

# =========================================================
# AI MEMORY TABLE
# =========================================================

def create_ai_memory_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_memory(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_ai_memory_table()

# =========================================================
# LOAD USER SETTINGS
# =========================================================

def get_user_settings(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return dict(row) if row else None

# =========================================================
# SAVE MEMORY
# =========================================================

def save_memory(
    user_id,
    conversation_id,
    role,
    content
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ai_memory
        VALUES(?,?,?,?,?,?)
        """,
        (
            generate_id(),
            user_id,
            conversation_id,
            role,
            content,
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# LOAD MEMORY
# =========================================================

def load_memory(conversation_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role,content
        FROM ai_memory
        WHERE conversation_id=?
        ORDER BY created_at ASC
        LIMIT 30
        """,
        (conversation_id,)
    )

    data = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return data

# =========================================================
# OPENROUTER ENGINE
# =========================================================

def ask_openrouter(
    model,
    messages
):

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization":
            f"Bearer {OPENROUTER_API_KEY}"
        },
        json={
            "model": model,
            "messages": messages
        },
        timeout=120
    )

    return response.json()

# =========================================================
# MODEL ROUTER
# =========================================================

def choose_model(settings):

    model = settings.get(
        "ai_model",
        "openrouter"
    )

    mapping = {
        "openrouter":
        "deepseek/deepseek-chat",

        "groq":
        "llama-3.3-70b-versatile",

        "kimi":
        "moonshotai/kimi-k2",

        "openai":
        "gpt-4o"
    }

    return mapping.get(
        model,
        "deepseek/deepseek-chat"
    )

# =========================================================
# MAIN CHAT ENDPOINT
# =========================================================

@app.post("/api/chat")
def ai_chat(
    data: AIChatRequest
):

    settings = get_user_settings(
        data.user_id
    )

    if not settings:

        settings = {
            "ai_model":"openrouter",
            "temperature":0.7,
            "system_prompt":
            "You are a helpful AI assistant."
        }

    history = load_memory(
        data.conversation_id
    )

    messages = []

    messages.append({
        "role":"system",
        "content":
        settings["system_prompt"]
    })

    for item in history:

        messages.append({
            "role":
            item["role"],
            "content":
            item["content"]
        })

    messages.append({
        "role":"user",
        "content":
        data.message
    })

    model = choose_model(
        settings
    )

    result = ask_openrouter(
        model,
        messages
    )

    ai_text = result["choices"][0]\
    ["message"]["content"]

    save_memory(
        data.user_id,
        data.conversation_id,
        "user",
        data.message
    )

    save_memory(
        data.user_id,
        data.conversation_id,
        "assistant",
        ai_text
    )

    return {
        "success": True,
        "model": model,
        "response": ai_text
    }

# =========================================================
# AI CAPABILITIES
# =========================================================

@app.get("/api/ai/capabilities")
def ai_capabilities():

    return {
        "success": True,
        "chat": True,
        "memory": True,
        "web_search": True,
        "news": True,
        "weather": True,
        "finance": True,
        "sports": True,
        "movies": True,
        "drafts": True,
        "attachments": True
    }

# =========================================================
# PROVIDER STATUS
# =========================================================

@app.get("/api/providers")
def providers():

    return {
        "success": True,
        "providers":[
            "OpenRouter",
            "OpenAI",
            "Groq",
            "Kimi",
            "Tavily",
            "Exa",
            "Firecrawl",
            "NewsAPI",
            "GNews",
            "Guardian",
            "Mediastack",
            "OpenWeather",
            "ExchangeRate",
            "AlphaVantage",
            "Finnhub",
            "TMDB",
            "SportMonks",
            "Sportradar",
            "TheSportsDB",
            "AllSports",
            "API-Sports",
            "OddsAPI"
        ]
    }

# =========================================================
# END OF PART 7
#
# PARTS 1-7 COMPLETE
# =========================================================


