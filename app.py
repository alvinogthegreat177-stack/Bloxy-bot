# =========================================================
# BLOXY-BOT ULTIMATE AI 2026
# COMPLETE SINGLE FILE APP.PY
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import traceback
import uvicorn
import json
import os
import secrets

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

WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

EXA_API_KEY = os.getenv("EXA_API_KEY")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

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
# LOAD/SAVE
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
                "max_results": 2
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
                "max": 3
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
                "pageSize": 3
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
            timeout=15
        )

        data = r.json()

        return data.get("extract", "")

    except:

        return ""


def exa_search(query):

    if not EXA_API_KEY:

        return ""

    try:

        r = requests.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": EXA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "numResults": 2
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

    if not WOLFRAM_API_KEY and not WOLFRAM_APP_ID:

        return ""

    try:

        key = WOLFRAM_API_KEY or WOLFRAM_APP_ID

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

def thesportsdb_search(team):

    if not THESPORTSDB_API_KEY:

        return ""

    try:

        r = requests.get(
            f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
            params={
                "t": team
            },
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def allsports_search():

    if not ALLSPORTS_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://apiv2.allsportsapi.com/football/",
            params={
                "met": "Livescore",
                "APIkey": ALLSPORTS_API_KEY
            },
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def odds_search():

    if not ODDS_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://api.the-odds-api.com/v4/sports/",
            params={
                "apiKey": ODDS_API_KEY
            },
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def apisports_search():

    if not APISPORTS_API_KEY:

        return ""

    try:

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

        return r.text[:2000]

    except:

        return ""


def sportmonk_search():

    if not SPORTMONK_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://api.sportmonks.com/v3/football/livescores",
            params={
                "api_token":
                SPORTMONK_API_KEY
            },
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""


def sportradar_search():

    if not SPORTRADAR_API_KEY:

        return ""

    try:

        r = requests.get(
            f"https://api.sportradar.com/soccer/trial/v4/en/schedules/live/schedule.json?api_key={SPORTRADAR_API_KEY}",
            timeout=20
        )

        return r.text[:2000]

    except:

        return ""

# =========================================================
# CONTEXT
# =========================================================

def build_context(prompt):

    context = []

    t = tavily_search(prompt)

    if t:

        context.append("TAVILY:\\n" + t)

    g = gnews_search(prompt)

    if g:

        context.append("GNEWS:\\n" + g)

    n = newsapi_search(prompt)

    if n:

        context.append("NEWSAPI:\\n" + n)

    w = wikipedia_search(prompt)

    if w:

        context.append("WIKIPEDIA:\\n" + w)

    e = exa_search(prompt)

    if e:

        context.append("EXA:\\n" + e)

    f = finance_search()

    if f:

        context.append("FINANCE:\\n" + f)

    wa = wolfram_search(prompt)

    if wa:

        context.append("WOLFRAM:\\n" + wa)

    s1 = thesportsdb_search(prompt)

    if s1:

        context.append("SPORTSDB:\\n" + s1)

    s2 = allsports_search()

    if s2:

        context.append("ALLSPORTS:\\n" + s2)

    s3 = odds_search()

    if s3:

        context.append("ODDS:\\n" + s3)

    s4 = apisports_search()

    if s4:

        context.append("APISPORTS:\\n" + s4)

    s5 = sportmonk_search()

    if s5:

        context.append("SPORTMONKS:\\n" + s5)

    s6 = sportradar_search()

    if s6:

        context.append("SPORTRADAR:\\n" + s6)

    return "\\n\\n".join(context)

# =========================================================
# AI
# =========================================================

def ask_ai(messages):

    try:

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
                "llama-3.3-70b-versatile",

                "messages":
                messages,

                "temperature":
                0.8,

                "max_tokens":
                1500
            },
            timeout=60
        )

        data = r.json()

        if "choices" in data:

            return data["choices"][0]["message"]["content"]

        return str(data)

    except Exception:

        print(traceback.format_exc())

        return "Bloxy-bot AI error."

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
        "username": data.username,
        "password": data.password
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
            "ok": True,
            "username": OWNER_USERNAME,
            "verified": True,
            "email": OWNER_EMAIL
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

Use live information.
Use sports APIs.
Use web search.
Use current knowledge.
Avoid hallucinations.
Know everything in the world.
Say factual things.
Be punctual and have correct spelling of words.
Be polite.
Use emojis in every conversation.
Give correct information.
Know everything on every topic.


Context:

{context}

"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history[-6:]

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
# UI
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
background:#101010;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.logo{
padding:24px;
font-size:30px;
font-weight:bold;
color:#00ff88;
text-shadow:0 0 18px #00ff88;
}

.newchat{
margin:15px;
padding:16px;
border:none;
border-radius:18px;
background:#1d1d1d;
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
}

.chatbuttons{
display:flex;
gap:8px;
}

.chatoption{
cursor:pointer;
opacity:0.7;
}

.userbox{
padding:16px;
border-top:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
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
line-height:1.7;
white-space:pre-wrap;
}

.user{
border-left:4px solid orange;
}

.assistant{
border-left:4px solid #00ff88;
}

.inputarea{
padding:18px;
background:#111;
border-top:1px solid #222;
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
font-size:18px;
cursor:pointer;
font-weight:bold;
}

.helper{
margin-top:10px;
text-align:center;
opacity:0.4;
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

@media(max-width:700px){

.sidebar{
width:90px;
}

.logo{
font-size:18px;
}

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

<button class="guestbtn"
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

<button class="newchat"
onclick="newChat()">
+ New Chat
</button>

<div class="chatlist"
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
L14.7 5.1
L18.8 4.4
L19.6 8.4
L23 10.9
L20.9 14.4
L22 18.5
L17.9 19.6
L15.4 23
L11.9 20.9
L7.8 22
L6.7 17.9
L3.3 15.4
L5.4 11.9
L4.3 7.8
L8.4 6.7
Z"/>

<path
fill="white"

d="
M10.2 15.8
L6.9 12.5
L8.3 11.1
L10.2 13
L15.9 7.3
L17.3 8.7
Z"/>

</svg>

</span>
`;

}

return "";

}

function newChat(){

let name =
prompt(
"Conversation name"
);

if(!name) return;

chats[name] = [];

currentChat = name;

renderChats();

render();

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

d.className =
"chatitem";

d.innerHTML = `
<div>${c}</div>

<div class="chatbuttons">

<div class="chatoption"
onclick="
event.stopPropagation();
renameChat('${c}')
">
✏️
</div>

<div class="chatoption"
onclick="
event.stopPropagation();
pinChat('${c}')
">
📌
</div>

<div class="chatoption"
onclick="
event.stopPropagation();
deleteChat('${c}')
">
🗑️
</div>

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
prompt(
"Rename chat",
c
);

if(!n) return;

chats[n] = chats[c];

delete chats[c];

currentChat = n;

renderChats();

}

function pinChat(c){

if(c.startsWith("📌 ")) return;

chats["📌 " + c] = chats[c];

delete chats[c];

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

document.getElementById(
"userbox"
).innerHTML =
d.username + verifiedBadge();

});

}

function guestMode(){

document.getElementById(
"auth"
).style.display = "none";

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
