# app.py
# BLOXY-BOT COMPLETE FRESH REWRITE
# Single-file AI platform with:
# - FastAPI backend
# - Persistent accounts
# - Guest mode
# - Long-term conversation storage
# - Multi-model AI routing
# - Live web search
# - Sports tables
# - Modern UI
# - Conversation rename/pin/delete
# - SVG verified badge
# - Ctrl+Enter send
# - Draft system
# - Auto-scroll
# - SQLite persistence
# - Real-time data support

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

app = FastAPI()

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("bloxybot.db", check_same_thread=False)
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

cur.execute("""
CREATE TABLE IF NOT EXISTS drafts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    draft TEXT
)
""")

conn.commit()

# =========================================================
# AI MODELS
# =========================================================

MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat-v3-0324:free",
    "qwen/qwen-2.5-72b-instruct",
    "mistralai/mistral-small-3.2-24b-instruct:free"
]

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def realtime_search(query):
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
            results.append(item.get("content", ""))

        return "\n".join(results)

    except:
        return ""


def format_response(text):

    lines = text.split("\n")
    output = []

    for line in lines:

        clean = line.strip()

        if clean:
            output.append("• " + clean)

    return "\n".join(output)


def ai_reply(message, history):

    live_data = realtime_search(message)

    system_prompt = f"""
You are Bloxy-bot.

Rules:
- Use modern formatting.
- Use emojis naturally.
- Avoid ugly paragraphs.
- Use bullet lists when appropriate.
- Give real-time answers using provided live data.
- Be intelligent and clean.
- Avoid dictionary-style responses.
- Make sports tables look good.
- Keep answers concise but informative.

Live Data:
{live_data}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    for h in history:
        messages.append(h)

    messages.append({
        "role": "user",
        "content": message
    })

    for model in MODELS:

        try:

            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 1000
                },
                timeout=40
            )

            data = r.json()

            reply = data["choices"][0]["message"]["content"]

            return format_response(reply)

        except:
            continue

    return "⚠️ Bloxy-bot could not generate a response."


def get_prem_table():

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

        standings = data["response"][0]["league"]["standings"][0]

        html = """
        <table class='table'>
        <tr>
        <th>#</th>
        <th>Club</th>
        <th>Pts</th>
        </tr>
        """

        for team in standings:
            html += f"""
            <tr>
            <td>{team['rank']}</td>
            <td>{team['team']['name']}</td>
            <td>{team['points']}</td>
            </tr>
            """

        html += "</table>"

        return html

    except:
        return "⚠️ Could not load Premier League table."

# =========================================================
# AUTH ROUTES
# =========================================================

@app.post("/register")
def register(data: Register):

    if "@" not in data.email:
        return {"success": False, "message": "Invalid email"}

    if len(data.password) < 6:
        return {"success": False, "message": "Password too short"}

    verified = 1 if data.username.lower() in ["atg", "alvin", "consolemicgg"] else 0

    try:

        cur.execute(
            "INSERT INTO users(email, username, password, verified, created_at) VALUES(?,?,?,?,?)",
            (
                data.email,
                data.username,
                hash_password(data.password),
                verified,
                str(time.time())
            )
        )

        conversation_id = str(uuid.uuid4())

        cur.execute(
            "INSERT INTO conversations(conversation_id,email,title,messages,updated_at) VALUES(?,?,?,?,?)",
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
            "conversation_id": conversation_id,
            "verified": bool(verified)
        }

    except:
        return {"success": False, "message": "Account already exists"}


@app.post("/login")
def login(data: Login):

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
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
        "username": user[2],
        "verified": bool(user[4])
    }

# =========================================================
# CONVERSATIONS
# =========================================================

@app.get("/conversations/{email}")
def get_conversations(email: str):

    cur.execute(
        "SELECT conversation_id,title,pinned FROM conversations WHERE email=? ORDER BY pinned DESC, updated_at DESC",
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
        "INSERT INTO conversations(conversation_id,email,title,messages,updated_at) VALUES(?,?,?,?,?)",
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
        "UPDATE conversations SET title=? WHERE conversation_id=?",
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
        "UPDATE conversations SET pinned=1 WHERE conversation_id=?",
        (data.conversation_id,)
    )

    conn.commit()

    return {"success": True}


@app.post("/delete-chat")
def delete_chat(data: ConversationAction):

    cur.execute(
        "DELETE FROM conversations WHERE conversation_id=?",
        (data.conversation_id,)
    )

    conn.commit()

    return {"success": True}

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: Chat):

    low = data.message.lower().strip()

    if low in [
        "pl table",
        "prem table",
        "epl table",
        "premier league table"
    ]:
        return {
            "reply": get_prem_table()
        }

    history = []

    if data.email != "guest":

        cur.execute(
            "SELECT messages FROM conversations WHERE conversation_id=?",
            (data.conversation_id,)
        )

        row = cur.fetchone()

        if row:
            try:
                history = json.loads(row[0])[-20:]
            except:
                history = []

    reply = ai_reply(data.message, history)

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
            "UPDATE conversations SET messages=?, updated_at=? WHERE conversation_id=?",
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

# =========================================================
# UI
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body{
margin:0;
background:#0b0b0b;
font-family:Arial;
color:white;
overflow:hidden;
}
.sidebar{
position:fixed;
left:0;
top:0;
bottom:0;
width:320px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}
.logo{
padding:24px;
font-size:34px;
font-weight:bold;
background:linear-gradient(90deg,#ff8800,#ffaa00);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}
.newchat{
margin:12px;
padding:16px;
background:#1d1d1d;
border-radius:18px;
cursor:pointer;
font-weight:bold;
}
.conversations{
flex:1;
overflow-y:auto;
padding:12px;
}
.conversation{
padding:14px;
background:#181818;
border-radius:16px;
margin-bottom:10px;
display:flex;
justify-content:space-between;
align-items:center;
}
.main{
margin-left:320px;
height:100vh;
display:flex;
flex-direction:column;
}
.messages{
flex:1;
overflow-y:auto;
padding:20px;
scroll-behavior:smooth;
}
.message{
padding:18px;
border-radius:18px;
margin-bottom:14px;
white-space:pre-wrap;
line-height:1.7;
word-break:break-word;
}
.user{
background:#1f1f1f;
}
.bot{
background:#181818;
border-left:4px solid orange;
}
.inputbar{
display:flex;
gap:12px;
padding:18px;
background:#111;
}
textarea{
flex:1;
height:70px;
background:#1c1c1c;
border:none;
border-radius:18px;
padding:18px;
color:white;
resize:none;
font-size:16px;
outline:none;
}
.send{
width:80px;
border:none;
border-radius:18px;
background:orange;
color:white;
font-size:22px;
font-weight:bold;
cursor:pointer;
}
.auth{
position:fixed;
inset:0;
background:#0b0b0b;
display:flex;
justify-content:center;
align-items:center;
z-index:9999;
}
.authbox{
width:430px;
background:#111;
padding:36px;
border-radius:28px;
}
.title{
font-size:40px;
font-weight:bold;
margin-bottom:20px;
background:linear-gradient(90deg,#ff8800,#ffcc00);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}
.input{
width:100%;
padding:16px;
margin-bottom:14px;
background:#1c1c1c;
border:none;
border-radius:16px;
color:white;
box-sizing:border-box;
}
.authbtn{
width:100%;
padding:16px;
border:none;
border-radius:16px;
background:orange;
color:white;
font-weight:bold;
margin-bottom:12px;
cursor:pointer;
}
.account{
padding:18px;
border-top:1px solid #222;
display:flex;
align-items:center;
gap:10px;
font-weight:bold;
}
.tooltip{
display:none;
position:absolute;
background:#222;
padding:10px;
border-radius:12px;
width:230px;
font-size:12px;
bottom:30px;
left:0;
}
.badge:hover .tooltip{
display:block;
}
.badge{
position:relative;
display:flex;
align-items:center;
}
.table{
width:100%;
border-collapse:collapse;
}
.table td,.table th{
padding:10px;
border-bottom:1px solid #333;
}
.typing{
animation:pulse 1s infinite;
}
@keyframes pulse{
0%{opacity:0.3;}
50%{opacity:1;}
100%{opacity:0.3;}
}
</style>
</head>
<body>
<div class='auth' id='auth'>
<div class='authbox'>
<div class='title'>🤖 Bloxy-bot</div>
<input class='input' id='email' placeholder='Email'>
<input class='input' id='username' placeholder='Username'>
<input class='input' id='password' type='password' placeholder='Password'>
<button class='authbtn' onclick='register()'>Create Account</button>
<button class='authbtn' onclick='login()'>Login</button>
<button class='authbtn' onclick='guestMode()'>Continue as Guest</button>
</div>
</div>
<div class='sidebar'>
<div class='logo'>Bloxy-bot</div>
<div class='newchat' onclick='newChat()'>➕ New Chat</div>
<div class='conversations' id='conversations'></div>
<div class='account' id='account'>👤 Guest</div>
</div>
<div class='main'>
<div class='messages' id='messages'>💬 Start chatting...</div>
<div class='inputbar'>
<textarea id='msg' placeholder='Message Bloxy-bot...'></textarea>
<button class='send' onclick='send()'>➤</button>
</div>
</div>
<script>
let EMAIL='guest';
let USERNAME='Guest';
let VERIFIED=false;
let CONVERSATION_ID='';

function verifiedSVG(){
return `
<div class='badge'>
<svg width='18' height='18' viewBox='0 0 24 24' fill='orange'>
<path d='M12 0L15 4L20 4L21 9L24 12L21 15L20 20L15 20L12 24L9 20L4 20L3 15L0 12L3 9L4 4L9 4Z'/>
</svg>
<div class='tooltip'>
This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform.
</div>
</div>`;
}

function updateAccount(){
document.getElementById('account').innerHTML=`👤 ${USERNAME} ${VERIFIED ? verifiedSVG() : ''}`;
}

function guestMode(){
document.getElementById('auth').style.display='none';
}

async function register(){
let email=document.getElementById('email').value;
let username=document.getElementById('username').value;
let password=document.getElementById('password').value;

let r=await fetch('/register',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email,username,password})
});

let d=await r.json();

if(d.success){
EMAIL=email;
USERNAME=username;
VERIFIED=d.verified;
CONVERSATION_ID=d.conversation_id;
localStorage.setItem('bloxy_email',EMAIL);
updateAccount();
document.getElementById('auth').style.display='none';
loadConversations();
}else{
alert(d.message);
}
}

async function login(){
let email=document.getElementById('email').value;
let password=document.getElementById('password').value;

let r=await fetch('/login',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email,password})
});

let d=await r.json();

if(d.success){
EMAIL=email;
USERNAME=d.username;
VERIFIED=d.verified;
localStorage.setItem('bloxy_email',EMAIL);
updateAccount();
document.getElementById('auth').style.display='none';
loadConversations();
}else{
alert('Wrong login');
}
}

async function loadConversations(){
if(EMAIL==='guest') return;

let r=await fetch('/conversations/'+EMAIL);
let d=await r.json();

let html='';

for(let c of d.conversations){
html+=`
<div class='conversation'>
<div onclick="openConversation('${c.conversation_id}')">${c.pinned ? '📌 ' : ''}${c.title}</div>
<div onclick="menu(event,'${c.conversation_id}')">⋮</div>
</div>`;
}

document.getElementById('conversations').innerHTML=html;

if(d.conversations.length>0){
CONVERSATION_ID=d.conversations[0].conversation_id;
}
}

function openConversation(id){
CONVERSATION_ID=id;
}

function menu(e,id){
e.stopPropagation();

let action=prompt('rename | pin | delete');

if(action==='rename'){
let title=prompt('New title');
fetch('/rename-chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email:EMAIL,conversation_id:id,new_title:title})
}).then(()=>loadConversations());
}

if(action==='pin'){
fetch('/pin-chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email:EMAIL,conversation_id:id})
}).then(()=>loadConversations());
}

if(action==='delete'){
fetch('/delete-chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email:EMAIL,conversation_id:id})
}).then(()=>loadConversations());
}
}

async function newChat(){
if(EMAIL==='guest') return;

let r=await fetch('/new-chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email:EMAIL,conversation_id:''})
});

let d=await r.json();

CONVERSATION_ID=d.conversation_id;

document.getElementById('messages').innerHTML='💬 Start chatting...';

loadConversations();
}

async function send(){
let msg=document.getElementById('msg').value.trim();
if(!msg) return;

let box=document.getElementById('messages');

box.innerHTML+=`<div class='message user'>👤 ${msg}</div>`;
box.innerHTML+=`<div class='message bot typing' id='typing'>🤖 Bloxy-bot is typing...</div>`;

box.scrollTop=box.scrollHeight;

document.getElementById('msg').value='';

let r=await fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({email:EMAIL,conversation_id:CONVERSATION_ID,message:msg})
});

let d=await r.json();

document.getElementById('typing').remove();

box.innerHTML+=`<div class='message bot'>🤖 ${d.reply}</div>`;

box.scrollTop=box.scrollHeight;
}

document.getElementById('msg').addEventListener('keydown',function(e){
if(e.ctrlKey && e.key==='Enter'){
e.preventDefault();
send();
}
});

updateAccount();
</script>
</body>
</html>
"""

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
