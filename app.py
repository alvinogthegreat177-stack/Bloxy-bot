from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import requests
import os
import json
import traceback
import uuid

app = FastAPI()

# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY", "")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "")

# =========================================================
# DATABASE
# =========================================================

USERS_FILE = "users.json"

def load_users():

    try:

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return {}

def save_users(users):

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

USERS = load_users()

# =========================================================
# AI MODELS
# =========================================================

MODELS = [

    {
        "provider": "groq",
        "model": "llama-3.1-8b-instant"
    },

    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile"
    },

    {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3-0324:free"
    },

    {
        "provider": "openrouter",
        "model": "qwen/qwen3-32b"
    },

    {
        "provider": "openrouter",
        "model": "mistralai/mistral-small-3.2-24b-instruct:free"
    }

]

# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    email: str
    chat_id: str
    message: str

class ConversationRequest(BaseModel):
    email: str
    chat_name: str

# =========================================================
# SPORTS TABLE
# =========================================================

def premier_league_table():

    try:

        if APISPORTS_API_KEY:

            r = requests.get(
                "https://v3.football.api-sports.io/standings",
                headers={
                    "x-apisports-key": APISPORTS_API_KEY
                },
                params={
                    "league": 39,
                    "season": 2025
                },
                timeout=6
            )

            data = r.json()

            standings = data["response"][0]["league"]["standings"][0]

            html = """

<table style='width:100%;border-collapse:collapse;margin-top:10px;'>

<tr style='background:#1f1f1f;'>

<th style='padding:10px;'>#</th>
<th style='padding:10px;'>Club</th>
<th style='padding:10px;'>Pts</th>

</tr>

"""

            for team in standings:

                html += f"""

<tr style='border-top:1px solid #333;'>

<td style='padding:10px;'>{team['rank']}</td>
<td style='padding:10px;'>{team['team']['name']}</td>
<td style='padding:10px;'>{team['points']}</td>

</tr>

"""

            html += "</table>"

            return html

    except:
        pass

    return "<div>Could not load Premier League table.</div>"

# =========================================================
# CONTEXT
# =========================================================

def get_context(prompt):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{prompt}",
            timeout=3
        )

        return r.text[:1000]

    except:
        return ""

# =========================================================
# AI
# =========================================================

def groq_chat(model, messages):

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 260
        },
        timeout=15
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]

def openrouter_chat(model, messages):

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 260
        },
        timeout=15
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]

def ask_ai(messages):

    for model in MODELS:

        try:

            if model["provider"] == "groq":
                return groq_chat(model["model"], messages)

            if model["provider"] == "openrouter":
                return openrouter_chat(model["model"], messages)

        except:
            continue

    return "Bloxy-bot is overloaded right now."

# =========================================================
# REGISTER
# =========================================================

@app.post("/register")
def register(data: RegisterRequest):

    email = data.email.strip().lower()
    username = data.username.strip()
    password = data.password.strip()

    if "@" not in email:
        return {
            "success": False,
            "message": "Email must contain @"
        }

    if "." not in email:
        return {
            "success": False,
            "message": "Invalid email"
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": "Password must be 6+ characters"
        }

    if email in USERS:
        return {
            "success": False,
            "message": "Account already exists"
        }

    USERS[email] = {

        "username": username,
        "password": password,
        "verified": username.lower() == "atg",
        "conversations": {}

    }

    save_users(USERS)

    return {
        "success": True
    }

# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login(data: LoginRequest):

    email = data.email.strip().lower()

    if email not in USERS:
        return {
            "success": False,
            "message": "Account not found"
        }

    if USERS[email]["password"] != data.password:
        return {
            "success": False,
            "message": "Wrong password"
        }

    return {

        "success": True,
        "username": USERS[email]["username"],
        "verified": USERS[email]["verified"],
        "conversations": USERS[email]["conversations"]

    }

# =========================================================
# NEW CONVERSATION
# =========================================================

@app.post("/newchat")
def newchat(data: ConversationRequest):

    if data.email not in USERS:
        return {
            "success": False
        }

    USERS[data.email]["conversations"][data.chat_name] = []

    save_users(USERS)

    return {
        "success": True
    }

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    if data.message.lower() in [
        "pl table",
        "premier league table",
        "epl table"
    ]:

        return {
            "reply": premier_league_table()
        }

    if data.email == "guest":

        history = []

    else:

        if data.chat_id not in USERS[data.email]["conversations"]:
            USERS[data.email]["conversations"][data.chat_id] = []

        history = USERS[data.email]["conversations"][data.chat_id]

    context = get_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI Ultimate.

RULES:

1. Never say knowledge cutoff
2. Never say outdated
3. Never say As an AI
4. Never define like a dictionary
5. Always sound modern
6. Always sound premium
7. Always sound conversational
8. Always answer naturally
9. Always support sports
10. Always support football
11. Always support NBA
12. Always support UFC
13. Always support F1
14. Always support horse racing
15. Always support live info
16. Always support current events
17. Always support coding
18. Always support science
19. Always support gaming
20. Always support finance
21. Always support transfer news
22. Always support standings
23. Always avoid fake stats
24. Always avoid ugly formatting
25. Always stay clean
26. Always stay intelligent
27. Always stay smooth
28. Always stay useful
29. Always remain Bloxy-bot
30. Always feel like a premium AI

LIVE CONTEXT:

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

    blocked = [

        "As an AI",
        "knowledge cutoff",
        "training cutoff"

    ]

    for b in blocked:
        reply = reply.replace(b, "")

    if data.email != "guest":

        history.append({

            "role": "user",
            "content": data.message

        })

        history.append({

            "role": "assistant",
            "content": reply

        })

        USERS[data.email]["conversations"][data.chat_id] = history

        save_users(USERS)

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

<meta name='viewport' content='width=device-width, initial-scale=1.0'>

<title>Bloxy-bot</title>

<style>

*{
box-sizing:border-box;
}

body{
margin:0;
background:#0d0d0d;
font-family:Arial;
color:white;
overflow:hidden;
}

.auth{
position:fixed;
inset:0;
background:#0d0d0d;
display:flex;
justify-content:center;
align-items:center;
z-index:999;
}

.authBox{
width:420px;
background:#151515;
padding:30px;
border-radius:24px;
border:1px solid #222;
}

.authTitle{
font-size:34px;
font-weight:bold;
margin-bottom:25px;
color:#00ff88;
}

.authInput{
width:100%;
padding:16px;
margin-bottom:14px;
background:#1d1d1d;
border:none;
border-radius:14px;
color:white;
outline:none;
}

.authBtn{
width:100%;
padding:16px;
border:none;
border-radius:14px;
background:orange;
color:white;
font-size:15px;
cursor:pointer;
margin-bottom:10px;
}

.guestBtn{
background:#222;
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
font-size:32px;
font-weight:bold;
padding:20px;
color:#00ff88;
}

.newchat{
margin:0 20px 20px 20px;
padding:14px;
border:none;
border-radius:14px;
background:#1d1d1d;
color:white;
cursor:pointer;
}

.chatlist{
flex:1;
overflow:auto;
padding:20px;
}

.chatitem{
padding:14px;
background:#181818;
border-radius:14px;
margin-bottom:10px;
display:flex;
justify-content:space-between;
align-items:center;
}

.accountBar{
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

.topbar{
padding:18px;
background:#111;
border-bottom:1px solid #222;
font-weight:bold;
}

.messages{
flex:1;
overflow:auto;
padding:20px;
}

.msg{
padding:18px;
border-radius:18px;
margin-bottom:18px;
background:#181818;
line-height:1.7;
max-width:900px;
}

.user{
margin-left:auto;
border-left:4px solid orange;
}

.assistant{
border-left:4px solid #00ff88;
}

.topName{
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
margin-bottom:8px;
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
background:#1d1d1d;
border:none;
outline:none;
border-radius:18px;
color:white;
}

.send{
width:70px;
border:none;
background:orange;
color:white;
font-size:22px;
border-radius:18px;
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
gap:5px;
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
display:flex;
align-items:center;
position:relative;
}

.badgeTooltip{
position:absolute;
bottom:35px;
left:-50px;
width:260px;
background:#1b1b1b;
padding:12px;
border-radius:14px;
font-size:11px;
opacity:0;
pointer-events:none;
transition:.2s;
border:1px solid #333;
}

.badgeWrap:hover .badgeTooltip{
opacity:1;
}

table{
background:#111;
border-radius:14px;
overflow:hidden;
}

</style>

</head>

<body>

<div class='auth' id='auth'>

<div class='authBox'>

<div class='authTitle'>
Bloxy-bot
</div>

<input
id='registerEmail'
class='authInput'
placeholder='example@gmail.com'
>

<input
id='registerUser'
class='authInput'
placeholder='Username'
>

<input
id='registerPass'
class='authInput'
type='password'
placeholder='Password (6+ chars)'
>

<button class='authBtn' onclick='register()'>
Create Account
</button>

<hr style='border:1px solid #222;margin:20px 0;'>

<input
id='loginEmail'
class='authInput'
placeholder='example@gmail.com'
>

<input
id='loginPass'
class='authInput'
type='password'
placeholder='Password'
>

<button class='authBtn' onclick='login()'>
Login
</button>

<button class='authBtn guestBtn' onclick='guestMode()'>
Continue As Guest
</button>

</div>

</div>

<div class='container'>

<div class='sidebar'>

<div class='logo'>
Bloxy-bot
</div>

<button class='newchat' onclick='newChat()'>
+ New Chat
</button>

<div class='chatlist' id='chatlist'></div>

<div class='accountBar'>

<div id='account'></div>

<div id='logoutArea'></div>

</div>

</div>

<div class='main'>

<div class='topbar'>
Bloxy-bot AI Ultimate
</div>

<div class='messages' id='messages'></div>

<div class='inputarea'>

<div class='row'>

<input
id='message'
class='input'
placeholder='Message Bloxy-bot...'
onkeydown="if(event.key==='Enter'){send()}"
>

<button class='send' onclick='send()'>
➤
</button>

</div>

<div class='helper'>
Bloxy-bot can make mistakes.Verify highly important information
</div>

</div>

</div>

</div>

<script>

let currentUser={
email:'guest',
username:'Guest',
verified:false,
guest:true
};

let chats={
'Main':[]
};

let currentChat='Main';

function badge(){

return `

<div class='badgeWrap'>

<div class='badgeTooltip'>
This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform.
</div>

<svg viewBox='0 0 24 24' width='18' height='18'>

<path
fill='#ff8800'
d='M12 1 L15 4 L19 3 L20 7 L23 12 L20 17 L19 21 L15 20 L12 23 L9 20 L5 21 L4 17 L1 12 L4 7 L5 3 L9 4 Z'
/>

<path
fill='white'
d='M10 15 L7 12 L8.5 10.5 L10 12 L15.5 6.5 L17 8 Z'
/>

</svg>

</div>

`;

}

function hideAuth(){

document.getElementById('auth').style.display='none';

}

function updateAccount(){

document.getElementById('account').innerHTML=

currentUser.username +

(currentUser.verified ? badge() : '');

if(currentUser.guest){

document.getElementById('logoutArea').innerHTML='';

}else{

document.getElementById('logoutArea').innerHTML=`

<button onclick='logout()'>
Logout
</button>

`;

}

}

async function register(){

let email=document.getElementById('registerEmail').value.trim();
let username=document.getElementById('registerUser').value.trim();
let password=document.getElementById('registerPass').value.trim();

let r=await fetch('/register',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email,
username,
password

})

});

let d=await r.json();

if(!d.success){

alert(d.message);
return;

}

alert("Account created successfully");

}

async function login(){

let email=document.getElementById('loginEmail').value.trim();
let password=document.getElementById('loginPass').value.trim();

let r=await fetch('/login',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email,
password

})

});

let d=await r.json();

if(!d.success){

alert(d.message);
return;

}

currentUser={

email:email,
username:d.username,
verified:d.verified,
guest:false

};

chats=d.conversations;

if(Object.keys(chats).length===0){

chats={
'Main':[]
};

}

currentChat=Object.keys(chats)[0];

hideAuth();

updateAccount();

renderChats();

render();

}

function guestMode(){

currentUser={

email:'guest',
username:'Guest',
verified:false,
guest:true

};

hideAuth();

updateAccount();

renderChats();

render();

}

function logout(){

location.reload();

}

async function newChat(){

let name='Chat '+(Object.keys(chats).length+1);

chats[name]=[];

currentChat=name;

if(!currentUser.guest){

await fetch('/newchat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
chat_name:name

})

});

}

renderChats();

render();

}

function renderChats(){

let box=document.getElementById('chatlist');

box.innerHTML='';

Object.keys(chats).forEach(name=>{

let d=document.createElement('div');

d.className='chatitem';

d.innerHTML=`

<span onclick="switchChat('${name}')">
${name}
</span>

`;

box.appendChild(d);

});

}

function switchChat(name){

currentChat=name;

render();

}

function render(){

let box=document.getElementById('messages');

box.innerHTML='';

for(let m of chats[currentChat]){

let d=document.createElement('div');

d.className='msg '+m.role;

d.innerHTML=`

<div class='topName'>

${m.role==='assistant'
?'Bloxy-bot'
:currentUser.username}

${m.role==='user' && currentUser.verified ? badge() : ''}

</div>

<div>${m.content}</div>

`;

box.appendChild(d);

}

box.scrollTop=box.scrollHeight;

}

async function send(){

let input=document.getElementById('message');

let msg=input.value.trim();

if(!msg)return;

input.value='';

chats[currentChat].push({

role:'user',
content:msg

});

chats[currentChat].push({

role:'assistant',
content:`

<div class='typing'>

<div class='dot'></div>
<div class='dot'></div>
<div class='dot'></div>

<span>
Bloxy-bot is typing...
</span>

</div>

`

});

render();

let r=await fetch('/chat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
chat_id:currentChat,
message:msg

})

});

let d=await r.json();

chats[currentChat].pop();

chats[currentChat].push({

role:'assistant',
content:d.reply

});

render();

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
