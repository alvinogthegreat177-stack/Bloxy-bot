from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback
import uuid
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
# OWNER VERIFIED ACCOUNT
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

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

class Auth(BaseModel):

    email: str
    password: str

class ChatRequest(BaseModel):

    email: str
    chat_id: str
    message: str

# =========================================================
# WIKIPEDIA
# =========================================================

def wikipedia_search(query):

    try:

        query = query.replace(" ", "_")

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=20
        )

        if r.status_code != 200:
            return ""

        data = r.json()

        return data.get("extract", "")

    except:

        return ""

# =========================================================
# TAVILY
# =========================================================

def tavily_search(query):

    if not TAVILY_API_KEY:
        return ""

    try:

        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 2
            },
            timeout=30
        )

        if r.status_code != 200:
            return ""

        data = r.json()

        results = data.get("results", [])

        text = []

        for item in results:

            content = item.get("content", "")

            if content:

                text.append(content)

        return "\n".join(text)

    except:

        return ""

# =========================================================
# NEWS
# =========================================================

def news_search(query):

    if not NEWS_API_KEY:
        return ""

    try:

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": 2
            },
            timeout=20
        )

        if r.status_code != 200:
            return ""

        data = r.json()

        articles = data.get("articles", [])

        text = []

        for a in articles:

            title = a.get("title", "")
            source = a.get("source", {}).get("name", "")

            if title:

                text.append(f"{title} - {source}")

        return "\n".join(text)

    except:

        return ""

# =========================================================
# WOLFRAM
# =========================================================

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

        if r.status_code != 200:
            return ""

        return r.text

    except:

        return ""

# =========================================================
# TOOL ROUTER
# =========================================================

def build_tool_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in [
        "who is",
        "what is",
        "history",
        "country",
        "city"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:

            context.append(
                f"WIKIPEDIA:\n{wiki}"
            )

    if any(x in text for x in [
        "news",
        "latest",
        "today",
        "trending"
    ]):

        news = news_search(prompt)

        if news:

            context.append(
                f"NEWS:\n{news}"
            )

    if any(x in text for x in [
        "solve",
        "calculate",
        "equation",
        "math",
        "physics"
    ]):

        wolfram = wolfram_search(prompt)

        if wolfram:

            context.append(
                f"WOLFRAM:\n{wolfram}"
            )

    if any(x in text for x in [
        "search",
        "internet",
        "online",
        "research",
        "web"
    ]):

        tav = tavily_search(prompt)

        if tav:

            context.append(
                f"TAVILY:\n{tav}"
            )

    return "\n\n".join(context)

# =========================================================
# AI SYSTEM
# =========================================================

def ask_ai(messages):

    if not OPENROUTER_API_KEY:

        return "OpenRouter API key missing."

    try:

        clean_messages = []

        for m in messages:

            role = str(m.get("role", "user"))
            content = str(m.get("content", "")).strip()

            if not content:
                continue

            clean_messages.append({
                "role": role,
                "content": content
            })

        if len(clean_messages) == 0:

            return "No valid messages."

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bloxy-bot.ai",
                "X-Title": "Bloxy-bot"
            },

            json={

                "model": "openrouter/auto",

                "messages": clean_messages,

                "temperature": 0.7,

                "max_tokens": 4500,

                "top_p": 1,

                "stream": False
            },

            timeout=120
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        if response.status_code != 200:

            try:

                err = response.json()

                return f"AI Error: {err}"

            except:

                return f"AI Error {response.status_code}"

        data = response.json()

        choices = data.get("choices")

        if not choices:

            return "No AI response choices."

        message = choices[0].get("message", {})

        content = message.get("content", "")

        if not content:

            return "Empty AI response."

        return content.strip()

    except Exception as e:

        print(traceback.format_exc())

        return f"Bloxy-bot AI system error: {str(e)}"

# =========================================================
# SIGNUP
# =========================================================

@app.post("/signup")
def signup(data: Auth):

    email = data.email.strip().lower()

    password = data.password.strip()

    if not email or not password:

        return {
            "ok": False,
            "error": "Missing email or password"
        }

    if email in users:

        return {
            "ok": False,
            "error": "Account already exists"
        }

    username = email.split("@")[0]

    users[email] = {
        "password": password,
        "username": username,
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
def login(data: Auth):

    email = data.email.strip().lower()

    password = data.password.strip()

    if email == OWNER_EMAIL:

        if password != OWNER_PASSWORD:

            return {
                "ok": False,
                "error": "Wrong password"
            }

        return {
            "ok": True,
            "username": "aTg",
            "verified": True,
            "email": OWNER_EMAIL
        }

    if email not in users:

        return {
            "ok": False,
            "error": "Account not found"
        }

    if users[email]["password"] != password:

        return {
            "ok": False,
            "error": "Wrong password"
        }

    return {
        "ok": True,
        "username": users[email]["username"],
        "verified": False,
        "email": email
    }

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    email = data.email
    chat_id = data.chat_id
    message = data.message

    if email not in chat_memory:

        chat_memory[email] = {}

    if chat_id not in chat_memory[email]:

        chat_memory[email][chat_id] = []

    history = chat_memory[email][chat_id]

    tool_context = build_tool_context(message)

    system_prompt = f"""

You are Bloxy-bot AI.

Rules:

- Speak formally and diplomatically
- Format replies vertically
- Use clean spacing
- Avoid huge paragraphs
- Be intelligent and modern
- Use emojis naturally
- Sound premium and advanced
- Never say:
"As an AI language model"

External Context:
{tool_context}

"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history

    messages.append({
        "role": "user",
        "content": message
    })

    reply = ask_ai(messages)

    history.append({
        "role": "user",
        "content": message
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

<meta name="viewport" content="width=device-width, initial-scale=1.0">

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

.container{
display:flex;
height:100vh;
}

.sidebar{
width:280px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
justify-content:space-between;
}

.side-top{
padding:12px;
overflow:auto;
}

.logo{
font-size:24px;
font-weight:bold;
margin-bottom:15px;
}

.newchat{
width:100%;
padding:14px;
background:#1e1e1e;
border:none;
border-radius:12px;
color:white;
cursor:pointer;
margin-bottom:14px;
transition:0.2s;
}

.newchat:hover{
background:#2a2a2a;
}

.chatitem{
padding:12px;
background:#1a1a1a;
border-radius:12px;
margin-top:8px;
display:flex;
justify-content:space-between;
align-items:center;
}

.chatname{
cursor:pointer;
flex:1;
overflow:hidden;
text-overflow:ellipsis;
white-space:nowrap;
}

.actions{
display:flex;
gap:5px;
}

.actionbtn{
background:transparent;
border:none;
color:white;
cursor:pointer;
font-size:14px;
}

.userbox{
padding:18px;
border-top:1px solid #222;
background:#101010;
}

.main{
flex:1;
display:flex;
flex-direction:column;
}

.messages{
flex:1;
overflow:auto;
padding:25px;
scroll-behavior:smooth;
}

.msg{
padding:16px;
margin-bottom:18px;
background:#1a1a1a;
border-radius:16px;
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
border-top:1px solid #222;
background:#111;
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

#auth{
position:fixed;
top:0;
left:0;
right:0;
bottom:0;
background:#000000dd;
display:flex;
justify-content:center;
align-items:center;
z-index:999;
backdrop-filter:blur(10px);
}

.authbox{
width:360px;
background:#171717;
padding:30px;
border-radius:22px;
box-shadow:0 0 40px rgba(0,0,0,0.5);
}

.authtitle{
font-size:28px;
font-weight:bold;
margin-bottom:18px;
}

.authinput{
width:100%;
padding:16px;
margin-top:12px;
border:none;
outline:none;
border-radius:14px;
background:#222;
color:white;
font-size:15px;
}

.authbtn{
width:100%;
padding:16px;
margin-top:14px;
border:none;
border-radius:14px;
background:#ff8c00;
color:white;
font-weight:bold;
cursor:pointer;
font-size:15px;
transition:0.2s;
}

.authbtn:hover{
opacity:0.9;
}

.badge{
width:18px;
height:18px;
display:inline-block;
vertical-align:middle;
margin-left:4px;
}

.username{
display:flex;
align-items:center;
gap:4px;
font-weight:bold;
}

@media(max-width:700px){

.sidebar{
width:90px;
}

.logo{
font-size:18px;
}

.chatname{
display:none;
}

}

</style>

</head>

<body>

<div id="auth">

<div class="authbox">

<div class="authtitle">
Bloxy-bot
</div>

<input
class="authinput"
id="email"
placeholder="Email"
>

<input
class="authinput"
id="password"
type="password"
placeholder="Password"
>

<button class="authbtn" onclick="signup()">
Signup
</button>

<button class="authbtn" onclick="login()">
Login
</button>

</div>

</div>

<div class="container">

<div class="sidebar">

<div class="side-top">

<div class="logo">
Bloxy-bot
</div>

<button class="newchat" onclick="newChat()">
+ New Chat
</button>

<div id="chatlist"></div>

</div>

<div class="userbox" id="userbox">
Guest
</div>

</div>

<div class="main">

<div class="messages" id="messages"></div>

<div class="input-area">

<input
class="inputbox"
id="message"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}"
>

<div class="notice">
Bloxy-bot can make mistakes. Double check just in case.
</div>

</div>

</div>

</div>

<script>

let currentUser = {
email:null,
username:"Guest",
verified:false
};

let currentChat = "main";

let chats = {
"main":[]
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

function updateUserBox(){

let html = `
<div class="username">
${currentUser.username}
${currentUser.verified ? verifiedBadge() : ""}
</div>
`;

document.getElementById("userbox").innerHTML = html;
}

const savedUser = localStorage.getItem("bloxy_user");

if(savedUser){

currentUser = JSON.parse(savedUser);

document.getElementById("auth").style.display = "none";

updateUserBox();
}

function signup(){

fetch("/signup",{

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

currentUser = {
email:d.email,
username:d.username,
verified:d.verified
};

localStorage.setItem(
"bloxy_user",
JSON.stringify(currentUser)
);

document.getElementById("auth").style.display = "none";

updateUserBox();

});

}

function newChat(){

let id = "Chat " + (Object.keys(chats).length + 1);

chats[id] = [];

currentChat = id;

renderChats();

render();

}

function renderChats(){

let box = document.getElementById("chatlist");

box.innerHTML = "";

for(let c in chats){

let wrap = document.createElement("div");

wrap.className = "chatitem";

let title = document.createElement("div");

title.className = "chatname";

title.innerText = c;

title.onclick = ()=>{

currentChat = c;

render();

};

let actions = document.createElement("div");

actions.className = "actions";

let rename = document.createElement("button");

rename.className = "actionbtn";

rename.innerText = "✏";

rename.onclick = ()=>{

let newName = prompt("Rename chat:", c);

if(!newName) return;

chats[newName] = chats[c];

delete chats[c];

if(currentChat === c){

currentChat = newName;
}

renderChats();

};

let del = document.createElement("button");

del.className = "actionbtn";

del.innerText = "🗑";

del.onclick = ()=>{

delete chats[c];

if(Object.keys(chats).length === 0){

chats["main"] = [];

currentChat = "main";

}else{

currentChat = Object.keys(chats)[0];

}

renderChats();

render();

};

actions.appendChild(rename);

actions.appendChild(del);

wrap.appendChild(title);

wrap.appendChild(actions);

box.appendChild(wrap);

}

}

async function send(){

let input = document.getElementById("message");

let msg = input.value.trim();

if(!msg){

return;
}

input.value = "";

chats[currentChat].push({
role:"user",
content:msg
});

render();

try{

let r = await fetch("/chat",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
email:currentUser.email,
chat_id:currentChat,
message:msg
})

});

let d = await r.json();

chats[currentChat].push({
role:"assistant",
content:d.reply
});

render();

}catch(e){

chats[currentChat].push({
role:"assistant",
content:"Bloxy-bot connection error."
});

render();

}

}

function render(){

let box = document.getElementById("messages");

box.innerHTML = "";

for(let m of chats[currentChat]){

let d = document.createElement("div");

d.className = "msg";

if(m.role === "user"){

d.innerHTML = `
<div class="username">
${currentUser.username}
${currentUser.verified ? verifiedBadge() : ""}
</div>

<div style="margin-top:10px;">
${m.content}
</div>
`;

}else{

d.innerHTML = `
<div class="username">
Bloxy-bot
</div>

<div style="margin-top:10px;">
${m.content}
</div>
`;

}

box.appendChild(d);

}

box.scrollTop = box.scrollHeight;

}

renderChats();

render();

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
