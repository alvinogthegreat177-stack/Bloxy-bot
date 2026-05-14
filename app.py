from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback

app = FastAPI()

# =========================================================
# API KEYS
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

# =========================================================
# OWNER
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


class RenameChat(BaseModel):
    email: str
    old_chat: str
    new_chat: str


class DeleteChat(BaseModel):
    email: str
    chat_id: str


# =========================================================
# SEARCH TOOLS
# =========================================================

def wikipedia_search(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=10
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
            timeout=20
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
# SMART ROUTER
# =========================================================

def build_context(prompt):

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
            context.append(f"WIKIPEDIA:\n{wiki}")

    if any(x in text for x in [
        "news",
        "latest",
        "today",
        "trending"
    ]):

        news = news_search(prompt)

        if news:
            context.append(f"NEWS:\n{news}")

    if any(x in text for x in [
        "football",
        "sports",
        "soccer",
        "nba",
        "f1",
        "boxing",
        "tennis",
        "cricket",
        "ufc"
    ]):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS:\n{sports}")

    if any(x in text for x in [
        "solve",
        "equation",
        "math",
        "calculate",
        "physics"
    ]):

        wolf = wolfram_search(prompt)

        if wolf:
            context.append(f"WOLFRAM:\n{wolf}")

    return "\n\n".join(context)

# =========================================================
# AI
# =========================================================

def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "OpenRouter API key missing."

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bloxy-bot.onrender.com",
                "X-Title": "Bloxy-bot"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 8650
            },
            timeout=60
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except Exception:

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
        "password": data.password
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

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI.

Rules:

- Speak naturally
- Use clean spacing
- Be modern
- Be intelligent
- Avoid giant paragraphs
- Be accurate
- Use emojis naturally

External Context:

{context}

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
# RENAME CHAT
# =========================================================

@app.post("/rename_chat")
def rename_chat(data: RenameChat):

    if data.email not in chat_memory:
        return {"ok": False}

    if data.old_chat not in chat_memory[data.email]:
        return {"ok": False}

    chat_memory[data.email][data.new_chat] = \
        chat_memory[data.email][data.old_chat]

    del chat_memory[data.email][data.old_chat]

    save_json(CHATS_FILE, chat_memory)

    return {"ok": True}

# =========================================================
# DELETE CHAT
# =========================================================

@app.post("/delete_chat")
def delete_chat(data: DeleteChat):

    if data.email not in chat_memory:
        return {"ok": False}

    if data.chat_id not in chat_memory[data.email]:
        return {"ok": False}

    del chat_memory[data.email][data.chat_id]

    save_json(CHATS_FILE, chat_memory)

    return {"ok": True}

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
font-family:Arial;
color:white;
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
transition:0.3s;
}

.logo{
font-size:28px;
font-weight:bold;
padding:20px;
color:#00ff88;
text-shadow:0 0 15px #00ff88;
}

.newchat{
margin:14px;
padding:15px;
border:none;
border-radius:16px;
background:#1d1d1d;
color:white;
cursor:pointer;
font-size:15px;
}

.chatlist{
flex:1;
overflow:auto;
padding:10px;
}

.chatitem{
padding:14px;
background:#1a1a1a;
border-radius:14px;
margin-bottom:10px;
cursor:pointer;
transition:0.2s;
}

.chatitem:hover{
background:#252525;
}

.userbox{
padding:16px;
border-top:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
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
}

.msg{
background:#1a1a1a;
padding:18px;
border-radius:18px;
margin-bottom:18px;
line-height:1.7;
white-space:pre-wrap;
animation:fade 0.2s ease;
position:relative;
}

.reactions{
margin-top:10px;
display:flex;
gap:10px;
font-size:14px;
opacity:0.7;
}

.inputarea{
padding:18px;
background:#111;
border-top:1px solid #222;
}

.inputbox{
width:100%;
padding:18px;
border:none;
outline:none;
border-radius:18px;
background:#1e1e1e;
color:white;
font-size:15px;
}

.typing{
padding:10px;
font-size:14px;
opacity:0.7;
}

.auth{
position:fixed;
top:0;
left:0;
right:0;
bottom:0;
background:#000000cc;
display:flex;
justify-content:center;
align-items:center;
backdrop-filter:blur(10px);
z-index:999;
}

.authbox{
width:360px;
background:#171717;
padding:30px;
border-radius:24px;
}

.authinput{
width:100%;
padding:16px;
border:none;
outline:none;
border-radius:14px;
background:#222;
color:white;
margin-top:12px;
}

.authbtn{
width:100%;
padding:16px;
border:none;
border-radius:14px;
background:#00ff88;
margin-top:12px;
cursor:pointer;
font-weight:bold;
}

.guestbtn{
width:100%;
padding:14px;
margin-top:12px;
background:#222;
border:none;
border-radius:14px;
color:white;
cursor:pointer;
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

@media(max-width:700px){

.sidebar{
position:fixed;
left:-280px;
top:0;
bottom:0;
z-index:999;
}

.sidebar.open{
left:0;
}

.main{
width:100%;
}

}

</style>

</head>

<body>

<div class="auth" id="auth">

<div class="authbox">

<h2>Bloxy-bot</h2>

<input id="username"
class="authinput"
placeholder="Username">

<input id="email"
class="authinput"
placeholder="Email">

<input id="password"
type="password"
class="authinput"
placeholder="Password">

<button class="authbtn" onclick="signup()">
Signup
</button>

<button class="authbtn" onclick="login()">
Login
</button>

<button class="guestbtn" onclick="guestMode()">
Stay Signed Out
</button>

</div>

</div>

<div class="container">

<div class="sidebar" id="sidebar">

<div class="logo">
Bloxy-bot
</div>

<button class="newchat" onclick="newChat()">
+ New Chat
</button>

<div class="chatlist" id="chatlist"></div>

<div class="userbox">

<div id="userbox">
Guest
</div>

<div onclick="logout()" style="cursor:pointer;">
⋮
</div>

</div>

</div>

<div class="main">

<div class="messages" id="messages"></div>

<div class="typing" id="typing"></div>

<div class="inputarea">

<input
id="message"
class="inputbox"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}">

</div>

</div>

</div>

<script>

let currentUser = {
email:"guest",
username:"Guest",
verified:false
};

let currentChat = "Main";

let chats = {
"Main":[]
};

function saveLocal(){

localStorage.setItem(
"bloxy_user",
JSON.stringify(currentUser)
);

localStorage.setItem(
"bloxy_chats",
JSON.stringify(chats)
);

}

function loadLocal(){

let u = localStorage.getItem("bloxy_user");

if(u){

currentUser = JSON.parse(u);

document.getElementById("auth").style.display = "none";

}

let c = localStorage.getItem("bloxy_chats");

if(c){

chats = JSON.parse(c);

}

}

function updateUser(){

document.getElementById("userbox").innerHTML =
currentUser.username;

}

function renderChats(){

let box = document.getElementById("chatlist");

box.innerHTML = "";

for(let c in chats){

let d = document.createElement("div");

d.className = "chatitem";

d.innerHTML = `
<div>${c}</div>
`;

d.onclick = ()=>{

currentChat = c;

render();

};

box.appendChild(d);

}

}

function render(){

let box = document.getElementById("messages");

box.innerHTML = "";

for(let m of chats[currentChat]){

let d = document.createElement("div");

d.className = "msg";

d.innerHTML = `
<b>${m.role==="user" ? currentUser.username : "Bloxy-bot"}</b>

<div style="margin-top:10px;">
${m.content}
</div>

<div class="reactions">
👍 ❤️ 😂
</div>
`;

box.appendChild(d);

}

box.scrollTop = box.scrollHeight;

saveLocal();

}

function newChat(){

let id = "Chat " + (Object.keys(chats).length + 1);

chats[id] = [];

currentChat = id;

renderChats();

render();

}

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

alert("Signup successful");

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

document.getElementById("auth").style.display = "none";

updateUser();

saveLocal();

});

}

function guestMode(){

document.getElementById("auth").style.display = "none";

updateUser();

}

function logout(){

localStorage.clear();

location.reload();

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

document.getElementById("typing").innerHTML =
"Bloxy-bot is typing...";

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

document.getElementById("typing").innerHTML = "";

let reply = "";

let i = 0;

chats[currentChat].push({
role:"assistant",
content:""
});

let interval = setInterval(()=>{

if(i < d.reply.length){

reply += d.reply[i];

chats[currentChat][
chats[currentChat].length - 1
].content = reply;

render();

i++;

}else{

clearInterval(interval);

}

},10);

})
.catch(()=>{

document.getElementById("typing").innerHTML = "";

});

}

loadLocal();

updateUser();

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
