from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import requests
import os
import json

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

def save_users(data):

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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
    old_name: str = ""
    new_name: str = ""

# =========================================================
# SPORTS TABLE
# =========================================================

def get_prem_table():

    try:

        r = requests.get(
            "https://v3.football.api-sports.io/standings",
            headers={
                "x-apisports-key": APISPORTS_API_KEY
            },
            params={
                "league": 39,
                "season": 2025
            },
            timeout=5
        )

        data = r.json()

        standings = data["response"][0]["league"]["standings"][0]

        html = """

<table style='width:100%;border-collapse:collapse;background:#111;border-radius:14px;overflow:hidden;'>

<tr style='background:#1f1f1f;'>

<th style='padding:12px;'>#</th>
<th style='padding:12px;'>Club</th>
<th style='padding:12px;'>Pts</th>

</tr>

"""

        for t in standings:

            html += f"""

<tr style='border-top:1px solid #333;'>

<td style='padding:12px;'>{t['rank']}</td>
<td style='padding:12px;'>{t['team']['name']}</td>
<td style='padding:12px;'>{t['points']}</td>

</tr>

"""

        html += "</table>"

        return html

    except:
        return "Could not load Premier League table."

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
            "max_tokens": 400
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
            "max_tokens": 400
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

            else:
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

    if "@" not in email or "." not in email:
        return {
            "success": False,
            "message": "Invalid email"
        }

    if len(password) < 6:
        return {
            "success": False,
            "message": "Password must contain 6+ characters"
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

        "memory": [],

        "conversations": {

            "Main": {

                "messages": [],
                "pinned": False

            }

        }

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
# NEW CHAT
# =========================================================

@app.post("/newchat")
def newchat(data: ConversationRequest):

    if data.email not in USERS:
        return {
            "success": False
        }

    name = "Chat " + str(len(USERS[data.email]["conversations"]) + 1)

    USERS[data.email]["conversations"][name] = {

        "messages": [],
        "pinned": False

    }

    save_users(USERS)

    return {

        "success": True,
        "chat_name": name

    }

# =========================================================
# RENAME CHAT
# =========================================================

@app.post("/renamechat")
def renamechat(data: ConversationRequest):

    convos = USERS[data.email]["conversations"]

    convos[data.new_name] = convos.pop(data.old_name)

    save_users(USERS)

    return {
        "success": True
    }

# =========================================================
# PIN CHAT
# =========================================================

@app.post("/pinchat")
def pinchat(data: ConversationRequest):

    convos = USERS[data.email]["conversations"]

    convos[data.old_name]["pinned"] = not convos[data.old_name]["pinned"]

    save_users(USERS)

    return {
        "success": True
    }

# =========================================================
# DELETE CHAT
# =========================================================

@app.post("/deletechat")
def deletechat(data: ConversationRequest):

    convos = USERS[data.email]["conversations"]

    if len(convos) == 1:
        return {
            "success": False
        }

    del convos[data.old_name]

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
            "reply": get_prem_table()
        }

    history = []
    memory = []

    if data.email != "guest":

        user = USERS[data.email]

        history = user["conversations"][data.chat_id]["messages"]

        memory = user["memory"][-40:]

    rules = ""

    for i in range(1, 151):

        rules += f"{i}. Always remain modern intelligent accurate natural and useful.\\n"

    system_prompt = f"""

You are Bloxy-bot AI Ultimate.

{rules}

Long term memory:

{memory}

Never say:
- As an AI
- knowledge cutoff
- training cutoff

Always:
- answer naturally
- answer fast
- support all sports
- support live info
- support coding
- support gaming
- support science
- support finance
- support current events
- support all conversations
- avoid dictionary style answers

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

    blocked = [

        "As an AI",
        "knowledge cutoff",
        "training cutoff"

    ]

    for b in blocked:
        reply = reply.replace(b, "")

    if data.email != "guest":

        USERS[data.email]["memory"].append({

            "user": data.message,
            "assistant": reply

        })

        USERS[data.email]["conversations"][data.chat_id]["messages"].append({

            "role": "user",
            "content": data.message

        })

        USERS[data.email]["conversations"][data.chat_id]["messages"].append({

            "role": "assistant",
            "content": reply

        })

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

<meta charset='UTF-8'>

<meta name='viewport' content='width=device-width, initial-scale=1.0'>

<title>Bloxy-bot</title>

<style>

*{
box-sizing:border-box;
}

html{
scroll-behavior:smooth;
overflow:hidden;
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
width:300px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.logo{
font-size:34px;
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
overflow-y:auto;
overflow-x:hidden;
scrollbar-width:thin;
scrollbar-color:#ff8800 #111;
padding:20px;
}

.messages{
flex:1;
overflow-y:auto;
overflow-x:hidden;
scrollbar-width:thin;
scrollbar-color:#00ff88 #111;
scroll-behavior:smooth;
padding:20px;
padding-bottom:40px;
}

.chatlist::-webkit-scrollbar,
.messages::-webkit-scrollbar{
width:10px;
}

.chatlist::-webkit-scrollbar-track,
.messages::-webkit-scrollbar-track{
background:#111;
border-radius:10px;
}

.chatlist::-webkit-scrollbar-thumb{
background:#ff8800;
border-radius:10px;
}

.messages::-webkit-scrollbar-thumb{
background:#00ff88;
border-radius:10px;
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

.chatbuttons{
display:flex;
gap:6px;
}

.chatbuttons button{
background:#222;
border:none;
color:white;
padding:6px 8px;
border-radius:8px;
cursor:pointer;
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

.msg{
padding:18px;
border-radius:18px;
margin-bottom:18px;
background:#181818;
line-height:1.7;
max-width:900px;
word-wrap:break-word;
overflow-wrap:break-word;
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
caret-color:#00ff88;
}

.input:focus{
box-shadow:0 0 10px rgba(0,255,136,.25);
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

</style>

</head>

<body>

<div class='auth' id='auth'>

<div class='authBox'>

<div class='authTitle'>
Bloxy-bot
</div>

<input id='registerEmail' class='authInput' placeholder='example@gmail.com'>

<input id='registerUser' class='authInput' placeholder='Username'>

<input id='registerPass' class='authInput' type='password' placeholder='Password'>

<button class='authBtn' onclick='register()'>
Create Account
</button>

<hr style='border:1px solid #222;margin:20px 0;'>

<input id='loginEmail' class='authInput' placeholder='example@gmail.com'>

<input id='loginPass' class='authInput' type='password' placeholder='Password'>

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

"Main":{
messages:[],
pinned:false
}

};

let currentChat="Main";

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

if(currentUser.guest){

let name="Guest Chat "+(Object.keys(chats).length+1);

chats[name]={
messages:[],
pinned:false
};

currentChat=name;

renderChats();

render();

return;

}

let r=await fetch('/newchat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email

})

});

let d=await r.json();

chats[d.chat_name]={

messages:[],
pinned:false

};

currentChat=d.chat_name;

renderChats();

render();

}

function switchChat(name){

currentChat=name;

render();

}

async function renameChat(name){

let newName=prompt("Rename chat",name);

if(!newName)return;

if(currentUser.guest){

chats[newName]=chats[name];

delete chats[name];

currentChat=newName;

renderChats();

return;

}

await fetch('/renamechat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
old_name:name,
new_name:newName

})

});

chats[newName]=chats[name];

delete chats[name];

currentChat=newName;

renderChats();

}

async function pinChat(name){

chats[name].pinned=!chats[name].pinned;

renderChats();

if(currentUser.guest)return;

await fetch('/pinchat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
old_name:name

})

});

}

async function deleteChat(name){

if(Object.keys(chats).length===1)return;

delete chats[name];

currentChat=Object.keys(chats)[0];

renderChats();

render();

if(currentUser.guest)return;

await fetch('/deletechat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
old_name:name

})

});

}

function renderChats(){

let box=document.getElementById('chatlist');

box.innerHTML='';

Object.keys(chats).forEach(name=>{

let d=document.createElement('div');

d.className='chatitem';

d.innerHTML=`

<span onclick="switchChat('${name}')">

${chats[name].pinned ? '📌 ' : ''}${name}

</span>

<div class='chatbuttons'>

<button onclick="renameChat('${name}')">
✏️
</button>

<button onclick="pinChat('${name}')">
📌
</button>

<button onclick="deleteChat('${name}')">
🗑️
</button>

</div>

`;

box.appendChild(d);

});

}

function render(){

let box=document.getElementById('messages');

box.innerHTML='';

for(let m of chats[currentChat].messages){

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

chats[currentChat].messages.push({

role:'user',
content:msg

});

chats[currentChat].messages.push({

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

chats[currentChat].messages.pop();

chats[currentChat].messages.push({

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
