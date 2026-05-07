from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import uuid

app = FastAPI()

# ======================================================
# ENVIRONMENT VARIABLES
# ======================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

# ======================================================
# OWNER ACCOUNT
# ======================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

# ======================================================
# DATABASE
# ======================================================

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

users = load_json(USERS_FILE, {})
chat_memory = load_json(CHATS_FILE, {})

# ======================================================
# MODELS
# ======================================================

class Auth(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    email: str
    chat_id: str
    message: str

# ======================================================
# TOOLS
# ======================================================

def wikipedia_search(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        )

        data = r.json()

        if "extract" in data:
            return data["extract"]

    except:
        pass

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
            }
        )

        data = r.json()

        articles = data.get("articles", [])

        if not articles:
            return ""

        output = []

        for a in articles:
            output.append(
                f"{a['title']} - {a.get('source', {}).get('name','News')}"
            )

        return "\n".join(output)

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
            }
        )

        data = r.json()

        results = data.get("results", [])

        output = []

        for x in results:
            output.append(x.get("content", ""))

        return "\n".join(output)

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
            }
        )

        return r.text

    except:
        return ""

# ======================================================
# AI BRAIN
# ======================================================

def ask_groq(messages):

    try:

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": messages,
                "temperature": 0.7
            },
            timeout=60
        )

        data = r.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return "Bloxy-bot could not generate a response."

    except Exception:
        return "Bloxy-bot is temporarily unavailable."

# ======================================================
# SMART ROUTER
# ======================================================

def build_tool_context(prompt):

    text = prompt.lower()

    context = []

    # WIKIPEDIA
    if any(x in text for x in [
        "who is",
        "what is",
        "history",
        "country",
        "city",
        "person"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:
            context.append(
                f"WIKIPEDIA:\n{wiki}"
            )

    # NEWS
    if any(x in text for x in [
        "news",
        "latest",
        "today",
        "current",
        "trending"
    ]):

        news = news_search(prompt)

        if news:
            context.append(
                f"NEWS:\n{news}"
            )

    # WOLFRAM
    if any(x in text for x in [
        "solve",
        "equation",
        "calculate",
        "math",
        "physics"
    ]):

        wolfram = wolfram_search(prompt)

        if wolfram:
            context.append(
                f"WOLFRAM:\n{wolfram}"
            )

    # TAVILY
    if any(x in text for x in [
        "search",
        "internet",
        "web",
        "online",
        "research"
    ]):

        tav = tavily_search(prompt)

        if tav:
            context.append(
                f"TAVILY:\n{tav}"
            )

    return "\n\n".join(context)

# ======================================================
# SIGNUP
# ======================================================

@app.post("/signup")
def signup(data: Auth):

    if data.email in users:
        return {
            "ok": False,
            "error": "User already exists"
        }

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0]
    }

    save_json(USERS_FILE, users)

    return {
        "ok": True
    }

# ======================================================
# LOGIN
# ======================================================

@app.post("/login")
def login(data: Auth):

    # VERIFIED OWNER ACCOUNT
    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:
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

    # NORMAL USERS
    if data.email not in users:
        return {
            "ok": False,
            "error": "User not found"
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

# ======================================================
# CHAT
# ======================================================

@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    tool_context = build_tool_context(data.message)

    system_prompt = f"""
You are Bloxy-bot AI.

Rules:
- Be intelligent
- Be diplomatic
- Use vertical formatting
- Use emojis naturally
- Be modern and conversational
- Never say 'As an AI language model'

External tool context:
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
        "content": data.message
    })

    reply = ask_groq(messages)

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

# ======================================================
# FRONTEND
# ======================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

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
cursor:pointer;
transition:0.2s;
}

.chatitem:hover{
background:#252525;
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
line-height:1.7;
animation:fade 0.18s ease;
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
}

.authbox{
width:350px;
background:#171717;
padding:25px;
border-radius:20px;
}

.authinput{
width:100%;
padding:15px;
margin-top:10px;
border:none;
outline:none;
border-radius:12px;
background:#222;
color:white;
}

.authbtn{
width:100%;
padding:15px;
margin-top:12px;
border:none;
border-radius:12px;
background:#ff8c00;
color:white;
font-weight:bold;
cursor:pointer;
}

.badge{
width:16px;
height:16px;
vertical-align:middle;
margin-left:5px;
}

</style>
</head>

<body>

<div id="auth">

<div class="authbox">

<h2>Bloxy-bot</h2>

<input class="authinput" id="email" placeholder="Email">

<input class="authinput" id="password" type="password" placeholder="Password">

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
<path fill="#ff8c00"
d="M12 2 L15 8 L22 9 L17 13 L18 20 L12 16 L6 20 L7 13 L2 9 L9 8 Z"/>
<path d="M9 12l2 2 4-5"
stroke="white"
stroke-width="2"
fill="none"/>
</svg>
`;
}

function updateUserBox(){

let html = currentUser.username;

if(currentUser.verified){
html += verifiedBadge();
}

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

alert("Signup successful.");
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

let id = "chat_" + Date.now();

chats[id] = [];

currentChat = id;

renderChats();

render();
}

function renderChats(){

let box = document.getElementById("chatlist");

box.innerHTML = "";

for(let c in chats){

let d = document.createElement("div");

d.className = "chatitem";

d.innerText = c;

d.onclick = ()=>{
currentChat = c;
render();
};

box.appendChild(d);
}
}

function send(){

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
});
}

function render(){

let box = document.getElementById("messages");

box.innerHTML = "";

for(let m of chats[currentChat]){

let d = document.createElement("div");

d.className = "msg";

if(m.role === "user"){

let name = currentUser.username;

if(currentUser.verified){
name += verifiedBadge();
}

d.innerHTML = `
<b>${name}</b>
<br><br>
${m.content}
`;

}else{

d.innerHTML = `
<b>Bloxy-bot</b>
<br><br>
${m.content}
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

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
