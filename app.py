# =========================================================
# BLOXY-BOT ULTIMATE AI 2026
# COMPLETE APP.PY
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import traceback
import uvicorn
import json
import os
import random
import time

app = FastAPI()

# =========================================================
# ENV VARIABLES
# =========================================================

SECRET_API_KEY = os.getenv("SECRET_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

KIMI_API_KEY = os.getenv("KIMI_API_KEY")

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
# LOAD
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
# AI MODELS
# =========================================================

AI_MODELS = [

    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile"
    },

    {
        "provider": "openrouter",
        "model": "qwen/qwen3-32b"
    },

    {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3-0324:free"
    },

    {
        "provider": "openrouter",
        "model": "mistralai/mistral-large"
    },

    {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet"
    },

    {
        "provider": "openrouter",
        "model": "moonshotai/kimi-k2"
    },

    {
        "provider": "openrouter",
        "model": "openai/gpt-5"
    }

]

# =========================================================
# Pydantic
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
            timeout=20
        )

        return r.text[:2000]

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
                "max": 4
            },
            timeout=20
        )

        return r.text[:2000]

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
                "pageSize": 4
            },
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def wikipedia_search(query):

    try:

        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query,
            timeout=20
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
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def finance_search():

    if not FINNHUB_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://finnhub.io/api/v1/news",
            params={
                "category": "general",
                "token": FINNHUB_API_KEY
            },
            timeout=20
        )

        return r.text[:2000]

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
                "appid": key,
                "i": query
            },
            timeout=20
        )

        return r.text

    except:

        return ""

# =========================================================
# SPORTS
# =========================================================

def sports_context(query):

    context = []

    try:

        if THESPORTSDB_API_KEY:

            r = requests.get(
                f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
                params={
                    "t": query
                },
                timeout=20
            )

            context.append(r.text[:1200])

    except:

        pass

    try:

        if ALLSPORTS_API_KEY:

            r = requests.get(
                "https://apiv2.allsportsapi.com/football/",
                params={
                    "met": "Livescore",
                    "APIkey": ALLSPORTS_API_KEY
                },
                timeout=20
            )

            context.append(r.text[:1200])

    except:

        pass

    try:

        if ODDS_API_KEY:

            r = requests.get(
                "https://api.the-odds-api.com/v4/sports/",
                params={
                    "apiKey": ODDS_API_KEY
                },
                timeout=20
            )

            context.append(r.text[:1200])

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
                    "live": "all"
                },
                timeout=20
            )

            context.append(r.text[:1200])

    except:

        pass

    try:

        if SPORTMONK_API_KEY:

            r = requests.get(
                "https://api.sportmonks.com/v3/football/livescores",
                params={
                    "api_token":
                    SPORTMONK_API_KEY
                },
                timeout=20
            )

            context.append(r.text[:1200])

    except:

        pass

    try:

        if SPORTRADAR_API_KEY:

            r = requests.get(
                f"https://api.sportradar.com/soccer/trial/v4/en/schedules/live/schedule.json?api_key={SPORTRADAR_API_KEY}",
                timeout=20
            )

            context.append(r.text[:1200])

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
            0.7,

            "max_tokens":
            850
        },
        timeout=60
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
            0.7,

            "max_tokens":
            850
        },
        timeout=60
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]


def ask_ai(messages):

    shuffled = AI_MODELS.copy()

    random.shuffle(shuffled)

    for model in shuffled:

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
            "ok": False
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
        "ok": True
    }


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:

            return {
                "ok": False
            }

        return {

            "ok":
            True,

            "username":
            OWNER_USERNAME,

            "verified":
            True,

            "email":
            OWNER_EMAIL

        }

    if data.email not in users:

        return {
            "ok": False
        }

    if users[data.email]["password"] != data.password:

        return {
            "ok": False
        }

    return {

        "ok":
        True,

        "username":
        users[data.email]["username"],

        "verified":
        False,

        "email":
        data.email

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

Use:
- live web info
- live sports
- live finance
- live news
- current events
- current knowledge
- reasoning
- all APIs

Context:

{context}

"""

    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]

    messages += history[-8:]

    messages.append({

        "role":
        "user",

        "content":
        data.message

    })

    reply = ask_ai(messages)

    history.append({

        "role":
        "user",

        "content":
        data.message

    })

    history.append({

        "role":
        "assistant",

        "content":
        reply

    })

    save_json(CHATS_FILE, chat_memory)

    return {

        "reply":
        reply

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
width:280px;
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
width:60px;
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
margin-left:6px;
vertical-align:middle;
}

.verified svg{
width:18px;
height:18px;
filter:drop-shadow(0 0 6px orange);
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
"Main":[]
};

function verifiedBadge(){

if(currentUser.verified){

return `
<span class="verified">

<svg viewBox="0 0 24 24">

<path
fill="#ff9900"

d="
M12 2
L15 5
L19 4
L20 8
L23 12
L20 16
L19 20
L15 19
L12 22
L9 19
L5 20
L4 16
L1 12
L4 8
L5 4
L9 5
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

function newChat(){

let n = prompt("Chat name");

if(!n) return;

chats[n] = [];

currentChat = n;

renderChats();

render();

}

function renderChats(){

let box =
document.getElementById("chatlist");

box.innerHTML = "";

for(let c in chats){

let d =
document.createElement("div");

d.className = "chatitem";

d.innerHTML = `
<div>${c}</div>

<div>

<span onclick="
event.stopPropagation();
renameChat('${c}')
">✏️</span>

<span onclick="
event.stopPropagation();
deleteChat('${c}')
">🗑️</span>

</div>
`;

d.onclick = ()=>{

currentChat = c;

render();

};

box.appendChild(d);

}

}

function renameChat(c){

let n =
prompt("Rename", c);

if(!n) return;

chats[n] = chats[c];

delete chats[c];

currentChat = n;

renderChats();

}

function deleteChat(c){

delete chats[c];

if(Object.keys(chats).length===0){

chats["Main"] = [];

}

currentChat =
Object.keys(chats)[0];

renderChats();

render();

}

function render(){

let box =
document.getElementById("messages");

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
<b>${name}${badge}</b>

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

document.getElementById(
"auth"
).style.display = "none";

});

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

chats[currentChat].push({
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

chats[currentChat].push({
role:"assistant",
content:d.reply
});

render();

});

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
