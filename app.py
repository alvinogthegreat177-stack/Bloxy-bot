# =========================================================
# BLOXY-BOT X (PART 1)
# app.py
# Core Backend Foundation
# =========================================================

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import bcrypt
import requests
import json
import uuid
import time
import os

app = FastAPI(title="Bloxy-Bot X")

# =========================================================
# CONFIG
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")

MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat-v3-0324:free",
    "mistralai/mistral-small-3.2-24b-instruct:free"
]

# =========================================================
# DATABASE
# =========================================================

db = sqlite3.connect(
    "bloxybot.db",
    check_same_thread=False
)

db.row_factory = sqlite3.Row

cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT UNIQUE,
username TEXT UNIQUE,
password TEXT,
verified INTEGER DEFAULT 0,
created_at TEXT
)
""")

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

cur.execute("""
CREATE TABLE IF NOT EXISTS drafts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT,
draft TEXT
)
""")

db.commit()

# =========================================================
# MODELS
# =========================================================

class Register(BaseModel):
    email:str
    username:str
    password:str

class Login(BaseModel):
    email:str
    password:str

class ChatRequest(BaseModel):
    email:str
    conversation_id:str
    message:str

class ConversationAction(BaseModel):
    email:str
    conversation_id:str

class RenameChat(BaseModel):
    email:str
    conversation_id:str
    title:str

# =========================================================
# PASSWORDS
# =========================================================

def hash_password(password:str):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def verify_password(
    password:str,
    hashed:str
):
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )

# =========================================================
# SEARCH
# =========================================================

def tavily_search(query:str):

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

        r.raise_for_status()

        data = r.json()

        output = []

        for item in data.get("results", []):
            output.append(
                item.get("content", "")
            )

        return "\n".join(output)

    except Exception as e:
        print("TAVILY ERROR:", e)
        return ""

# =========================================================
# NEWS API
# =========================================================

def latest_news(topic:str):

    if not NEWS_API_KEY:
        return ""

    try:

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": topic,
                "pageSize": 5,
                "apiKey": NEWS_API_KEY
            },
            timeout=15
        )

        r.raise_for_status()

        data = r.json()

        articles = []

        for a in data.get("articles", []):
            articles.append(
                f"{a.get('title','')}"
            )

        return "\n".join(articles)

    except Exception as e:
        print("NEWS ERROR:", e)
        return ""

# =========================================================
# OPENROUTER
# =========================================================

def ai_response(
    prompt,
    history
):

    live_search = tavily_search(prompt)
    live_news = latest_news(prompt)

    system_prompt = f"""
You are Bloxy-Bot X.

Use:
- clean formatting
- markdown
- bullets
- concise answers

Web Search:
{live_search}

News:
{live_news}
"""

    messages = [
        {
            "role":"system",
            "content":system_prompt
        }
    ]

    messages.extend(history)

    messages.append({
        "role":"user",
        "content":prompt
    })

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

            r.raise_for_status()

            data = r.json()

            if "choices" not in data:
                continue

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            print(model, e)

    return "⚠️ AI unavailable."

# =========================================================
# AUTH
# =========================================================

@app.post("/register")
def register(data:Register):

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
                hash_password(
                    data.password
                ),
                str(time.time())
            )
        )

        db.commit()

        return {
            "success":True
        }

    except Exception as e:

        return {
            "success":False,
            "message":str(e)
        }

@app.post("/login")
def login(data:Login):

    cur.execute(
        "SELECT * FROM users WHERE email=?",
        (data.email,)
    )

    user = cur.fetchone()

    if not user:
        return {"success":False}

    if not verify_password(
        data.password,
        user["password"]
    ):
        return {"success":False}

    return {
        "success":True,
        "username":user["username"],
        "verified":bool(
            user["verified"]
        )
    }

# ===== END PART 1 =====
# NEXT: conversations, sports,
# drafts, chat routes, UI.

# =========================================================
# BLOXY-BOT X (PART 2)
# Conversations + Drafts + Chat Routes
# =========================================================

@app.get("/conversations/{email}")
def get_conversations(email: str):

    cur.execute(
        """
        SELECT conversation_id,title,pinned,updated_at
        FROM conversations
        WHERE email=?
        ORDER BY pinned DESC, updated_at DESC
        """,
        (email,)
    )

    rows = cur.fetchall()

    return {
        "conversations": [
            dict(row) for row in rows
        ]
    }


@app.post("/new-chat")
def new_chat(data: ConversationAction):

    cid = str(uuid.uuid4())

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
            cid,
            data.email,
            "New Chat",
            "[]",
            str(time.time())
        )
    )

    db.commit()

    return {
        "success": True,
        "conversation_id": cid
    }


@app.post("/rename-chat")
def rename_chat(data: RenameChat):

    cur.execute(
        """
        UPDATE conversations
        SET title=?
        WHERE conversation_id=?
        AND email=?
        """,
        (
            data.title,
            data.conversation_id,
            data.email
        )
    )

    db.commit()

    return {"success": True}


@app.post("/pin-chat")
def pin_chat(data: ConversationAction):

    cur.execute(
        """
        SELECT pinned
        FROM conversations
        WHERE conversation_id=?
        AND email=?
        """,
        (
            data.conversation_id,
            data.email
        )
    )

    row = cur.fetchone()

    if not row:
        raise HTTPException(404)

    new_value = 0 if row["pinned"] else 1

    cur.execute(
        """
        UPDATE conversations
        SET pinned=?
        WHERE conversation_id=?
        """,
        (
            new_value,
            data.conversation_id
        )
    )

    db.commit()

    return {"success": True}


@app.post("/delete-chat")
def delete_chat(data: ConversationAction):

    cur.execute(
        """
        DELETE FROM conversations
        WHERE conversation_id=?
        AND email=?
        """,
        (
            data.conversation_id,
            data.email
        )
    )

    db.commit()

    return {"success": True}


@app.get("/messages/{conversation_id}")
def load_messages(conversation_id: str):

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
        return {"messages": []}

    try:
        return {
            "messages":
            json.loads(row["messages"])
        }
    except:
        return {"messages": []}


# =========================================================
# DRAFTS
# =========================================================

class DraftModel(BaseModel):
    email: str
    draft: str


@app.post("/save-draft")
def save_draft(data: DraftModel):

    cur.execute(
        "DELETE FROM drafts WHERE email=?",
        (data.email,)
    )

    cur.execute(
        """
        INSERT INTO drafts(
        email,
        draft
        )
        VALUES(?,?)
        """,
        (
            data.email,
            data.draft
        )
    )

    db.commit()

    return {"success": True}


@app.get("/draft/{email}")
def load_draft(email: str):

    cur.execute(
        """
        SELECT draft
        FROM drafts
        WHERE email=?
        """,
        (email,)
    )

    row = cur.fetchone()

    if not row:
        return {"draft": ""}

    return {"draft": row["draft"]}


# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    history = []

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
                row["messages"]
            )[-20:]
        except:
            history = []

    reply = ai_response(
        data.message,
        history
    )

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

    db.commit()

    return {
        "reply": reply
    }

# ===== END PART 2 =====
# PART 3 = Sports API + News Commands + Full UI

# =========================================================
# BLOXY-BOT X (PART 3)
# Sports + News + Utility Endpoints
# =========================================================

def get_premier_league_table():
    try:
        r = requests.get(
            "https://v3.football.api-sports.io/standings",
            headers={
                "x-apisports-key": APISPORTS_API_KEY
            },
            params={
                "league": 39,
                "season": 2025
            },
            timeout=20
        )

        data = r.json()

        standings = (
            data["response"][0]
            ["league"]["standings"][0]
        )

        return standings

    except:
        return []


@app.get("/sports/epl")
def epl_table():

    table = get_premier_league_table()

    return {
        "success": True,
        "table": table
    }


@app.get("/sports/top5")
def top_five():

    table = get_premier_league_table()

    return {
        "leaders": table[:5]
    }


# =========================================================
# NEWS SEARCH
# =========================================================

@app.get("/news")
def news(query: str):

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

        data = r.json()

        return {
            "articles":
            data.get("articles", [])
        }

    except:
        return {
            "articles": []
        }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "version": "Bloxy-Bot X"
    }


# =========================================================
# STATS
# =========================================================

@app.get("/stats")
def stats():

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM conversations"
    )
    chats = cur.fetchone()[0]

    return {
        "users": users,
        "conversations": chats
    }

# ===== END PART 3 =====
# FINAL MERGED app.py = combine Part 1 + Part 2 + Part 3 and resolve duplicate classes/imports.

# =========================================================
# BLOXY-BOT X (PART 4)
# UI (HTML + CSS + JavaScript)
# =========================================================

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

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial,sans-serif;
}

body{
background:#0b0b0b;
color:white;
height:100vh;
overflow:hidden;
}

.sidebar{
position:fixed;
left:0;
top:0;
bottom:0;
width:300px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.logo{
padding:20px;
font-size:28px;
font-weight:bold;
color:orange;
}

.newchat{
margin:12px;
padding:14px;
background:#1c1c1c;
border-radius:14px;
cursor:pointer;
}

.conversations{
flex:1;
overflow:auto;
padding:10px;
}

.conversation{
background:#181818;
padding:12px;
margin-bottom:8px;
border-radius:12px;
cursor:pointer;
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
margin-bottom:12px;
border-radius:14px;
white-space:pre-wrap;
}

.user{
background:#202020;
}

.bot{
background:#151515;
border-left:4px solid orange;
}

.inputbar{
display:flex;
gap:10px;
padding:15px;
background:#111;
}

textarea{
flex:1;
height:70px;
background:#1c1c1c;
border:none;
border-radius:14px;
padding:15px;
color:white;
resize:none;
}

button{
border:none;
cursor:pointer;
}

.send{
width:80px;
border-radius:14px;
background:orange;
color:white;
font-weight:bold;
}

.auth{
position:fixed;
inset:0;
display:flex;
justify-content:center;
align-items:center;
background:#0b0b0b;
z-index:999;
}

.authbox{
width:400px;
background:#111;
padding:30px;
border-radius:20px;
}

.input{
width:100%;
padding:14px;
margin-bottom:10px;
background:#1c1c1c;
border:none;
border-radius:12px;
color:white;
}

.authbtn{
width:100%;
padding:14px;
margin-bottom:10px;
background:orange;
color:white;
border-radius:12px;
}

</style>
</head>

<body>

<div class="auth" id="auth">

<div class="authbox">

<h2>Bloxy-Bot X</h2>

<br>

<input id="email" class="input" placeholder="Email">

<input id="username" class="input" placeholder="Username">

<input id="password" type="password" class="input" placeholder="Password">

<button class="authbtn" onclick="registerUser()">
Register
</button>

<button class="authbtn" onclick="loginUser()">
Login
</button>

<button class="authbtn" onclick="guestMode()">
Guest Mode
</button>

</div>
</div>

<div class="sidebar">

<div class="logo">
🤖 Bloxy
</div>

<div class="newchat" onclick="newChat()">
➕ New Chat
</div>

<div id="conversations" class="conversations">
</div>

</div>

<div class="main">

<div id="messages" class="messages">
</div>

<div class="inputbar">

<textarea
id="msg"
placeholder="Message Bloxy..."
></textarea>

<button
class="send"
onclick="sendMessage()">
Send
</button>

</div>

</div>

<script>

let EMAIL="guest";
let CONVERSATION="";

function guestMode(){
document.getElementById("auth").style.display="none";
}

async function registerUser(){

const email =
document.getElementById("email").value;

const username =
document.getElementById("username").value;

const password =
document.getElementById("password").value;

const r = await fetch("/register",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
email,
username,
password
})
});

const d = await r.json();

if(d.success){
alert("Registered");
}
}

async function loginUser(){

const email =
document.getElementById("email").value;

const password =
document.getElementById("password").value;

const r = await fetch("/login",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
email,
password
})
});

const d = await r.json();

if(!d.success){
alert("Login failed");
return;
}

EMAIL=email;

localStorage.setItem(
"bloxy_email",
email
);

document.getElementById(
"auth"
).style.display="none";

loadChats();
}

async function loadChats(){

const r = await fetch(
"/conversations/"+EMAIL
);

const d = await r.json();

let html="";

for(const c of d.conversations){

html += `
<div
class="conversation"
onclick="openChat('${c.conversation_id}')">
${c.title}
</div>`;
}

document.getElementById(
"conversations"
).innerHTML = html;
}

function openChat(id){
CONVERSATION=id;
}

async function newChat(){

const r = await fetch(
"/new-chat",
{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
email:EMAIL,
conversation_id:""
})
}
);

const d = await r.json();

CONVERSATION =
d.conversation_id;

loadChats();
}

async function sendMessage(){

const msg =
document.getElementById(
"msg"
).value.trim();

if(!msg) return;

const box =
document.getElementById(
"messages"
);

box.innerHTML +=
`<div class="message user">${msg}</div>`;

document.getElementById(
"msg"
).value="";

const r = await fetch(
"/chat",
{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
email:EMAIL,
conversation_id:CONVERSATION,
message:msg
})
}
);

const d = await r.json();

box.innerHTML +=
`<div class="message bot">${d.reply}</div>`;

box.scrollTop =
box.scrollHeight;
}

document
.getElementById("msg")
.addEventListener(
"keydown",
function(e){

if(
e.key==="Enter"
&& !e.shiftKey
){
e.preventDefault();
sendMessage();
}
}
);

</script>

</body>
</html>
"""

# ===== END PART 4 =====
# PART 5 = Final cleanup, startup,
# autosave drafts, chat loading,
# mobile menu, and final merge.

# =========================================================
# BLOXY-BOT X (PART 5)
# Final Cleanup + Startup + Quality Fixes
# =========================================================

# AUTO LOAD SAVED EMAIL
window.onload = async function(){

    let saved =
    localStorage.getItem(
        "bloxy_email"
    );

    if(saved){

        EMAIL = saved;

        document.getElementById(
            "auth"
        ).style.display = "none";

        await loadChats();
    }
};

# AUTO SCROLL HELPER

function scrollBottom(){

    let box =
    document.getElementById(
        "messages"
    );

    box.scrollTop =
    box.scrollHeight;
}

# DRAFT AUTOSAVE

setInterval(async ()=>{

    if(EMAIL==="guest")
        return;

    let draft =
    document.getElementById(
        "msg"
    ).value;

    try{

        await fetch(
        "/save-draft",
        {
            method:"POST",
            headers:{
                "Content-Type":
                "application/json"
            },
            body:JSON.stringify({
                email:EMAIL,
                draft:draft
            })
        });

    }catch(e){}

},3000);

# LOAD DRAFT

async function loadDraft(){

    if(EMAIL==="guest")
        return;

    try{

        let r =
        await fetch(
        "/draft/"+EMAIL
        );

        let d =
        await r.json();

        document.getElementById(
        "msg"
        ).value =
        d.draft || "";

    }catch(e){}
}

# IMPROVED OPEN CHAT

async function openChat(id){

    CONVERSATION = id;

    let r =
    await fetch(
    "/messages/"+id
    );

    let d =
    await r.json();

    let html = "";

    for(let m of d.messages){

        let cls =
        m.role==="user"
        ? "user"
        : "bot";

        html += `
        <div class="message ${cls}">
        ${m.content}
        </div>`;
    }

    document.getElementById(
    "messages"
    ).innerHTML = html;

    scrollBottom();
}

# LOAD DRAFT AFTER LOGIN

# add:
# await loadDraft();
# directly after successful login

# =========================================================
# FASTAPI STARTUP
# =========================================================

@app.get("/health")
def health():
    return {
        "status":"online",
        "app":"Bloxy-Bot X"
    }

# =========================================================
# APP START
# =========================================================

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# =========================================================
# END OF PART 5
# =========================================================

# You now have:
# ✅ Part 1
# ✅ Part 2
# ✅ Part 3
# ✅ Part 4
# ✅ Part 5
#
# Next step: merge all parts into one app.py,
# remove duplicate imports/classes/routes,
# then test and fix runtime errors.
