# =========================================================
# BLOXY-BOT AI 2026
# FULL COMPLETE ERROR-RECTIFIED SCRIPT
# =========================================================
#
# FIXED:
#
# ✅ GUEST MODE
# ✅ LOGOUT
# ✅ VERIFIED BADGE
# ✅ VERIFIED TOOLTIP
# ✅ LIVE RESPONSES
# ✅ NO TRAINING CUTOFF RESPONSES
# ✅ CLEAN HELPER TEXT
# ✅ SPORTS + NON SPORTS
# ✅ PIN CHATS
# ✅ RENAME CHATS
# ✅ DELETE CHATS
# ✅ SAVE LOGIN
# ✅ SAVE CHATS
# ✅ FAST AI
# ✅ TYPING ANIMATION
# ✅ LIVE SPORTS
# ✅ LIVE NEWS
# ✅ LIVE WEB SEARCH
# ✅ MOBILE UI
# ✅ ORANGE SEND BUTTON
# ✅ ENTER TO SEND
# ✅ ACCOUNT BAR
# ✅ GUEST LOGIN
# ✅ OWNER VERIFIED BADGE
# ✅ MULTI AI MODELS
#
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import uvicorn
import traceback
import json
import os

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
# LOAD / SAVE
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
"model":"llama-3.1-8b-instant"
},

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
},

{
"provider":"openrouter",
"model":"mistralai/mistral-large"
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
# SEARCH
# =========================================================

def tavily_search(query):

    if not TAVILY_API_KEY:

        return ""

    try:

        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key":TAVILY_API_KEY,
                "query":query,
                "max_results":2
            },
            timeout=4
        )

        return r.text[:1000]

    except:

        return ""


def gnews_search(query):

    if not GNEWS_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q":query,
                "token":GNEWS_API_KEY,
                "lang":"en",
                "max":2
            },
            timeout=4
        )

        return r.text[:1000]

    except:

        return ""


def wikipedia_search(query):

    try:

        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query,
            timeout=4
        )

        return r.json().get("extract","")

    except:

        return ""

# =========================================================
# SPORTS
# =========================================================

def sports_context(query):

    try:

        r = requests.get(
            "https://www.thesportsdb.com/api/v1/json/"
            + THESPORTSDB_API_KEY
            + "/searchteams.php",

            params={
                "t":query
            },

            timeout=4
        )

        return r.text[:800]

    except:

        return ""

# =========================================================
# CONTEXT
# =========================================================

def build_context(prompt):

    parts = [

        tavily_search(prompt),

        gnews_search(prompt),

        wikipedia_search(prompt),

        sports_context(prompt)

    ]

    return "\n\n".join(
        [x for x in parts if x]
    )

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

            "model":model,

            "messages":messages,

            "temperature":0.5,

            "max_tokens":140

        },

        timeout=10
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

            "model":model,

            "messages":messages,

            "temperature":0.5,

            "max_tokens":140

        },

        timeout=10
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

    return "Bloxy-bot is overloaded right now."

# =========================================================
# AUTH
# =========================================================

@app.post("/signup")
def signup(data: Signup):

    if data.email in users:

        return {"ok":False}

    users[data.email] = {

        "username":
        data.username,

        "password":
        data.password

    }

    save_json(USERS_FILE, users)

    return {"ok":True}


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:

            return {"ok":False}

        return {

            "ok":True,

            "username":OWNER_USERNAME,

            "verified":True,

            "email":OWNER_EMAIL

        }

    if data.email not in users:

        return {"ok":False}

    if users[data.email]["password"] != data.password:

        return {"ok":False}

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

    if data.email not in chat_memory:

        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:

        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI.

You have access to:
- live web search
- live sports APIs
- live news APIs
- finance APIs
- AI routing systems

NEVER say:
- "My training cutoff was..."
- "My last update was..."
- "I only know up to..."
- "I don't have real-time data"

STRICT RULES:

1. NEVER act like a dictionary
2. NEVER define every word
3. NEVER repeat greetings
4. NEVER overexplain
5. ALWAYS sound natural
6. ALWAYS sound modern
7. ALWAYS answer directly
8. ALWAYS be conversational
9. ALWAYS sound intelligent
10. NEVER sound robotic
11. NEVER mention outdated info
12. NEVER mention limitations
13. ALWAYS feel premium
14. Sports answers should feel live
15. NEVER hallucinate fake scores
16. ALWAYS prioritize usefulness
17. NEVER spam emojis
18. NEVER repeat prompts
19. NEVER sound formal
20. ALWAYS feel smooth
21. ALWAYS keep responses concise
22. NEVER explain obvious things
23. ALWAYS keep sports updated
24. ALWAYS prioritize recent information
25. ALWAYS sound fast
26. NEVER say you are just an AI
27. ALWAYS answer confidently
28. NEVER break character
29. ALWAYS feel modern
30. ALWAYS act like a live AI assistant
31. BE kind, polite,fluent and eloquent
31. USE emojis in every conversation
32. USE your tokens well
33. USE all APIs depending on the request

You can answer:
- sports
- coding
- Roblox scripting
- AI
- politics
- science
- finance
- history
- world news
- gaming
- entertainment
- school questions
- math
- conversations
- general questions
- literature
- movies,series and films
- any game scripting
- any software development making
- economics
- general conversations
- stories and novels
- documentations
- live-web information
- world-wide news,updates and information
- Definitions of words if asked to define

Context:

{context}

"""

    messages = [

        {
            "role":"system",
            "content":system_prompt
        }

    ]

    messages += history[-2:]

    messages.append({

        "role":"user",

        "content":data.message

    })

    reply = ask_ai(messages)

    blocked = [

        "My last update was",

        "My training cutoff",

        "I only know up to",

        "I don't have real-time",

        "I'm an AI language model",

        "As an AI"

    ]

    for b in blocked:

        reply = reply.replace(b,"")

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
}

.logo{
padding:24px;
font-size:28px;
font-weight:bold;
color:#00ff88;
}

.newchat{
margin:14px;
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
padding:15px;
background:#1b1b1b;
border-radius:16px;
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
padding:20px;
}

.msg{
padding:18px;
background:#1b1b1b;
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
background:#111;
border-top:1px solid #222;
}

.row{
display:flex;
gap:10px;
}

.input{
flex:1;
padding:18px;
border:none;
outline:none;
border-radius:18px;
background:#1d1d1d;
color:white;
font-size:15px;
}

.send{
width:65px;
border:none;
border-radius:18px;
background:orange;
color:white;
font-size:20px;
cursor:pointer;
}

.helper{
text-align:center;
opacity:.45;
font-size:12px;
margin-top:10px;
}

.typing{
display:flex;
align-items:center;
gap:6px;
}

.dot{
width:8px;
height:8px;
background:#00ff88;
border-radius:50%;
animation:bounce 1s infinite;
}

.dot:nth-child(2){
animation-delay:.2s;
}

.dot:nth-child(3){
animation-delay:.4s;
}

@keyframes bounce{

0%,80%,100%{
transform:scale(0);
}

40%{
transform:scale(1);
}

}

.badgeWrap{
position:relative;
display:flex;
align-items:center;
}

.badgeWrap svg{
width:18px;
height:18px;
filter:drop-shadow(0 0 6px orange);
}

.badgeTooltip{
position:absolute;
bottom:30px;
left:-40px;
width:250px;
background:#1a1a1a;
padding:12px;
border-radius:12px;
font-size:11px;
opacity:0;
transition:.2s;
border:1px solid #333;
line-height:1.6;
pointer-events:none;
}

.badgeWrap:hover .badgeTooltip{
opacity:1;
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
width:350px;
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

#account{
padding:15px;
border-top:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
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

<button class="authbtn"
onclick="guestMode()">
Continue as Guest
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

<div id="account">

<div style="
display:flex;
align-items:center;
gap:6px;
">

<span id="accountName">
Guest
</span>

<div class="badgeWrap"
id="ownerBadge"
style="display:none;">

<div class="badgeTooltip">

This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform.

</div>

<svg viewBox="0 0 24 24">

<path
fill="#ff8800"

d="
M12 1
L15 4
L19 3
L20 7
L23 12
L20 17
L19 21
L15 20
L12 23
L9 20
L5 21
L4 17
L1 12
L4 7
L5 3
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

</div>

</div>

<button onclick="logout()">
Logout
</button>

</div>

</div>

<div class="main">

<div class="messages"
id="messages">
</div>

<div class="inputarea">

<div class="row">

<input
id="message"
class="input"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}">

<button
class="send"
onclick="send()">
➤
</button>

</div>

<div class="helper">

Bloxy-bot can make mistakes.Verify highly important information

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

let chats = {

"Main":{
messages:[],
pinned:false
}

};

let currentChat = "Main";

function updateAccount(){

document.getElementById(
"accountName"
).innerHTML =
currentUser.username;

document.getElementById(
"ownerBadge"
).style.display =
currentUser.verified
? "flex"
: "none";

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

function pinChat(c){

chats[c].pinned =
!chats[c].pinned;

renderChats();

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

function renameChat(c){

let n =
prompt("Rename",c);

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
messages:[]
};

}

currentChat =
Object.keys(chats)[0];

renderChats();

render();

}

function verifiedBadge(){

return `

<div class="badgeWrap">

<div class="badgeTooltip">

This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform.

</div>

<svg viewBox="0 0 24 24">

<path
fill="#ff8800"

d="
M12 1
L15 4
L19 3
L20 7
L23 12
L20 17
L19 21
L15 20
L12 23
L9 20
L5 21
L4 17
L1 12
L4 7
L5 3
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

</div>

`;

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
"msg " + m.role;

if(m.typing){

d.innerHTML = `

<div style="
font-weight:bold;
margin-bottom:8px;
">

Bloxy-bot

</div>

<div class="typing">

<div class="dot"></div>
<div class="dot"></div>
<div class="dot"></div>

<span style="
margin-left:8px;
opacity:.7;
">
Bloxy-bot is typing...
</span>

</div>

`;

}else{

d.innerHTML = `

<div style="
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
margin-bottom:8px;
">

${m.role==="assistant"

? "Bloxy-bot"

: `

${currentUser.username}

${currentUser.verified
? verifiedBadge()
: ""}

`

}

</div>

<div>
${m.content.replace(/\\n/g,"<br>")}
</div>

`;

}

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

document.getElementById(
"auth"
).style.display = "none";

updateAccount();

render();

});

}

function guestMode(){

localStorage.removeItem(
"bloxyUser"
);

sessionStorage.clear();

currentUser = {

email:"guest",

username:"Guest",

verified:false

};

document.getElementById(
"auth"
).style.display = "none";

updateAccount();

render();

}

function logout(){

localStorage.removeItem(
"bloxyUser"
);

sessionStorage.clear();

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

chats[currentChat].messages.push({

role:"assistant",

typing:true

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

chats[currentChat].messages.pop();

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

}

updateAccount();

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
