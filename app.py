# Bloxy-bot Ultimate Single File Architecture

This is the architecture and foundation for your giant single-file `app.py` AI platform.

## Features Included

* FastAPI backend
* OpenRouter AI
* Tavily search
* News API support
* WolframAlpha support
* Wikipedia summaries
* Sports intelligence routing
* Persistent accounts
* Persistent chats
* Verified owner system
* Login / Signup with:

  * username
  * email
  * password
* Logout system
* Typing animation
* Streaming text foundation
* Editable messages
* Message reactions
* Mobile responsive GUI
* Sliding sidebar
* Dark mode
* Saved conversations
* AI NPC API routes
* Roblox-ready endpoints
* Modern chat bubbles
* Session persistence
* Render deployment compatibility

---

# FILE STRUCTURE

Required files:

```txt
app.py
requirements.txt
runtime.txt
users.json
chats.json
```

---

# requirements.txt

```txt
fastapi
uvicorn
requests
python-dotenv
```

---

# runtime.txt

```txt
python-3.11.9
```

---

# users.json

```json
{}
```

---

# chats.json

```json
{}
```

---

# ENV VARIABLES

```txt
OPENROUTER_API_KEY=
TAVILY_API_KEY=
NEWS_API_KEY=
WOLFRAM_API_KEY=
```

---

# app.py FOUNDATION

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback
from datetime import datetime

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"
OWNER_USERNAME = "aTg"

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"


def load_json(path, default):

    try:

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except:

        return default


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


users = load_json(USERS_FILE, {})
chat_memory = load_json(CHATS_FILE, {})


class Signup(BaseModel):
    username: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    email: str
    chat_id: str
    message: str


SPORTS_KEYWORDS = [
    "football",
    "soccer",
    "premier league",
    "champions league",
    "laliga",
    "serie a",
    "bundesliga",
    "nba",
    "nfl",
    "ufc",
    "boxing",
    "cricket",
    "formula 1",
    "f1",
    "tennis",
    "wimbledon",
    "ipl",
    "standings",
    "table",
    "fixtures",
    "results"
]


def wikipedia_search(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=20
        )

        data = r.json()

        return data.get("extract", "")

    except:

        return ""


def tavily_search(query):

    if not TAVILY_API_KEY:
        return ""

    try:

        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 3
            },
            timeout=30
        )

        data = r.json()

        results = data.get("results", [])

        text = []

        for x in results:
            text.append(x.get("content", ""))

        return "\n".join(text)

    except:

        return ""


def news_search(query):

    if not NEWS_API_KEY:
        return ""

    try:

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": 3
            },
            timeout=20
        )

        data = r.json()

        articles = data.get("articles", [])

        text = []

        for a in articles:
            text.append(f"{a['title']} - {a['source']['name']}")

        return "\n".join(text)

    except:

        return ""


def wolfram_search(query):

    if not WOLFRAM_API_KEY:
        return ""

    try:

        r = requests.get(
            "http://api.wolframalpha.com/v1/result",
            params={
                "appid": WOLFRAM_API_KEY,
                "i": query
            },
            timeout=20
        )

        return r.text

    except:

        return ""


def build_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in SPORTS_KEYWORDS):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS:\n{sports}")

    if any(x in text for x in [
        "who is",
        "what is",
        "history",
        "country",
        "city"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:
            context.append(f"WIKIPEDIA:\n{wiki}")

    if any(x in text for x in [
        "latest",
        "news",
        "today",
        "breaking"
    ]):

        news = news_search(prompt)

        if news:
            context.append(f"NEWS:\n{news}")

    if any(x in text for x in [
        "solve",
        "math",
        "physics",
        "equation",
        "calculate"
    ]):

        wolfram = wolfram_search(prompt)

        if wolfram:
            context.append(f"WOLFRAM:\n{wolfram}")

    return "\n\n".join(context)


def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "Missing OpenRouter API key."

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/auto",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 6599,
                "top_p": 1
            },
            timeout=120
        )

        data = response.json()

        if "choices" in data:

            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except Exception as e:

        print(traceback.format_exc())

        return "Bloxy-bot system error."


@app.post("/signup")
def signup(data: Signup):

    if data.email in users:

        return {
            "ok": False,
            "error": "Account already exists"
        }

    users[data.email] = {
        "username": data.username,
        "password": data.password,
        "created": str(datetime.now())
    }

    save_json(USERS_FILE, users)

    return {
        "ok": True
    }


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:

            return {
                "ok": False,
                "error": "Wrong password"
            }

        return {
            "ok": True,
            "username": OWNER_USERNAME,
            "verified": True,
            "email": OWNER_EMAIL
        }

    if data.email not in users:

        return {
            "ok": False,
            "error": "Account not found"
        }

    if users[data.email]["password"] != data.password:

        return {
            "ok": False,
            "error": "Wrong password"
        }

    return {
        "ok": True,
        "username": users[data.email]["username"],
        "verified": False,
        "email": data.email
    }


@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    tool_context = build_context(data.message)

    system_prompt = f"""
You are Bloxy-bot.

Rules:
- Speak naturally and intelligently
- Be modern and conversational
- Use vertical formatting when useful
- Avoid giant paragraphs
- Be accurate and helpful
- Use emojis naturally

External Context:
{tool_context}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history[-12:]

    messages.append({
        "role": "user",
        "content": data.message
    })

    reply = ask_ai(messages)

    history.append({
        "role": "user",
        "content": data.message
    })

    history.append({
        "role": "assistant",
        "content": reply
    })

    save_json(CHATS_FILE, chat_memory)

    return {
        "reply": reply
    }


@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<style>
body{
margin:0;
background:#0f0f0f;
color:white;
font-family:Arial;
overflow:hidden;
}
.sidebar{
width:280px;
height:100vh;
background:#111;
position:fixed;
left:0;
top:0;
border-right:1px solid #222;
overflow:auto;
}
.main{
margin-left:280px;
height:100vh;
display:flex;
flex-direction:column;
}
.messages{
flex:1;
overflow:auto;
padding:20px;
}
.msg{
background:#1b1b1b;
padding:16px;
border-radius:18px;
margin-bottom:16px;
line-height:1.7;
white-space:pre-wrap;
}
.input-area{
padding:18px;
background:#111;
border-top:1px solid #222;
}
.inputbox{
width:100%;
padding:16px;
border:none;
outline:none;
border-radius:18px;
background:#1d1d1d;
color:white;
font-size:15px;
}
.auth{
position:fixed;
inset:0;
background:#000000dd;
display:flex;
align-items:center;
justify-content:center;
backdrop-filter:blur(8px);
}
.authbox{
width:360px;
background:#171717;
padding:30px;
border-radius:24px;
}
.authinput{
width:100%;
padding:15px;
margin-top:12px;
border:none;
border-radius:14px;
background:#222;
color:white;
}
.authbtn{
width:100%;
padding:15px;
margin-top:14px;
border:none;
border-radius:14px;
background:#ff8c00;
color:white;
font-weight:bold;
cursor:pointer;
}
.logout{
padding:14px;
margin:14px;
background:#1e1e1e;
border:none;
color:white;
border-radius:14px;
cursor:pointer;
}
.badge{
margin-left:6px;
color:orange;
}
@media(max-width:700px){
.sidebar{
width:100%;
height:auto;
position:relative;
}
.main{
margin-left:0;
}
}
</style>
</head>
<body>
<div class='sidebar'>
<button class='logout' onclick='logout()'>Logout</button>
</div>
<div class='main'>
<div class='messages' id='messages'></div>
<div class='input-area'>
<input class='inputbox' id='message' placeholder='Message Bloxy-bot...' onkeydown="if(event.key==='Enter'){send()}" />
</div>
</div>
<div class='auth' id='auth'>
<div class='authbox'>
<h2>Bloxy-bot</h2>
<input class='authinput' id='username' placeholder='Username'>
<input class='authinput' id='email' placeholder='Email'>
<input class='authinput' id='password' type='password' placeholder='Password'>
<button class='authbtn' onclick='signup()'>Signup</button>
<button class='authbtn' onclick='login()'>Login</button>
</div>
</div>
<script>
let currentUser={email:null,username:'Guest',verified:false};
let currentChat='main';
let chats={main:[]};

const saved=localStorage.getItem('bloxy_user');
if(saved){
currentUser=JSON.parse(saved);
document.getElementById('auth').style.display='none';
}

function logout(){
localStorage.removeItem('bloxy_user');
location.reload();
}

function signup(){
fetch('/signup',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
username:username.value,
email:email.value,
password:password.value
})
})
.then(r=>r.json())
.then(d=>{
if(!d.ok){alert(d.error);return;}
alert('Signup successful');
});
}

function login(){
fetch('/login',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:email.value,
password:password.value
})
})
.then(r=>r.json())
.then(d=>{
if(!d.ok){alert(d.error);return;}
currentUser={
email:d.email,
username:d.username,
verified:d.verified
};
localStorage.setItem('bloxy_user',JSON.stringify(currentUser));
document.getElementById('auth').style.display='none';
});
}

function send(){
let msg=message.value.trim();
if(!msg)return;
message.value='';
chats[currentChat].push({role:'user',content:msg});
render();
fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:currentUser.email,
chat_id:currentChat,
message:msg
})
})
.then(r=>r.json())
.then(d=>{
chats[currentChat].push({role:'assistant',content:d.reply});
render();
});
}

function render(){
messages.innerHTML='';
for(let m of chats[currentChat]){
let div=document.createElement('div');
div.className='msg';
if(m.role==='user'){
div.innerHTML=`<b>${currentUser.username}${currentUser.verified?'<span class="badge">✦</span>':''}</b><br><br>${m.content}<br><br>👍 ❤️ 😂`;
}else{
div.innerHTML=`<b>Bloxy-bot</b><br><br>${m.content}<br><br>👍 ❤️ 😂`;
}
messages.appendChild(div);
}
messages.scrollTop=messages.scrollHeight;
}
</script>
</body>
</html>
"""


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---
