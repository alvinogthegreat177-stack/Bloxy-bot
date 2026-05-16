# =========================================================
# BLOXY-BOT FULL REWRITE
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import traceback
import json
import os

app = FastAPI()

# =========================================================
# API KEYS
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
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

# =========================================================
# LIVE SEARCH
# =========================================================

def gnews_search(query):

    if not GNEWS_API_KEY:
        return ""

    try:

        r = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "token": GNEWS_API_KEY,
                "lang": "en",
                "max": 5
            },
            timeout=20
        )

        data = r.json()

        text = []

        for a in data.get("articles", []):

            title = a.get("title", "")
            desc = a.get("description", "")

            text.append(
                f"{title}\n{desc}"
            )

        return "\n\n".join(text)

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
                "max_results": 5
            },
            timeout=20
        )

        data = r.json()

        results = data.get("results", [])

        text = []

        for x in results:

            text.append(
                x.get("content", "")
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
# CONTEXT ROUTER
# =========================================================

def build_context(prompt):

    text = prompt.lower()

    context = []

    news = gnews_search(prompt)

    if news:

        context.append(f"NEWS:\n{news}")

    web = tavily_search(prompt)

    if web:

        context.append(f"WEB:\n{web}")

    if any(x in text for x in [
        "math",
        "calculate",
        "equation",
        "solve",
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

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization":
                f"Bearer {OPENROUTER_API_KEY}",

                "Content-Type":
                "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 8999
            },
            timeout=60
        )

        data = response.json()

        if "choices" in data:

            return data["choices"][0] \
                ["message"]["content"]

        return str(data)

    except Exception:

        print(traceback.format_exc())

        return "Bloxy-bot AI error."

# =========================================================
# SIGNUP
# =========================================================

@app.post("/signup")
def signup(data: Signup):

    if data.email in users:

        return {
            "ok": False,
            "error": "Account exists"
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

    if users[data.email]["password"] \
        != data.password:

        return {
            "ok": False,
            "error": "Wrong password"
        }

    return {
        "ok": True,
        "username":
        users[data.email]["username"],
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

    if data.chat_id not in \
        chat_memory[data.email]:

        chat_memory[data.email] \
            [data.chat_id] = []

    history = \
        chat_memory[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI.

Rules:

- Use clean spacing
- Be intelligent
- Be modern
- Use current 2026 context
- Sports tables should be accurate
- Breaking news should use live data
- Use bullet points when useful
- Avoid giant paragraphs

Context:

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
# FRONTEND
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():

    return """

<!DOCTYPE html>
<html>

<head>

<title>Bloxy-bot</title>

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

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
}

.logo{
padding:20px;
font-size:30px;
font-weight:bold;
color:#00ff88;
text-shadow:0 0 18px #00ff88;
}

.newchat{
margin:15px;
padding:16px;
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
padding:15px;
border-radius:16px;
background:#1b1b1b;
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
border-radius:20px;
margin-bottom:18px;
line-height:1.7;
white-space:pre-wrap;
animation:fade 0.2s ease;
}

.assistant{
border-left:4px solid #00ff88;
}

.user{
border-left:4px solid #ff8800;
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
background:#1d1d1d;
color:white;
font-size:15px;
}

.helper{
font-size:12px;
opacity:0.45;
margin-top:10px;
text-align:center;
width:100%;
}

.typing{
padding:10px 25px;
font-size:14px;
opacity:0.7;
}

.auth{
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
border-radius:24px;
}

.authinput{
width:100%;
padding:16px;
border:none;
outline:none;
border-radius:16px;
background:#222;
color:white;
margin-top:12px;
}

.authbtn{
width:100%;
padding:16px;
border:none;
border-radius:16px;
background:#00ff88;
font-weight:bold;
cursor:pointer;
margin-top:12px;
}

.guestbtn{
width:100%;
padding:15px;
border:none;
border-radius:16px;
background:#222;
color:white;
cursor:pointer;
margin-top:12px;
}

.verified{
display:inline-flex;
align-items:center;
justify-content:center;
width:18px;
height:18px;
margin-left:6px;
filter:drop-shadow(0 0 6px #ff8800);
animation:pulse 2s infinite;
vertical-align:middle;
}

.verified svg{
width:18px;
height:18px;
}

@keyframes pulse{
0%{
transform:scale(1);
}
50%{
transform:scale(1.08);
}
100%{
transform:scale(1);
}
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
display:none;
}

}

</style>

</head>

<body>

<div class="auth" id="auth">

<div class="authbox">

<h2>Bloxy-bot</h2>

<input
id="username"
class="authinput"
placeholder="Username">

<input
id="email"
class="authinput"
placeholder="Email">

<input
id="password"
type="password"
class="authinput"
placeholder="Password">

<button
class="authbtn"
onclick="signup()">
Signup
</button>

<button
class="authbtn"
onclick="login()">
Login
</button>

<button
class="guestbtn"
onclick="guestMode()">
Stay Signed Out
</button>

</div>

</div>

<div class="container">

<div class="sidebar">

<div class="logo">
Bloxy-bot
</div>

<button
class="newchat"
onclick="newChat()">
+ New Chat
</button>

<div
class="chatlist"
id="chatlist">
</div>

<div class="userbox">

<div id="userbox">
Guest
</div>

<div>
⋮
</div>

</div>

</div>

<div class="main">

<div
class="messages"
id="messages">
</div>

<div
class="typing"
id="typing">
</div>

<div class="inputarea">

<input
id="message"
class="inputbox"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}">

<div class="helper">
Bloxy-bot can make mistakes.
Verify important information.
</div>

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

let u =
localStorage.getItem(
"bloxy_user"
);

if(u){

currentUser = JSON.parse(u);

document.getElementById(
"auth"
).style.display = "none";

}

let c =
localStorage.getItem(
"bloxy_chats"
);

if(c){

chats = JSON.parse(c);

}

}

function verifiedBadge(){

if(currentUser.verified){

return `
<span class="verified">
<svg viewBox="0 0 24 24"
fill="#ff8800">

<path d="
M12 0
L14.8 4.5
L20 4
L19.5 9.2
L24 12
L19.5 14.8
L20 20
L14.8 19.5
L12 24
L9.2 19.5
L4 20
L4.5 14.8
L0 12
L4.5 9.2
L4 4
L9.2 4.5
Z"/>

</svg>
</span>
`;

}

return "";

}

function updateUser(){

document.getElementById(
"userbox"
).innerHTML = `
${currentUser.username}
${verifiedBadge()}
`;

}

function renderChats(){

let box =
document.getElementById(
"chatlist"
);

box.innerHTML = "";

for(let c in chats){

let d =
document.createElement("div");

d.className = "chatitem";

d.innerHTML = c;

d.onclick = ()=>{

currentChat = c;

render();

};

box.appendChild(d);

}

}

function render(){

let box =
document.getElementById(
"messages"
);

box.innerHTML = "";

for(let m of chats[currentChat]){

let d =
document.createElement("div");

d.className =
"msg " +
(m.role==="assistant"
? "assistant"
: "user");

let name =
m.role==="assistant"
? "Bloxy-bot"
: currentUser.username;

let badge =
m.role==="user"
? verifiedBadge()
: "";

d.innerHTML = `
<b>
${name}
${badge}
</b>

<div style="margin-top:10px;">
${m.content.replace(/\\n/g,"<br>")}
</div>
`;

box.appendChild(d);

}

box.scrollTop =
box.scrollHeight;

saveLocal();

}

function newChat(){

let id =
"Chat " +
(Object.keys(chats).length+1);

chats[id] = [];

currentChat = id;

renderChats();
render();

}

function signup(){

fetch("/signup",{
method:"POST",
headers:{
"Content-Type":
"application/json"
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
"Content-Type":
"application/json"
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

document.getElementById(
"auth"
).style.display = "none";

updateUser();

saveLocal();

});

}

function guestMode(){

document.getElementById(
"auth"
).style.display = "none";

updateUser();

}

function send(){

let input =
document.getElementById(
"message"
);

let msg =
input.value.trim();

if(!msg){

return;

}

input.value = "";

chats[currentChat].push({
role:"user",
content:msg
});

render();

document.getElementById(
"typing"
).innerHTML =
"Bloxy-bot is typing...";

fetch("/chat",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
email:currentUser.email,
chat_id:currentChat,
message:msg
})
})
.then(r=>r.json())
.then(d=>{

document.getElementById(
"typing"
).innerHTML = "";

let box =
document.getElementById(
"messages"
);

let wrapper =
document.createElement("div");

wrapper.className =
"msg assistant";

wrapper.innerHTML = `
<b>Bloxy-bot</b>

<div id="streamingText"
style="margin-top:10px;">
</div>
`;

box.appendChild(wrapper);

let stream =
document.getElementById(
"streamingText"
);

let reply = "";

let i = 0;

let interval =
setInterval(()=>{

if(i < d.reply.length){

reply += d.reply[i];

stream.innerHTML =
reply.replace(/\\n/g,"<br>");

box.scrollTop =
box.scrollHeight;

i++;

}else{

clearInterval(interval);

chats[currentChat].push({
role:"assistant",
content:reply
});

saveLocal();

}

},8);

})
.catch(()=>{

document.getElementById(
"typing"
).innerHTML = "";

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

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
