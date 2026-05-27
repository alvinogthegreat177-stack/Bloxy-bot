# app.py
# BLOXY-BOT ULTIMATE REWRITE
# Single-file FastAPI AI platform

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sqlite3
import hashlib
import requests
import uvicorn
import json
import os
import time
import uuid

app = FastAPI()

# =========================================================
# ENV
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("bloxybot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    username TEXT,
    password TEXT,
    verified INTEGER DEFAULT 0,
    created_at TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS conversations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT,
    email TEXT,
    title TEXT,
    pinned INTEGER DEFAULT 0,
    messages TEXT,
    updated_at TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS drafts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    content TEXT
)
''')

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
# HELPERS
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def ask_ai(message, history):
    for model in MODELS:
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": history + [{"role":"user","content":message}],
                    "temperature": 0.5,
                    "max_tokens": 900
                },
                timeout=35
            )

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except:
            continue

    return "⚠️ Bloxy-bot could not generate a response."


def get_prem_table():
    try:
        r = requests.get(
            "https://v3.football.api-sports.io/standings",
            headers={"x-apisports-key": APISPORTS_API_KEY},
            params={"league":39,"season":2025},
            timeout=20
        )

        data = r.json()
        standings = data["response"][0]["league"]["standings"][0]

        html = "<table class='table'><tr><th>#</th><th>Club</th><th>Pts</th></tr>"

        for team in standings:
            html += f"<tr><td>{team['rank']}</td><td>{team['team']['name']}</td><td>{team['points']}</td></tr>"

        html += "</table>"

        return html

    except:
        return "⚠️ Could not load Premier League table"

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

class Chat(BaseModel):
    email:str
    conversation_id:str
    message:str

class ConversationAction(BaseModel):
    email:str
    conversation_id:str

class RenameConversation(BaseModel):
    email:str
    conversation_id:str
    new_title:str

# =========================================================
# AUTH
# =========================================================

@app.post("/register")
def register(data:Register):

    if "@" not in data.email:
        return {"success":False,"message":"Invalid email"}

    if len(data.password) < 6:
        return {"success":False,"message":"Password must be 6+ characters"}

    verified = 1 if data.username.lower() in ["alvin","consolemicgg","atg"] else 0

    try:
        cur.execute(
            "INSERT INTO users(email,username,password,verified,created_at) VALUES(?,?,?,?,?)",
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
            "success":True,
            "username":data.username,
            "verified":bool(verified),
            "conversation_id":conversation_id
        }

    except:
        return {"success":False,"message":"Account already exists"}

@app.post("/login")
def login(data:Login):

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (
            data.email,
            hash_password(data.password)
        )
    )

    user = cur.fetchone()

    if not user:
        return {"success":False}

    return {
        "success":True,
        "username":user[2],
        "verified":bool(user[4])
    }

# =========================================================
# CONVERSATIONS
# =========================================================

@app.get("/conversations/{email}")
def conversations(email:str):

    cur.execute(
        "SELECT conversation_id,title,pinned FROM conversations WHERE email=? ORDER BY pinned DESC, updated_at DESC",
        (email,)
    )

    rows = cur.fetchall()

    return {
        "conversations":[
            {
                "conversation_id":r[0],
                "title":r[1],
                "pinned":bool(r[2])
            }
            for r in rows
        ]
    }

@app.post("/new-chat")
def new_chat(data:ConversationAction):

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
        "success":True,
        "conversation_id":conversation_id
    }

@app.post("/rename-chat")
def rename_chat(data:RenameConversation):

    cur.execute(
        "UPDATE conversations SET title=? WHERE email=? AND conversation_id=?",
        (
            data.new_title,
            data.email,
            data.conversation_id
        )
    )

    conn.commit()

    return {"success":True}

@app.post("/pin-chat")
def pin_chat(data:ConversationAction):

    cur.execute(
        "UPDATE conversations SET pinned=1 WHERE email=? AND conversation_id=?",
        (
            data.email,
            data.conversation_id
        )
    )

    conn.commit()

    return {"success":True}

@app.post("/delete-chat")
def delete_chat(data:ConversationAction):

    cur.execute(
        "DELETE FROM conversations WHERE email=? AND conversation_id=?",
        (
            data.email,
            data.conversation_id
        )
    )

    conn.commit()

    return {"success":True}

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data:Chat):

    low = data.message.lower().strip()

    if low in ["pl table","prem table","epl table","premier league table"]:
        return {"reply":get_prem_table()}

    history = []

    if data.email != "guest":

        cur.execute(
            "SELECT messages FROM conversations WHERE conversation_id=?",
            (data.conversation_id,)
        )

        row = cur.fetchone()

        if row:
            try:
                history = json.loads(row[0])[-12:]
            except:
                history = []

    reply = ask_ai(data.message, history)

    if data.email != "guest":

        history.append({"role":"user","content":data.message})
        history.append({"role":"assistant","content":reply})

        cur.execute(
            "UPDATE conversations SET messages=?, updated_at=? WHERE conversation_id=?",
            (
                json.dumps(history),
                str(time.time()),
                data.conversation_id
            )
        )

        conn.commit()

    return {"reply":reply}

# =========================================================
# FRONTEND
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
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
display:flex;
flex-direction:column;
border-right:1px solid #222;
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
border-radius:18px;
background:#1c1c1c;
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
background:#191919;
border-radius:16px;
margin-bottom:10px;
cursor:pointer;
}
.account{
padding:18px;
border-top:1px solid #222;
font-weight:bold;
display:flex;
align-items:center;
gap:10px;
}
.verify{
width:18px;
height:18px;
background:orange;
clip-path:polygon(50% 0%,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%);
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
}
.message{
padding:16px;
margin-bottom:14px;
border-radius:18px;
white-space:pre-wrap;
line-height:1.6;
word-break:break-word;
}
.user{background:#1f1f1f;}
.bot{background:#181818;border-left:4px solid orange;}
.inputbar{
display:flex;
gap:10px;
padding:18px;
background:#111;
}
textarea{
flex:1;
height:70px;
background:#1c1c1c;
color:white;
border:none;
border-radius:18px;
padding:18px;
resize:none;
font-size:16px;
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
.authtitle{
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
.table{
width:100%;
border-collapse:collapse;
}
.table td,.table th{
padding:10px;
border-bottom:1px solid #333;
}
</style>
</head>
<body>
<div class="auth" id="auth">
<div class="authbox">
<div class="authtitle">🤖 Bloxy-bot</div>
<input id="email" class="input" placeholder="Email">
<input id="username" class="input" placeholder="Username">
<input id="password" type="password" class="input" placeholder="Password">
<button class="authbtn" onclick="register()">Create Account</button>
<button class="authbtn" onclick="login()">Login</button>
<button class="authbtn" onclick="guestMode()">Continue as Guest</button>
</div>
</div>
<div class="sidebar">
<div class="logo">Bloxy-bot</div>
<div class="newchat" onclick="newChat()">➕ New Chat</div>
<div class="conversations" id="conversations"></div>
<div class="account" id="account">👤 Guest</div>
</div>
<div class="main">
<div class="messages" id="messages">💬 Start chatting...</div>
<div class="inputbar">
<textarea id="msg" placeholder="Message Bloxy-bot..."></textarea>
<button class="send" onclick="send()">➤</button>
</div>
</div>
<script>
let EMAIL='guest';
let USERNAME='Guest';
let VERIFIED=false;
let CONVERSATION_ID='';

function guestMode(){
document.getElementById('auth').style.display='none';
}

function updateAccount(){
document.getElementById('account').innerHTML=`👤 ${USERNAME} ${VERIFIED ? `<span class='verify' title='This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform'></span>`:''}`;
}

async function register(){
let email=emailEl().value;
let username=usernameEl().value;
let password=passwordEl().value;

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
let email=emailEl().value;
let password=passwordEl().value;

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

let r=await fetch(`/conversations/${EMAIL}`);
let d=await r.json();

let html='';

for(let c of d.conversations){
html+=`<div class='conversation' onclick="openConversation('${c.conversation_id}')">${c.pinned?'📌 ':''}${c.title}</div>`;
}

document.getElementById('conversations').innerHTML=html;

if(d.conversations.length>0){
CONVERSATION_ID=d.conversations[0].conversation_id;
}
}

function openConversation(id){
CONVERSATION_ID=id;
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
box.innerHTML+=`<div class='message bot' id='typing'>🤖 Bloxy-bot is typing...</div>`;

box.scrollTop=box.scrollHeight;

document.getElementById('msg').value='';

let r=await fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:EMAIL,
conversation_id:CONVERSATION_ID,
message:msg
})
});

let d=await r.json();

document.getElementById('typing').remove();

box.innerHTML+=`<div class='message bot'>🤖 ${d.reply}</div>`;

box.scrollTop=box.scrollHeight;
}

function emailEl(){return document.getElementById('email')}
function usernameEl(){return document.getElementById('username')}
function passwordEl(){return document.getElementById('password')}

updateAccount();
</script>
</body>
</html>
'''

# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
