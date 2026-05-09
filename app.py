# Bloxy-bot Ultimate Single File Platform

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import requests
import json
import os
import time
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
# JSON HELPERS
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
# SPORTS ROUTER
# =========================================================

SPORTS_KEYWORDS = [
    "football","soccer","premier league","laliga",
    "serie a","bundesliga","ligue 1","ucl",
    "champions league","europa league","fifa",
    "world cup","uefa","epl","standings",
    "fixtures","table","goals","transfers",
    "basketball","nba","wnba","euroleague",
    "american football","nfl","super bowl",
    "baseball","mlb","home run",
    "nhl","hockey","stanley cup",
    "tennis","atp","wimbledon",
    "ufc","mma","boxing","wwe",
    "f1","formula 1","motogp",
    "cricket","ipl","t20",
    "golf","pga",
    "esports","valorant","fortnite"
]

# =========================================================
# SEARCH TOOLS
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
                "max_results": 4
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

# =========================================================
# CONTEXT ROUTER
# =========================================================

def build_tool_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in SPORTS_KEYWORDS):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS:\n{sports}")

    if any(x in text for x in [
        "who is","history","country","city"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:
            context.append(f"WIKIPEDIA:\n{wiki}")

    return "\n\n".join(context)

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
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 1,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except Exception as e:

        return str(e)

# =========================================================
# SIGNUP
# =========================================================

@app.post("/signup")
def signup(data: Auth):

    if data.email in users:
        return {"ok": False, "error": "Account already exists"}

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0],
        "created": str(datetime.now())
    }

    save_json(USERS_FILE, users)

    return {"ok": True}

# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: Auth):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:
            return {"ok": False, "error": "Wrong password"}

        return {
            "ok": True,
            "username": "aTg",
            "verified": True,
            "email": OWNER_EMAIL
        }

    if data.email not in users:
        return {"ok": False, "error": "Account not found"}

    if users[data.email]["password"] != data.password:
        return {"ok": False, "error": "Wrong password"}

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

    context = build_tool_context(data.message)

    system_prompt = f"""
You are Bloxy-bot.

Rules:
- Speak naturally like ChatGPT
- Use emojis naturally
- Be intelligent and modern
- Format vertically
- Avoid robotic wording
- Be conversational
- Use clean formatting
- Be helpful and confident

External Context:
{context}
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
margin:0;
padding:0;
font-family:Arial;
}

body{
background:#0f0f0f;
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
padding:20px;
font-size:24px;
font-weight:bold;
}

.chatlist{
flex:1;
overflow:auto;
padding:10px;
}

.chatitem{
padding:14px;
background:#1c1c1c;
border-radius:14px;
margin-bottom:10px;
cursor:pointer;
transition:0.2s;
}

.chatitem:hover{
background:#2a2a2a;
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
scroll-behavior:smooth;
}

.msg{
background:#1a1a1a;
padding:18px;
border-radius:18px;
margin-bottom:16px;
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

.username{
font-weight:bold;
display:flex;
align-items:center;
gap:6px;
margin-bottom:10px;
}

.input-area{
padding:20px;
background:#111;
border-top:1px solid #222;
}

.inputbox{
width:100%;
padding:16px;
border:none;
outline:none;
border-radius:16px;
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

.reactions{
margin-top:12px;
display:flex;
gap:8px;
}

.react{
cursor:pointer;
}

.userbox{
padding:18px;
border-top:1px solid #222;
}

#auth{
position:fixed;
inset:0;
background:#000000dd;
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
border-radius:22px;
}

.authinput{
width:100%;
padding:16px;
margin-top:12px;
background:#222;
border:none;
outline:none;
border-radius:14px;
color:white;
}

.authbtn{
width:100%;
padding:16px;
margin-top:12px;
background:#ff8c00;
border:none;
border-radius:14px;
color:white;
font-weight:bold;
cursor:pointer;
}

@media(max-width:700px){

.sidebar{
position:absolute;
left:-280px;
height:100%;
z-index:50;
}

.sidebar.open{
left:0;
}

}

</style>
</head>

<body>

<div id='auth'>

<div class='authbox'>

<h1>Bloxy-bot</h1>

<input class='authinput' id='email' placeholder='Email'>
<input class='authinput' id='password' type='password' placeholder='Password'>

<button class='authbtn' onclick='signup()'>Signup</button>
<button class='authbtn' onclick='login()'>Login</button>

</div>

</div>

<div class='container'>

<div class='sidebar' id='sidebar'>

<div class='logo'>Bloxy-bot</div>

<div class='chatlist' id='chatlist'></div>

<div class='userbox' id='userbox'></div>

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
Bloxy-bot can make mistakes. Double check important information.
</div>

</div>

</div>

</div>

<script>

let currentUser = {
email:null,
username:'Guest',
verified:false
};

let currentChat = 'main';

let chats = {
main:[]
};

function verifiedBadge(){

return `
<svg width='18' height='18' viewBox='0 0 24 24'>
<path fill='#ff8c00' d='M12 2 L15 4 L19 5 L20 9 L22 12 L20 15 L19 19 L15 20 L12 22 L9 20 L5 19 L4 15 L2 12 L4 9 L5 5 L9 4 Z'></path>
<path d='M8 12 L11 15 L16 9' stroke='white' stroke-width='2' fill='none'></path>
</svg>
`;

}

function updateUserBox(){

userbox.innerHTML = `
<div class='username'>
${currentUser.username}
${currentUser.verified ? verifiedBadge() : ''}
</div>
`;

}

function signup(){

fetch('/signup',{
method:'POST',
headers:{
'Content-Type':'application/json'
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

alert('Signup successful');

});

}

function login(){

fetch('/login',{
method:'POST',
headers:{
'Content-Type':'application/json'
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
'bloxy_user',
JSON.stringify(currentUser)
);

updateUserBox();

auth.style.display='none';

});

}

const saved = localStorage.getItem('bloxy_user');

if(saved){

currentUser = JSON.parse(saved);

updateUserBox();

auth.style.display='none';

}

function typeText(element, text){

let i = 0;

element.innerHTML = '';

let interval = setInterval(()=>{

    element.innerHTML += text.charAt(i);

    i++;

    if(i >= text.length){
        clearInterval(interval);
    }

}, 8);

}

function send(){

let msg = message.value.trim();

if(!msg) return;

message.value='';

chats[currentChat].push({
role:'user',
content:msg
});

render();

fetch('/chat',{
method:'POST',
headers:{
'Content-Type':'application/json'
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
role:'assistant',
content:d.reply
});

render();

});

}

function render(){

messages.innerHTML='';

for(let m of chats[currentChat]){

let div = document.createElement('div');

div.className='msg';

let title = m.role === 'user'
?
`${currentUser.username} ${currentUser.verified ? verifiedBadge() : ''}`
:
'Bloxy-bot';

let body = document.createElement('div');

body.style.marginTop='10px';

body.innerText = m.content;

let react = document.createElement('div');

react.className='reactions';

react.innerHTML=`
<div class='react'>👍</div>
<div class='react'>❤️</div>
<div class='react'>😂</div>
<div class='react'>👎</div>
`;

let edit = document.createElement('button');

edit.innerText='Edit';

edit.onclick=()=>{

let newText = prompt('Edit message', m.content);

if(!newText) return;

m.content = newText;

render();

};

let head = document.createElement('div');

head.className='username';

head.innerHTML=title;

let speak = document.createElement('button');

speak.innerText='🔊';

speak.onclick=()=>{

speechSynthesis.speak(
new SpeechSynthesisUtterance(m.content)
);

};

head.appendChild(speak);

let bubble = document.createElement('div');

bubble.appendChild(head);
bubble.appendChild(body);
bubble.appendChild(react);
bubble.appendChild(edit);

messages.appendChild(bubble);

}

messages.scrollTop = messages.scrollHeight;

}

chats.main=[];

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

```

# requirements.txt

```txt
fastapi
uvicorn
requests
python-dotenv
```

# runtime.txt

```txt
python-3.11.9
```

# users.json

```json
{}
```

# chats.json

```json
{}
```
