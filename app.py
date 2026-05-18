# =========================================================
# BLOXY-BOT ULTIMATE AI 2026
# FULL APP.PY
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import traceback
import uvicorn
import json
import os
import time

app = FastAPI()

# =========================================================
# ENV VARIABLES
# =========================================================

SECRET_API_KEY = os.getenv("SECRET_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

EXA_API_KEY = os.getenv("EXA_API_KEY")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")

THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")

ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")

SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")

# =========================================================
# FILES
# =========================================================

USERS_FILE = "users.json"

CHATS_FILE = "chats.json"

# =========================================================
# LOAD JSON
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
# OWNER
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"

OWNER_PASSWORD = "alvindev17.og"

OWNER_USERNAME = "aTg"

# =========================================================
# MODELS
# =========================================================

AI_MODELS = [

{
"provider":"groq",
"model":"llama-3.3-70b-versatile"
},

{
"provider":"openrouter",
"model":"deepseek/deepseek-chat-v3-0324:free"
},

{
"provider":"openrouter",
"model":"qwen/qwen3-32b"
},

{
"provider":"openrouter",
"model":"moonshotai/kimi-k2"
}

]

# =========================================================
# REQUEST MODELS
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
            timeout=10
        )

        return r.text[:1500]

    except:

        return ""


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
                "max": 3
            },
            timeout=10
        )

        return r.text[:1500]

    except:

        return ""


def newsapi_search(query):

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
            timeout=10
        )

        return r.text[:1500]

    except:

        return ""


def wikipedia_search(query):

    try:

        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query,
            timeout=10
        )

        return r.json().get("extract", "")

    except:

        return ""


def exa_search(query):

    if not EXA_API_KEY:

        return ""

    try:

        r = requests.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": EXA_API_KEY
            },
            json={
                "query": query,
                "numResults": 3
            },
            timeout=10
        )

        return r.text[:1500]

    except:

        return ""


def finance_search():

    if not FINNHUB_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://finnhub.io/api/v1/news",
            params={
                "category":"general",
                "token":FINNHUB_API_KEY
            },
            timeout=10
        )

        return r.text[:1200]

    except:

        return ""


def wolfram_search(query):

    key = WOLFRAM_API_KEY or WOLFRAM_APP_ID

    if not key:

        return ""

    try:

        r = requests.get(
            "http://api.wolframalpha.com/v1/result",
            params={
                "appid":key,
                "i":query
            },
            timeout=10
        )

        return r.text

    except:

        return ""

# =========================================================
# SPORTS
# =========================================================

def premier_league_table():

    try:

        r = requests.get(
            "https://v3.football.api-sports.io/standings",
            headers={
                "x-apisports-key":
                APISPORTS_API_KEY
            },
            params={
                "league":39,
                "season":2025
            },
            timeout=10
        )

        data = r.json()

        table = data["response"][0]["league"]["standings"][0]

        text = "Premier League Table\n\n"

        for t in table[:20]:

            text += f"{t['rank']}. {t['team']['name']} - {t['points']} pts\n"

        return text

    except:

        return "Could not load Premier League table."


def sports_context(query):

    context = []

    try:

        if THESPORTSDB_API_KEY:

            r = requests.get(
                f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
                params={
                    "t":query
                },
                timeout=10
            )

            context.append(r.text[:1000])

    except:

        pass

    try:

        if ALLSPORTS_API_KEY:

            r = requests.get(
                "https://apiv2.allsportsapi.com/football/",
                params={
                    "met":"Livescore",
                    "APIkey":ALLSPORTS_API_KEY
                },
                timeout=10
            )

            context.append(r.text[:1000])

    except:

        pass

    try:

        if ODDS_API_KEY:

            r = requests.get(
                "https://api.the-odds-api.com/v4/sports/",
                params={
                    "apiKey":ODDS_API_KEY
                },
                timeout=10
            )

            context.append(r.text[:1000])

    except:

        pass

    try:

        if APISPORTS_API_KEY:

            r = requests.get(
                "https://v3.football.api-sports.io/fixtures",
                headers={
                    "x-apisports-key":
                    APISPORTS_API_KEY
                },
                params={
                    "live":"all"
                },
                timeout=10
            )

            context.append(r.text[:1000])

    except:

        pass

    return "\n\n".join(context)

# =========================================================
# CONTEXT
# =========================================================

def build_context(prompt):

    items = [

        tavily_search(prompt),

        gnews_search(prompt),

        newsapi_search(prompt),

        wikipedia_search(prompt),

        exa_search(prompt),

        finance_search(),

        wolfram_search(prompt),

        sports_context(prompt)

    ]

    return "\n\n".join([x for x in items if x])

# =========================================================
# AI
# =========================================================

def groq_chat(model, messages):

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization":
            f"Bearer {GROQ_API_KEY}",
            "Content-Type":
            "application/json"
        },
        json={
            "model":
            model,

            "messages":
            messages,

            "temperature":
            0.6,

            "max_tokens":
            350
        },
        timeout=40
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]


def openrouter_chat(model, messages):

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type":
            "application/json"
        },
        json={
            "model":
            model,

            "messages":
            messages,

            "temperature":
            0.6,

            "max_tokens":
            350
        },
        timeout=40
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]


def ask_ai(messages):

    for model in AI_MODELS:

        try:

            if model["provider"] == "groq":

                return groq_chat(
                    model["model"],
                    messages
                )

            if model["provider"] == "openrouter":

                return openrouter_chat(
                    model["model"],
                    messages
                )

        except Exception:

            print(traceback.format_exc())

            continue

    return "Bloxy-bot AI systems are overloaded."

# =========================================================
# AUTH
# =========================================================

@app.post("/signup")
def signup(data: Signup):

    if data.email in users:

        return {
            "ok":False
        }

    users[data.email] = {

        "username":
        data.username,

        "password":
        data.password,

        "created":
        time.time()

    }

    save_json(USERS_FILE, users)

    return {
        "ok":True
    }


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:

            return {
                "ok":False
            }

        return {

            "ok":True,

            "username":OWNER_USERNAME,

            "verified":True,

            "email":OWNER_EMAIL

        }

    if data.email not in users:

        return {
            "ok":False
        }

    if users[data.email]["password"] != data.password:

        return {
            "ok":False
        }

    return {

        "ok":True,

        "username":
        users[data.email]["username"],

        "verified":False,

        "email":data.email

    }

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    lower = data.message.lower()

    if "pl table" in lower or "premier league table" in lower:

        return {
            "reply":
            premier_league_table()
        }

    if data.email not in chat_memory:

        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:

        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI.

RULES:

- NEVER define every word
- Talk naturally
- Give direct answers
- Use live context aggressively
- Sports answers must feel live
- Be modern
- Be fast
- Do not act like a dictionary
- Avoid robotic explanations
- Only explain deeply if user asks

Context:

{context}

"""

    messages = [

        {
            "role":"system",
            "content":system_prompt
        }

    ]

    messages += history[-6:]

    messages.append({

        "role":"user",

        "content":data.message

    })

    reply = ask_ai(messages)

    history.append({

        "role":"user",

        "content":data.message

    })

    history.append({

        "role":"assistant",

        "content":reply

    })

    save_json(CHATS_FILE, chat_memory)

    return {

        "reply":reply

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

body{
margin:0;
background:#0d0d0d;
font-family:Arial;
color:white;
overflow:hidden;
}

.container{
display:flex;
height:100vh;
}

.sidebar{
width:290px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.logo{
padding:24px;
font-size:28px;
font-weight:bold;
color:#00ff88;
}

.newchat{
margin:15px;
padding:16px;
border:none;
border-radius:18px;
background:#1e1e1e;
color:white;
cursor:pointer;
}

.chatlist{
flex:1;
overflow:auto;
padding:12px;
}

.chatitem{
padding:16px;
background:#1a1a1a;
border-radius:18px;
margin-bottom:12px;
display:flex;
justify-content:space-between;
align-items:center;
cursor:pointer;
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
padding:18px;
background:#1a1a1a;
border-radius:18px;
margin-bottom:18px;
white-space:pre-wrap;
line-height:1.7;
}

.user{
border-left:4px solid orange;
}

.assistant{
border-left:4px solid #00ff88;
}

.inputarea{
padding:18px;
border-top:1px solid #222;
background:#111;
}

.inputrow{
display:flex;
gap:10px;
}

.inputbox{
flex:1;
padding:18px;
border:none;
outline:none;
border-radius:18px;
background:#1d1d1d;
color:white;
}

.sendbtn{
width:65px;
border:none;
border-radius:18px;
background:orange;
color:white;
font-size:20px;
cursor:pointer;
font-weight:bold;
}

.helper{
text-align:center;
opacity:0.4;
margin-top:10px;
font-size:12px;
}

.verified{
display:inline-flex;
align-items:center;
}

.verified svg{
width:18px;
height:18px;
filter:drop-shadow(0 0 5px orange);
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

#accountBar{
padding:16px;
border-top:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
background:#111;
}

#accountLeft{
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
}

#accountBtns button{
background:#1d1d1d;
border:none;
color:white;
padding:10px;
border-radius:12px;
cursor:pointer;
}

</style>

</head>

<body>

<div class="auth"
id="auth">

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

<button class="authbtn"
onclick="signup()">
Signup
</button>

<button class="authbtn"
onclick="login()">
Login
</button>

</div>

</div>

<div class="container">

<div class="sidebar">

<div class="logo">
Bloxy-bot
</div>

<button class="newchat"
onclick="newChat()">
+ New Chat
</button>

<div class="chatlist"
id="chatlist">
</div>

<div id="accountBar">

<div id="accountLeft">

<span id="accountName">
Guest
</span>

<span id="accountBadge">
</span>

</div>

<div id="accountBtns">

<button onclick="logout()">
Logout
</button>

</div>

</div>

</div>

<div class="main">

<div class="messages"
id="messages">
</div>

<div class="inputarea">

<div class="inputrow">

<input
id="message"
class="inputbox"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}">

<button class="sendbtn"
onclick="send()">
➤
</button>

</div>

<div class="helper">
Bloxy-bot can make mistakes. Verify important information.
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
"Main":{
messages:[],
pinned:false
}
};

function verifiedBadge(){

if(currentUser.verified){

return `
<span class="verified">

<svg viewBox="0 0 24 24">

<path
fill="#ff8800"

d="
M12 1
L15 4
L20 4
L20 9
L23 12
L20 15
L20 20
L15 20
L12 23
L9 20
L4 20
L4 15
L1 12
L4 9
L4 4
L9 4
Z"/>

<path
fill="white"

d="
M10 15
L7 12
L8.5 10.5
L10 12
L15.5 6.5
L17 8
Z"/>

</svg>

</span>
`;

}

return "";

}

function updateAccountBar(){

document.getElementById(
"accountName"
).innerText =
currentUser.username;

document.getElementById(
"accountBadge"
).innerHTML =
verifiedBadge();

}

function newChat(){

let n = prompt("Chat name");

if(!n) return;

chats[n] = {
messages:[],
pinned:false
};

currentChat = n;

renderChats();

render();

}

function pinChat(c){

chats[c].pinned =
!chats[c].pinned;

renderChats();

}

function renameChat(c){

let n = prompt(
"Rename",
c
);

if(!n) return;

chats[n] = chats[c];

delete chats[c];

currentChat = n;

renderChats();

}

function deleteChat(c){

delete chats[c];

if(Object.keys(chats).length===0){

chats["Main"] = {
messages:[],
pinned:false
};

}

currentChat =
Object.keys(chats)[0];

renderChats();

render();

}

function renderChats(){

let box =
document.getElementById(
"chatlist"
);

box.innerHTML = "";

let keys =
Object.keys(chats);

keys.sort((a,b)=>{

return chats[b].pinned -
chats[a].pinned;

});

for(let c of keys){

let d =
document.createElement("div");

d.className = "chatitem";

d.innerHTML = `

<div>

${chats[c].pinned ? "📌 " : ""}

${c}

</div>

<div style="
display:flex;
gap:10px;
">

<span onclick="
event.stopPropagation();
pinChat('${c}')
">
📌
</span>

<span onclick="
event.stopPropagation();
renameChat('${c}')
">
✏️
</span>

<span onclick="
event.stopPropagation();
deleteChat('${c}')
">
🗑️
</span>

</div>
`;

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

for(let m of chats[currentChat].messages){

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

<div style="
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
">

${name}

${badge}

</div>

<div style="margin-top:10px;">
${m.content.replace(/\\n/g,"<br>")}
</div>

`;

box.appendChild(d);

}

box.scrollTop =
box.scrollHeight;

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

alert("Signup failed");

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

alert("Login failed");

return;

}

currentUser = {
email:d.email,
username:d.username,
verified:d.verified
};

localStorage.setItem(
"bloxyUser",
JSON.stringify(currentUser)
);

updateAccountBar();

document.getElementById(
"auth"
).style.display = "none";

});

}

function logout(){

localStorage.removeItem(
"bloxyUser"
);

location.reload();

}

function send(){

let input =
document.getElementById(
"message"
);

let msg =
input.value.trim();

if(!msg) return;

input.value = "";

chats[currentChat].messages.push({
role:"user",
content:msg
});

render();

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

chats[currentChat].messages.push({
role:"assistant",
content:d.reply
});

render();

});

}

let saved =
localStorage.getItem(
"bloxyUser"
);

if(saved){

currentUser =
JSON.parse(saved);

document.getElementById(
"auth"
).style.display = "none";

updateAccountBar();

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

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
