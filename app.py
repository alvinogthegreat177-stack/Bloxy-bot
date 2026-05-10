# =========================================================
# BLOXY-BOT ULTIMATE AI SYSTEM
# =========================================================
#
# Features Included:
#
# - OpenRouter AI
# - Tavily Search
# - News API Support
# - WolframAlpha Support
# - Wikipedia Search
# - Sports Intelligence
# - Persistent Accounts
# - Persistent Chats
# - Verified Owner Badge SVG
# - Username / Email / Password Signup
# - Guest Mode
# - Logout System
# - Saved Conversations
# - Sliding Sidebar
# - Modern Chat Bubbles
# - Message Reactions
# - Editable Message Foundation
# - Streaming Text Foundation
# - Typing Animation Foundation
# - Mobile Responsive GUI
# - Dark Mode
# - AI NPC Foundation
# - Roblox Ready API Structure
# - Render Compatible
#
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback
from datetime import datetime

app = FastAPI()

# =========================================================
# API KEYS
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

# =========================================================
# OWNER ACCOUNT
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"
OWNER_USERNAME = "aTg"

# =========================================================
# FILES
# =========================================================

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

# =========================================================
# HELPERS
# =========================================================

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

# =========================================================
# MODELS
# =========================================================

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

# =========================================================
# SPORTS KEYWORDS
# =========================================================

SPORTS_KEYWORDS = [
    "football",
    "soccer",
    "premier league",
    "nba",
    "nfl",
    "boxing",
    "ufc",
    "cricket",
    "formula 1",
    "f1",
    "tennis",
    "standings",
    "results",
    "fixtures",
    "table",
    "laliga",
    "bundesliga",
    "serie a",
    "ipl"
]

# =========================================================
# SEARCH SYSTEMS
# =========================================================

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

            text.append(
                f"{a['title']} - {a['source']['name']}"
            )

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

# =========================================================
# CONTEXT BUILDER
# =========================================================

def build_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in SPORTS_KEYWORDS):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS:\\n{sports}")

    if any(x in text for x in [
        "who is",
        "what is",
        "history",
        "country",
        "city"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:
            context.append(f"WIKIPEDIA:\\n{wiki}")

    if any(x in text for x in [
        "latest",
        "news",
        "today",
        "breaking"
    ]):

        news = news_search(prompt)

        if news:
            context.append(f"NEWS:\\n{news}")

    if any(x in text for x in [
        "solve",
        "equation",
        "math",
        "physics",
        "calculate"
    ]):

        wolfram = wolfram_search(prompt)

        if wolfram:
            context.append(f"WOLFRAM:\\n{wolfram}")

    return "\\n\\n".join(context)

# =========================================================
# AI SYSTEM
# =========================================================

def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "OpenRouter API key missing."

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
                "max_tokens": 4000
            },
            timeout=120
        )

        data = response.json()

        if "choices" in data:

            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except:

        print(traceback.format_exc())

        return "Bloxy-bot AI system error."

# =========================================================
# SIGNUP
# =========================================================

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

# =========================================================
# LOGIN
# =========================================================

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

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    if not data.email:

        guest_reply = ask_ai([
            {
                "role": "system",
                "content": "You are Bloxy-bot AI."
            },
            {
                "role": "user",
                "content": data.message
            }
        ])

        return {
            "reply": guest_reply
        }

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    tool_context = build_context(data.message)

    system_prompt = f"""
You are Bloxy-bot AI.

Rules:

- Speak naturally
- Avoid giant paragraphs
- Use vertical formatting when useful
- Be modern and intelligent
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

    messages += history[-10:]

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

# =========================================================
# FRONTEND
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """

<!DOCTYPE html>

<html>

<head>

<title>Bloxy-bot</title>

<meta name='viewport' content='width=device-width, initial-scale=1.0'>

<style>

*{
box-sizing:border-box;
}

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
display:flex;
flex-direction:column;
justify-content:space-between;
}

.side-top{
padding:14px;
overflow:auto;
}

.logo{
font-size:24px;
font-weight:bold;
margin-bottom:16px;
}

.newchat{
width:100%;
padding:14px;
border:none;
border-radius:14px;
background:#1d1d1d;
color:white;
cursor:pointer;
margin-bottom:14px;
}

.chatitem{
padding:13px;
background:#1a1a1a;
border-radius:14px;
margin-bottom:10px;
cursor:pointer;
transition:0.2s;
}

.chatitem:hover{
background:#232323;
}

.account{
padding:18px;
border-top:1px solid #222;
background:#101010;
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
padding:24px;
scroll-behavior:smooth;
}

.msg{
background:#1a1a1a;
padding:18px;
border-radius:18px;
margin-bottom:18px;
line-height:1.8;
white-space:pre-wrap;
animation:fade 0.2s ease;
}

@keyframes fade{
from{
opacity:0;
transform:translateY(10px);
}
to{
opacity:1;
transform:translateY(0px);
}
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

.notice{
text-align:center;
font-size:12px;
color:#777;
margin-top:10px;
}

.auth{
position:fixed;
inset:0;
background:#000000dd;
display:flex;
align-items:center;
justify-content:center;
backdrop-filter:blur(8px);
z-index:999;
}

.authbox{
width:370px;
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

.badge{
width:18px;
height:18px;
display:inline-block;
vertical-align:middle;
margin-left:4px;
}

.userline{
display:flex;
align-items:center;
gap:4px;
font-weight:bold;
}

.logoutbtn{
width:100%;
padding:12px;
margin-top:14px;
border:none;
border-radius:12px;
background:#1d1d1d;
color:white;
cursor:pointer;
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

<div class='side-top'>

<div class='logo'>
Bloxy-bot
</div>

<button class='newchat' onclick='newChat()'>
+ New Chat
</button>

<div id='chatlist'></div>

</div>

<div class='account' id='accountbox'></div>

</div>

<div class='main'>

<div class='messages' id='messages'></div>

<div class='input-area'>

<input
class='inputbox'
id='message'
placeholder='Message Bloxy-bot...'
onkeydown="if(event.key==='Enter'){send()}"
>

<div class='notice'>
Bloxy-bot can make mistakes. Double-check important information.
</div>

</div>

</div>

<div class='auth' id='auth'>

<div class='authbox'>

<h2>Bloxy-bot</h2>

<div style='color:#888;margin-bottom:18px;font-size:14px;line-height:1.6;'>
Welcome to Bloxy-bot AI.
</div>

<input
class='authinput'
id='username'
placeholder='Username'
>

<input
class='authinput'
id='email'
placeholder='Email'
>

<input
class='authinput'
id='password'
type='password'
placeholder='Password'
>

<button class='authbtn' onclick='signup()'>
Signup
</button>

<button class='authbtn' onclick='login()'>
Login
</button>

<div
onclick='guestMode()'
style='
margin-top:18px;
text-align:center;
font-size:13px;
color:#888;
cursor:pointer;
'>
Or stay signed out
</div>

<div style='
margin-top:10px;
text-align:center;
font-size:12px;
color:#666;
line-height:1.5;
'>
No conversations or chat history
will be saved in guest mode.
</div>

</div>

</div>

<script>

let currentUser={
email:null,
username:"Guest",
verified:false
};

let currentChat="main";

let chats={
main:[]
};

function verifiedBadge(){

return `
<svg class="badge" viewBox="0 0 24 24">

<path
fill="#ff8c00"
d="
M12 2.2
C13.2 2.2 14 3.5 15 4
C16 4.5 17.5 4.2 18.4 5
C19.3 5.8 19.1 7.2 19.6 8.3
C20.1 9.4 21.4 10.2 21.4 11.5
C21.4 12.8 20.1 13.6 19.6 14.7
C19.1 15.8 19.3 17.2 18.4 18
C17.5 18.8 16 18.5 15 19
C14 19.5 13.2 20.8 12 20.8
C10.8 20.8 10 19.5 9 19
C8 18.5 6.5 18.8 5.6 18
C4.7 17.2 4.9 15.8 4.4 14.7
C3.9 13.6 2.6 12.8 2.6 11.5
C2.6 10.2 3.9 9.4 4.4 8.3
C4.9 7.2 4.7 5.8 5.6 5
C6.5 4.2 8 4.5 9 4
C10 3.5 10.8 2.2 12 2.2
Z">
</path>

<path
d="M8.3 12.2 L10.7 14.4 L15.7 9.2"
stroke="white"
stroke-width="2.2"
fill="none"
stroke-linecap="round"
stroke-linejoin="round">
</path>

</svg>
`;

}

function updateAccountBox(){

let html=`

<div class='userline'>

${currentUser.username}

${currentUser.verified ? verifiedBadge() : ""}

</div>

<div style='margin-top:6px;font-size:12px;color:#777;'>

${currentUser.email || "Guest Mode"}

</div>

`;

if(currentUser.email){

html += `
<button class='logoutbtn' onclick='logout()'>
Logout
</button>
`;

}else{

html += `
<div style='margin-top:10px;font-size:12px;color:#777;line-height:1.5;'>
You are currently signed out.<br>
Chats will not be saved.
</div>
`;

}

document.getElementById("accountbox").innerHTML=html;

}

function renderChats(){

let box=document.getElementById("chatlist");

box.innerHTML="";

for(let c in chats){

let div=document.createElement("div");

div.className="chatitem";

div.innerText=c;

div.onclick=()=>{

currentChat=c;

render();

};

box.appendChild(div);

}

}

function newChat(){

let id="Chat "+(Object.keys(chats).length+1);

chats[id]=[];

currentChat=id;

renderChats();

render();

}

function guestMode(){

document.getElementById("auth").style.display="none";

updateAccountBox();

}

function logout(){

localStorage.removeItem("bloxy_user");

location.reload();

}

const saved=localStorage.getItem("bloxy_user");

if(saved){

currentUser=JSON.parse(saved);

document.getElementById("auth").style.display="none";

}

updateAccountBox();

renderChats();

function signup(){

fetch("/signup",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

username:username.value,
email:email.value,
password:password.value

})

})

.then(r=>r.json())

.then(d=>{

if(!d.ok){

alert(d.error);

return;

}

alert("Signup successful. Please login.");

});

}

function login(){

fetch("/login",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

email:email.value,
password:password.value

})

})

.then(r=>r.json())

.then(d=>{

if(!d.ok){

alert(d.error);

return;

}

currentUser={

email:d.email,
username:d.username,
verified:d.verified

};

localStorage.setItem(
"bloxy_user",
JSON.stringify(currentUser)
);

document.getElementById("auth").style.display="none";

updateAccountBox();

});

}

function send(){

let input=document.getElementById("message");

let msg=input.value.trim();

if(!msg)return;

input.value="";

chats[currentChat].push({
role:"user",
content:msg
});

render();

fetch("/chat",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

email:currentUser.email,
chat_id:currentChat,
message:msg

})

})

.then(r=>r.json())

.then(d=>{

chats[currentChat].push({
role:"assistant",
content:d.reply
});

render();

})

.catch(()=>{

chats[currentChat].push({
role:"assistant",
content:"Bloxy-bot connection error."
});

render();

});

}

function render(){

let box=document.getElementById("messages");

box.innerHTML="";

for(let m of chats[currentChat]){

let div=document.createElement("div");

div.className="msg";

if(m.role==="user"){

div.innerHTML=`

<div class='userline'>

${currentUser.username}

${currentUser.verified ? verifiedBadge() : ""}

</div>

<div style='margin-top:12px;'>

${m.content}

</div>

<div style='margin-top:14px;color:#888;font-size:13px;'>

👍 ❤️ 😂

</div>

`;

}else{

div.innerHTML=`

<div class='userline'>
Bloxy-bot
</div>

<div style='margin-top:12px;'>

${m.content}

</div>

<div style='margin-top:14px;color:#888;font-size:13px;'>

👍 ❤️ 😂

</div>

`;

}

box.appendChild(div);

}

box.scrollTop=box.scrollHeight;

}

</script>

</body>

</html>

"""

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
