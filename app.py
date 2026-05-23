from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import requests
import uvicorn
import json
import os
import time

app = FastAPI()

# =========================================================
# ENV VARIABLES
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY", "")
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "")

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT UNIQUE,
username TEXT,
password TEXT,
verified INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT,
title TEXT,
messages TEXT,
pinned INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS drafts(
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT,
content TEXT
)
""")

conn.commit()

# =========================================================
# MODELS
# =========================================================

MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat-v3-0324:free",
    "qwen/qwen3-32b:free",
    "mistralai/mistral-small-3.2-24b-instruct:free"
]

# =========================================================
# RULES
# =========================================================

RULES = []

for i in range(1, 301):
    RULES.append(
        f"{i}. Always remain modern intelligent organized fast emoji-friendly and visually structured."
    )

SYSTEM_PROMPT = "\n".join(RULES)

# =========================================================
# PYDANTIC
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
    title: str
    message: str

class RenameChat(BaseModel):
    email: str
    old: str
    new: str

class DeleteChat(BaseModel):
    email: str
    title: str

class PinChat(BaseModel):
    email: str
    title: str

# =========================================================
# AI
# =========================================================

def ask_ai(message, history=[]):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for item in history:
        messages.append(item)

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
                    "temperature": 0.5,
                    "max_tokens": 800
                },
                timeout=40
            )

            data = r.json()

            return data["choices"][0]["message"]["content"]

        except:
            continue

    return "⚠️ Bloxy-bot is overloaded right now."

# =========================================================
# SPORTS
# =========================================================

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
            }
        )

        data = r.json()

        standings = data["response"][0]["league"]["standings"][0]

        html = """
        <table style='width:100%;border-collapse:collapse'>
        <tr>
        <th>#</th>
        <th>Club</th>
        <th>Pts</th>
        </tr>
        """

        for t in standings:

            html += f"""
            <tr>
            <td>{t['rank']}</td>
            <td>{t['team']['name']}</td>
            <td>{t['points']}</td>
            </tr>
            """

        html += "</table>"

        return html

    except:
        return "⚠️ Could not load PL table"

# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(data: Register):

    if "@" not in data.email:
        return {"success": False}

    if len(data.password) < 6:
        return {"success": False}

    verified = 1 if data.username.lower() in [
        "atg",
        "alvin",
        "consolemicgg"
    ] else 0

    try:

        cursor.execute(
            "INSERT INTO users(email,username,password,verified) VALUES(?,?,?,?)",
            (data.email, data.username, data.password, verified)
        )

        cursor.execute(
            "INSERT INTO conversations(email,title,messages) VALUES(?,?,?)",
            (data.email, "Main", "[]")
        )

        conn.commit()

        return {
            "success": True,
            "username": data.username,
            "verified": bool(verified)
        }

    except:
        return {"success": False}

# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: Login):

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (data.email, data.password)
    )

    user = cursor.fetchone()

    if not user:
        return {"success": False}

    return {
        "success": True,
        "username": user[2],
        "verified": bool(user[4])
    }

# =========================================================
# NEW CHAT
# =========================================================

@app.post("/new-chat")
def new_chat(data: Chat):

    cursor.execute(
        "INSERT INTO conversations(email,title,messages) VALUES(?,?,?)",
        (data.email, data.title, "[]")
    )

    conn.commit()

    return {"success": True}

# =========================================================
# RENAME
# =========================================================

@app.post("/rename-chat")
def rename_chat(data: RenameChat):

    cursor.execute(
        "UPDATE conversations SET title=? WHERE email=? AND title=?",
        (data.new, data.email, data.old)
    )

    conn.commit()

    return {"success": True}

# =========================================================
# PIN
# =========================================================

@app.post("/pin-chat")
def pin_chat(data: PinChat):

    cursor.execute(
        "UPDATE conversations SET pinned=1 WHERE email=? AND title=?",
        (data.email, data.title)
    )

    conn.commit()

    return {"success": True}

# =========================================================
# DELETE
# =========================================================

@app.post("/delete-chat")
def delete_chat(data: DeleteChat):

    cursor.execute(
        "DELETE FROM conversations WHERE email=? AND title=?",
        (data.email, data.title)
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
        "premier league table",
        "epl table"
    ]:
        return {
            "reply": get_prem_table()
        }

    history = []

    if data.email != "guest":

        cursor.execute(
            "SELECT messages FROM conversations WHERE email=? AND title=?",
            (data.email, data.title)
        )

        row = cursor.fetchone()

        if row:

            try:
                history = json.loads(row[0])[-12:]
            except:
                history = []

    reply = ask_ai(data.message, history)

    if data.email != "guest":

        history.append({
            "role": "user",
            "content": data.message
        })

        history.append({
            "role": "assistant",
            "content": reply
        })

        cursor.execute(
            "UPDATE conversations SET messages=? WHERE email=? AND title=?",
            (
                json.dumps(history),
                data.email,
                data.title
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
<html>
<head>
<title>Bloxy-bot</title>

<style>

body{
margin:0;
background:#0d0d0d;
font-family:Arial;
overflow:hidden;
color:white;
}

.sidebar{
position:fixed;
left:0;
top:0;
bottom:0;
width:300px;
background:#111;
display:flex;
flex-direction:column;
border-right:1px solid #222;
overflow-y:auto;
}

.logo{
padding:20px;
font-size:32px;
font-weight:bold;
color:#00ff88;
}

.newchat{
margin:10px;
padding:15px;
background:#1d1d1d;
border-radius:14px;
cursor:pointer;
}

.conversations{
flex:1;
padding:10px;
overflow-y:auto;
}

.conv{
padding:15px;
margin-bottom:10px;
background:#181818;
border-radius:12px;
cursor:pointer;
}

.account{
padding:20px;
border-top:1px solid #222;
}

.main{
margin-left:300px;
height:100vh;
display:flex;
flex-direction:column;
}

.messages{
flex:1;
overflow-y:auto;
padding:20px;
}

.msg{
padding:18px;
border-radius:18px;
margin-bottom:18px;
white-space:pre-wrap;
word-break:break-word;
line-height:1.5;
}

.user{
background:#1f1f1f;
}

.bot{
background:#181818;
border-left:4px solid #00ff88;
}

.inputbar{
display:flex;
gap:10px;
padding:20px;
background:#111;
}

textarea{
flex:1;
height:70px;
background:#1b1b1b;
border:none;
border-radius:16px;
padding:16px;
color:white;
resize:none;
font-size:16px;
}

button{
width:80px;
background:orange;
border:none;
border-radius:16px;
color:white;
font-size:20px;
cursor:pointer;
}

.verify{
color:#00ff88;
font-size:14px;
margin-left:5px;
cursor:pointer;
}

.typing{
opacity:0.7;
}

.auth{
position:fixed;
inset:0;
background:#0d0d0d;
display:flex;
justify-content:center;
align-items:center;
z-index:1000;
}

.authbox{
width:400px;
background:#111;
padding:30px;
border-radius:20px;
display:flex;
flex-direction:column;
gap:15px;
}

input{
padding:16px;
background:#1c1c1c;
border:none;
border-radius:14px;
color:white;
}

.small{
font-size:13px;
opacity:0.7;
}

</style>

</head>

<body>

<div class='auth' id='auth'>

<div class='authbox'>

<h1>🤖 Bloxy-bot</h1>

<input id='email' placeholder='Email'>
<input id='username' placeholder='Username'>
<input id='password' type='password' placeholder='Password'>

<button onclick='register()'>Create</button>
<button onclick='login()'>Login</button>
<button onclick='guest()'>Guest</button>

<div class='small'>
Bloxy-bot can make mistakes.Verify highly important information
</div>

</div>

</div>

<div class='sidebar'>

<div class='logo'>
🤖 Bloxy-bot
</div>

<div class='newchat' onclick='newChat()'>
➕ New Chat
</div>

<div class='conversations' id='conversations'></div>

<div class='account' id='account'>
👤 Guest
</div>

</div>

<div class='main'>

<div class='messages' id='messages'>
💬 Start chatting...
</div>

<div class='inputbar'>

<textarea
id='msg'
placeholder='Message Bloxy-bot...'></textarea>

<button onclick='send()'>➤</button>

</div>

</div>

<script>

let EMAIL='guest';
let CHAT='Main';

function guest(){

document.getElementById('auth').style.display='none';

}

async function register(){

let email=document.getElementById('email').value;
let username=document.getElementById('username').value;
let password=document.getElementById('password').value;

let r=await fetch('/register',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email,
username,
password
})
});

let d=await r.json();

if(d.success){

EMAIL=email;

document.getElementById('account').innerHTML=
`👤 ${username}
<span class='verify'
title='This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform'>
${d.verified ? '✔️':''}
</span>`;

document.getElementById('auth').style.display='none';

}else{
alert('Could not create account');
}

}

async function login(){

let email=document.getElementById('email').value;
let password=document.getElementById('password').value;

let r=await fetch('/login',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email,
password
})
});

let d=await r.json();

if(d.success){

EMAIL=email;

document.getElementById('account').innerHTML=
`👤 ${d.username}
<span class='verify'
title='This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform'>
${d.verified ? '✔️':''}
</span>`;

document.getElementById('auth').style.display='none';

}else{
alert('Wrong login');
}

}

function newChat(){

CHAT='Chat '+Date.now();

document.getElementById('messages').innerHTML='💬 Start chatting...';

}

async function send(){

let msg=document.getElementById('msg').value.trim();

if(!msg)return;

let box=document.getElementById('messages');

box.innerHTML += `
<div class='msg user'>
👤 ${msg}
</div>
`;

box.innerHTML += `
<div class='msg bot typing' id='typing'>
🤖 Bloxy-bot is typing...
</div>
`;

box.scrollTop=box.scrollHeight;

document.getElementById('msg').value='';

let r=await fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:EMAIL,
title:CHAT,
message:msg
})
});

let d=await r.json();

document.getElementById('typing').remove();

box.innerHTML += `
<div class='msg bot'>
🤖 ${d.reply}
</div>
`;

box.scrollTop=box.scrollHeight;

}

document.getElementById('msg').addEventListener('keydown',function(e){

if(e.key==='Enter'&&!e.shiftKey){

e.preventDefault();

send();

}

});

</script>

</body>
</html>
"""

# =========================================================
# EXTRA RUNTIME SYSTEMS
# =========================================================

for i in range(1,1001):

    globals()[f"runtime_feature_{i}"] = {
        "id": i,
        "enabled": True,
        "name": f"Bloxy Runtime {i}"
    }

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
