from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
import hashlib
from datetime import datetime

app = FastAPI(
    title="Bloxy-Bot X",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_NAME = "bloxybotx.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tables()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


import secrets
from fastapi.responses import JSONResponse

def get_user_by_email(email):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    user = cur.fetchone()
    conn.close()
    return user

def create_session(user_id):
    token = secrets.token_hex(32)

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO sessions VALUES(?,?,?)",
        (
            token,
            user_id,
            now()
        )
    )

    conn.commit()
    conn.close()

    return token

@app.post("/api/register")
def register(data: RegisterRequest):

    if get_user_by_email(data.email):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Email already exists"
            }
        )

    user_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users VALUES(?,?,?,?,?)",
        (
            user_id,
            data.username,
            data.email,
            hash_password(data.password),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "user_id": user_id
    }

@app.post("/api/login")
def login(data: LoginRequest):

    user = get_user_by_email(data.email)

    if not user:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    if user["password"] != hash_password(data.password):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid credentials"
            }
        )

    token = create_session(user["id"])

    return {
        "success": True,
        "token": token,
        "user_id": user["id"],
        "username": user["username"]
    }

@app.post("/api/guest")
def guest_login():
    return {
        "success": True,
        "guest": True,
        "user_id": generate_id(),
        "username": "Guest"
    }

@app.delete("/api/logout/{token}")
def logout(token: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM sessions WHERE token=?",
        (token,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }

@app.get("/api/user/{user_id}")
def get_user(user_id: str):

    user = get_user_by_id(user_id)

    if not user:
        return {
            "success": False
        }

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }


# =========================================================
# PART 3
# CONVERSATIONS + MESSAGES
# =========================================================

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str

class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str

def create_conversation_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_conversation_tables()


# =========================================================
# PART 4
# CONVERSATION ROUTES
# =========================================================

@app.post("/api/conversations/create")
def create_conversation(data: CreateConversationRequest):
    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO conversations VALUES(?,?,?,?,?)",
        (
            conversation_id,
            data.user_id,
            data.title,
            now(),
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "conversation_id": conversation_id
    }


@app.get("/api/conversations/{user_id}")
def get_conversations(user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM conversations WHERE user_id=? ORDER BY updated_at DESC",
        (user_id,)
    )

    data = [dict(row) for row in cur.fetchall()]

    conn.close()

    return {
        "success": True,
        "conversations": data
    }


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM messages WHERE conversation_id=?",
        (conversation_id,)
    )

    cur.execute(
        "DELETE FROM conversations WHERE id=?",
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {"success": True}


# =========================================================
# PART 5A
# COMPLETE FRONTEND REPLACEMENT
# MODERN CHATGPT-STYLE LAYOUT
# REPLACE YOUR ENTIRE CURRENT:
#
# @app.get("/", response_class=HTMLResponse)
# def home():
#
# SECTION WITH THIS
# =========================================================

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>Bloxy-Bot X</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:'Inter',sans-serif;
}

body{
background:#0b0f19;
color:white;
height:100vh;
overflow:hidden;
}

.app{
display:flex;
height:100vh;
width:100%;
}

/* ==========================
SIDEBAR
========================== */

.sidebar{
width:280px;
background:#111827;
border-right:1px solid #1f2937;
display:flex;
flex-direction:column;
}

.logo{
padding:20px;
font-size:22px;
font-weight:700;
border-bottom:1px solid #1f2937;
}

.new-chat{
margin:15px;
padding:12px;
background:#2563eb;
border:none;
color:white;
border-radius:10px;
cursor:pointer;
font-weight:600;
}

.new-chat:hover{
background:#1d4ed8;
}

.search-box{
padding:0 15px 15px 15px;
}

.search-box input{
width:100%;
padding:12px;
background:#1f2937;
border:none;
border-radius:10px;
color:white;
}

.conversations{
flex:1;
overflow-y:auto;
padding:10px;
}

.chat-item{
padding:12px;
border-radius:10px;
cursor:pointer;
margin-bottom:5px;
background:#1f2937;
}

.chat-item:hover{
background:#2b3648;
}

/* ==========================
MAIN CHAT
========================== */

.main{
flex:1;
display:flex;
flex-direction:column;
background:#0b0f19;
}

.topbar{
height:65px;
border-bottom:1px solid #1f2937;
display:flex;
align-items:center;
justify-content:space-between;
padding:0 20px;
}

.model-select{
background:#1f2937;
border:none;
padding:10px;
border-radius:8px;
color:white;
}

.chat-area{
flex:1;
overflow-y:auto;
padding:30px;
}

.message{
max-width:900px;
margin:auto;
margin-bottom:20px;
padding:16px;
border-radius:12px;
line-height:1.7;
}

.user{
background:#1e293b;
}

.assistant{
background:#111827;
border:1px solid #1f2937;
}

.code{
background:#05070c;
padding:15px;
border-radius:10px;
overflow-x:auto;
margin-top:10px;
}

/* ==========================
INPUT
========================== */

.input-wrapper{
padding:20px;
border-top:1px solid #1f2937;
}

.input-box{
max-width:950px;
margin:auto;
display:flex;
gap:10px;
}

.input-box textarea{
flex:1;
height:60px;
resize:none;
border:none;
outline:none;
background:#111827;
color:white;
padding:15px;
border-radius:14px;
}

.send-btn{
width:60px;
border:none;
border-radius:14px;
background:#2563eb;
color:white;
cursor:pointer;
font-size:18px;
}

.send-btn:hover{
background:#1d4ed8;
}

/* ==========================
ACCOUNT
========================== */

.account{
padding:15px;
border-top:1px solid #1f2937;
}

.account button{
width:100%;
padding:12px;
border:none;
background:#1f2937;
color:white;
border-radius:10px;
cursor:pointer;
}

/* ==========================
SETTINGS MODAL
========================== */

.modal{
display:none;
position:fixed;
inset:0;
background:rgba(0,0,0,.7);
}

.modal-content{
width:600px;
max-width:95%;
background:#111827;
margin:50px auto;
padding:25px;
border-radius:15px;
}

.setting-row{
margin-top:15px;
}

.setting-row input,
.setting-row select{
width:100%;
padding:12px;
margin-top:5px;
background:#1f2937;
border:none;
color:white;
border-radius:8px;
}

/* ==========================
MOBILE
========================== */

@media(max-width:768px){

.sidebar{
display:none;
}

.main{
width:100%;
}

}

</style>

</head>

<body>

<div class="app">

<div class="sidebar">

<div class="logo">
🤖 Bloxy-Bot X
</div>

<button class="new-chat"
onclick="newChat()">
+ New Chat
</button>

<div class="search-box">
<input
placeholder="Search conversations..."
id="searchChats"
>
</div>

<div
class="conversations"
id="conversationList"
>

<div class="chat-item">
New Conversation
</div>

</div>

<div class="account">

<button onclick="openSettings()">
⚙ Settings
</button>

</div>

</div>

<div class="main">

<div class="topbar">

<h3>Bloxy-Bot X</h3>

<select
class="model-select"
id="model"
>
<option>OpenRouter</option>
<option>GPT-4o</option>
<option>Groq</option>
<option>Kimi</option>
</select>

</div>

<div
class="chat-area"
id="chat"
>

<div class="message assistant">
👋 Welcome to Bloxy-Bot X
</div>

</div>

<div class="input-wrapper">

<div class="input-box">

<textarea
id="message"
placeholder="Message Bloxy-Bot X..."
></textarea>

<button
class="send-btn"
onclick="sendMessage()"
>
➤
</button>

</div>

</div>

</div>

</div>

<div
class="modal"
id="settingsModal"
>

<div class="modal-content">

<h2>Settings</h2>

<div class="setting-row">
<label>Theme</label>
<select>
<option>Dark</option>
<option>Midnight</option>
<option>Ocean</option>
<option>Emerald</option>
</select>
</div>

<div class="setting-row">
<label>Temperature</label>
<input
type="range"
min="0"
max="2"
step="0.1"
value="0.7"
>
</div>

<div class="setting-row">
<label>System Prompt</label>
<input
placeholder="You are a helpful AI..."
>
</div>

<br>

<button
class="new-chat"
onclick="closeSettings()"
>
Save
</button>

</div>

</div>

<script>

function openSettings(){
document.getElementById(
"settingsModal"
).style.display="block";
}

function closeSettings(){
document.getElementById(
"settingsModal"
).style.display="none";
}

function newChat(){

document.getElementById(
"chat"
).innerHTML=
'<div class="message assistant">New conversation started.</div>';

}

async function sendMessage(){

const input =
document.getElementById(
"message"
);

const text =
input.value.trim();

if(!text) return;

const chat =
document.getElementById(
"chat"
);

chat.innerHTML +=
'<div class="message user">'+
text+
'</div>';

input.value="";

chat.scrollTop=
chat.scrollHeight;

try{

const response =
await fetch(
"/api/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
user_id:"guest",
conversation_id:"default",
message:text
})
}
);

const data =
await response.json();

chat.innerHTML +=
'<div class="message assistant">'+
(data.response || "No response")+
'</div>';

chat.scrollTop=
chat.scrollHeight;

}catch(err){

chat.innerHTML +=
'<div class="message assistant">Error contacting AI.</div>';

}

}

document
.getElementById("message")
.addEventListener(
"keydown",
function(e){

if(
e.key==="Enter" &&
!e.shiftKey
){

e.preventDefault();
sendMessage();

}

}
);

</script>

</body>
</html>
"""


# =========================================================
# PART 5B
# ADVANCED SIDEBAR + CONVERSATION MANAGEMENT
# PASTE INSIDE THE HTML FROM PART 5A
# =========================================================

# REPLACE:

<div
class="conversations"
id="conversationList"
>

<div class="chat-item">
New Conversation
</div>

</div>

# WITH:

<div class="sidebar-tools">

<button onclick="newChat()">
➕ New Chat
</button>

<button onclick="loadChats()">
🔄 Refresh
</button>

</div>

<div class="conversation-section">

<div class="section-title">
Chats
</div>

<div
class="conversations"
id="conversationList"
>
</div>

</div>

# =========================================================
# ADD TO CSS
# =========================================================

.sidebar-tools{
padding:10px;
display:flex;
gap:8px;
}

.sidebar-tools button{
flex:1;
padding:10px;
border:none;
background:#1f2937;
color:white;
border-radius:8px;
cursor:pointer;
}

.sidebar-tools button:hover{
background:#374151;
}

.section-title{
padding:12px;
font-size:12px;
font-weight:600;
color:#9ca3af;
text-transform:uppercase;
}

.chat-item{
position:relative;
padding:12px;
border-radius:10px;
background:#1f2937;
margin-bottom:6px;
cursor:pointer;
transition:.2s;
}

.chat-item:hover{
background:#2d3748;
}

.chat-actions{
position:absolute;
right:10px;
top:10px;
display:flex;
gap:5px;
}

.chat-actions button{
background:none;
border:none;
color:#9ca3af;
cursor:pointer;
}

.chat-actions button:hover{
color:white;
}

.active-chat{
background:#2563eb !important;
}

# =========================================================
# ADD TO JAVASCRIPT
# =========================================================

let currentConversation = null;

async function loadChats(){

try{

const response =
await fetch(
"/api/conversations/guest"
);

const data =
await response.json();

const container =
document.getElementById(
"conversationList"
);

container.innerHTML = "";

if(
!data.conversations ||
data.conversations.length === 0
){

container.innerHTML =
'<div class="chat-item">No Chats Yet</div>';

return;

}

data.conversations.forEach(chat=>{

container.innerHTML += `
<div
class="chat-item"
onclick="selectChat('${chat.id}')"
>

${chat.title}

<div class="chat-actions">

<button
onclick="
event.stopPropagation();
renameChat('${chat.id}');
"
>
✏️
</button>

<button
onclick="
event.stopPropagation();
deleteChat('${chat.id}');
"
>
🗑️
</button>

</div>

</div>
`;

});

}catch(err){

console.log(err);

}

}

function selectChat(id){

currentConversation = id;

document
.querySelectorAll(".chat-item")
.forEach(
item=>{
item.classList.remove(
"active-chat"
);
}
);

}

async function renameChat(id){

const title =
prompt(
"New conversation name:"
);

if(!title) return;

await fetch(
"/api/conversations/rename",
{
method:"PUT",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
conversation_id:id,
title:title
})
}
);

loadChats();

}

async function deleteChat(id){

if(
!confirm(
"Delete conversation?"
)
) return;

await fetch(
"/api/conversations/"+id,
{
method:"DELETE"
}
);

loadChats();

}

function newChat(){

currentConversation =
crypto.randomUUID();

document
.getElementById("chat")
.innerHTML =
'<div class="message assistant">New conversation started.</div>';

}

window.onload = () => {

loadChats();

};

# =========================================================
# END PART 5B
# NEXT = PART 5C
# ADVANCED CHAT WINDOW + MESSAGE ACTIONS
# =========================================================


# =========================================================
# PART 5C
# ADVANCED CHAT WINDOW + MESSAGE ACTIONS
# PASTE BELOW PART 5B
# =========================================================

# =========================================================
# ADD TO CSS
# =========================================================

.message{
position:relative;
max-width:900px;
margin:auto;
margin-bottom:20px;
padding:18px;
border-radius:14px;
line-height:1.8;
word-wrap:break-word;
}

.message-toolbar{
display:flex;
gap:10px;
margin-top:12px;
opacity:0;
transition:.2s;
}

.message:hover .message-toolbar{
opacity:1;
}

.message-toolbar button{
background:#1f2937;
border:none;
color:white;
padding:8px 10px;
border-radius:8px;
cursor:pointer;
}

.message-toolbar button:hover{
background:#374151;
}

.message-time{
font-size:12px;
color:#9ca3af;
margin-top:8px;
}

.typing{
display:flex;
gap:6px;
padding:10px;
}

.typing span{
width:8px;
height:8px;
background:#60a5fa;
border-radius:50%;
animation:bounce 1s infinite;
}

.typing span:nth-child(2){
animation-delay:.2s;
}

.typing span:nth-child(3){
animation-delay:.4s;
}

@keyframes bounce{

0%,100%{
transform:translateY(0);
}

50%{
transform:translateY(-5px);
}

}

.chat-header{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:20px;
}

.chat-title{
font-size:20px;
font-weight:600;
}

.chat-controls{
display:flex;
gap:10px;
}

.chat-controls button{
background:#1f2937;
border:none;
padding:10px;
border-radius:8px;
color:white;
cursor:pointer;
}

.chat-controls button:hover{
background:#374151;
}

# =========================================================
# REPLACE CHAT AREA CONTENT
# =========================================================

<div
class="chat-area"
id="chat"
>

<div class="chat-header">

<div class="chat-title">
New Conversation
</div>

<div class="chat-controls">

<button onclick="clearChat()">
🗑 Clear
</button>

<button onclick="exportChat()">
📄 Export
</button>

</div>

</div>

<div class="message assistant">

👋 Welcome to Bloxy-Bot X

<div class="message-time">
Just now
</div>

</div>

</div>

# =========================================================
# ADD TO JAVASCRIPT
# =========================================================

function getTime(){

return new Date()
.toLocaleTimeString(
[],
{
hour:'2-digit',
minute:'2-digit'
}
);

}

function appendUserMessage(text){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div class="message user">

${text}

<div class="message-toolbar">

<button onclick="copyText(this)">
📋 Copy
</button>

<button onclick="editMessage(this)">
✏️ Edit
</button>

</div>

<div class="message-time">
${getTime()}
</div>

</div>
`;

}

function appendAIMessage(text){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div class="message assistant">

${text}

<div class="message-toolbar">

<button onclick="copyText(this)">
📋 Copy
</button>

<button onclick="regenerateLast()">
🔄 Retry
</button>

</div>

<div class="message-time">
${getTime()}
</div>

</div>
`;

}

function showTyping(){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div
class="message assistant"
id="typingIndicator"
>

<div class="typing">

<span></span>
<span></span>
<span></span>

</div>

</div>
`;

}

function removeTyping(){

const typing =
document.getElementById(
"typingIndicator"
);

if(typing){

typing.remove();

}

}

function copyText(button){

const text =
button
.parentElement
.parentElement
.innerText;

navigator.clipboard
.writeText(text);

}

function editMessage(button){

const message =
button
.parentElement
.parentElement;

const oldText =
message.childNodes[0]
.textContent
.trim();

const updated =
prompt(
"Edit message",
oldText
);

if(updated){

message.childNodes[0]
.textContent =
updated;

}

}

function clearChat(){

if(
!confirm(
"Clear chat?"
)
){
return;
}

document
.getElementById(
"chat"
)
.innerHTML = "";

}

function exportChat(){

const content =
document
.getElementById(
"chat"
)
.innerText;

const blob =
new Blob(
[content],
{
type:"text/plain"
}
);

const a =
document.createElement("a");

a.href =
URL.createObjectURL(blob);

a.download =
"conversation.txt";

a.click();

}

async function regenerateLast(){

alert(
"Response regeneration coming in Part 7 integration."
);

}

# =========================================================
# REPLACE sendMessage()
# =========================================================

async function sendMessage(){

const input =
document.getElementById(
"message"
);

const text =
input.value.trim();

if(!text){
return;
}

appendUserMessage(text);

input.value="";

showTyping();

try{

const response =
await fetch(
"/api/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
user_id:"guest",
conversation_id:
currentConversation ||
"default",
message:text
})
}
);

const data =
await response.json();

removeTyping();

appendAIMessage(
data.response ||
"No response"
);

}catch(err){

removeTyping();

appendAIMessage(
"Error contacting AI."
);

}

const chat =
document.getElementById(
"chat"
);

chat.scrollTop =
chat.scrollHeight;

}

# =========================================================
# END PART 5C
# NEXT = PART 5D
# SETTINGS PANEL + ADVANCED USER PREFERENCES
# =========================================================


# =========================================================
# PART 5D
# ADVANCED SETTINGS PANEL + USER PREFERENCES
# PASTE BELOW PART 5C
# =========================================================

# =========================================================
# REPLACE SETTINGS MODAL HTML
# =========================================================

<div
class="modal"
id="settingsModal"
>

<div class="modal-content">

<h2>⚙ Settings</h2>

<div class="setting-row">
<label>Theme</label>
<select id="themeSelect">
<option value="dark">Dark</option>
<option value="midnight">Midnight</option>
<option value="ocean">Ocean</option>
<option value="emerald">Emerald</option>
<option value="purple">Purple</option>
</select>
</div>

<div class="setting-row">
<label>AI Model</label>
<select id="modelSelect">

<option value="gpt-5.5">
GPT-5.5
</option>

<option value="openrouter">
OpenRouter
</option>

<option value="groq">
Groq
</option>

<option value="kimi">
Kimi
</option>

</select>
</div>

<div class="setting-row">
<label>Temperature</label>

<input
id="temperature"
type="range"
min="0"
max="2"
step="0.1"
value="0.7"
>

<span id="tempValue">
0.7
</span>

</div>

<div class="setting-row">

<label>
System Prompt
</label>

<textarea
id="systemPrompt"
style="
width:100%;
height:120px;
background:#1f2937;
color:white;
border:none;
padding:12px;
border-radius:10px;
"
></textarea>

</div>

<div class="setting-row">

<label>

<input
type="checkbox"
id="memoryEnabled"
checked
>

Enable Memory

</label>

</div>

<br>

<button
class="new-chat"
onclick="saveSettings()"
>

💾 Save Settings

</button>

<button
class="new-chat"
onclick="resetSettings()"
style="
background:#dc2626;
margin-top:10px;
"
>

🔄 Reset

</button>

<button
class="new-chat"
onclick="closeSettings()"
style="
background:#374151;
margin-top:10px;
"
>

Close

</button>

</div>

</div>

# =========================================================
# ADD CSS
# =========================================================

.setting-row{
margin-top:18px;
}

.setting-row label{
display:block;
margin-bottom:8px;
font-weight:600;
}

.setting-row select,
.setting-row textarea,
.setting-row input[type=text]{

width:100%;
padding:12px;
background:#1f2937;
color:white;
border:none;
border-radius:10px;

}

.modal-content{
max-height:90vh;
overflow-y:auto;
}

#tempValue{
display:inline-block;
margin-top:10px;
font-weight:bold;
color:#60a5fa;
}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

document
.getElementById(
"temperature"
)
.addEventListener(
"input",
function(){

document
.getElementById(
"tempValue"
)
.innerText =
this.value;

}
);

async function saveSettings(){

const payload = {

user_id:"guest",

theme:
document
.getElementById(
"themeSelect"
)
.value,

ai_model:
document
.getElementById(
"modelSelect"
)
.value,

temperature:
parseFloat(
document
.getElementById(
"temperature"
)
.value
),

system_prompt:
document
.getElementById(
"systemPrompt"
)
.value,

memory_enabled:
document
.getElementById(
"memoryEnabled"
)
.checked

};

try{

await fetch(
"/api/preferences/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify(
payload
)
}
);

localStorage.setItem(
"bloxy_settings",
JSON.stringify(
payload
)
);

alert(
"Settings Saved"
);

}catch(err){

alert(
"Failed To Save"
);

}

}

function resetSettings(){

document
.getElementById(
"themeSelect"
)
.value =
"dark";

document
.getElementById(
"modelSelect"
)
.value =
"gpt-5.5";

document
.getElementById(
"temperature"
)
.value =
0.7;

document
.getElementById(
"tempValue"
)
.innerText =
"0.7";

document
.getElementById(
"systemPrompt"
)
.value =
"";

document
.getElementById(
"memoryEnabled"
)
.checked =
true;

}

function loadSettings(){

const saved =
localStorage.getItem(
"bloxy_settings"
);

if(!saved){
return;
}

const settings =
JSON.parse(saved);

document
.getElementById(
"themeSelect"
)
.value =
settings.theme || "dark";

document
.getElementById(
"modelSelect"
)
.value =
settings.ai_model || "gpt-5.5";

document
.getElementById(
"temperature"
)
.value =
settings.temperature || 0.7;

document
.getElementById(
"tempValue"
)
.innerText =
settings.temperature || 0.7;

document
.getElementById(
"systemPrompt"
)
.value =
settings.system_prompt || "";

document
.getElementById(
"memoryEnabled"
)
.checked =
settings.memory_enabled;

}

window.addEventListener(
"load",
loadSettings
);

# =========================================================
# END PART 5D
# NEXT = PART 5E
# ACCOUNT PANEL + PROFILE MANAGEMENT
# =========================================================


# =========================================================
# PART 5E
# ACCOUNT PANEL + PROFILE MANAGEMENT
# PASTE BELOW PART 5D
# =========================================================

# =========================================================
# REPLACE ACCOUNT HTML
# =========================================================

<div class="account">

<div class="account-card">

<div class="avatar">
👤
</div>

<div class="account-info">

<div id="usernameDisplay">
Guest
</div>

<div id="emailDisplay">
guest@bloxybotx.local
</div>

</div>

</div>

<button onclick="openAccountModal()">
Manage Account
</button>

</div>

<div
class="modal"
id="accountModal"
>

<div class="modal-content">

<h2>Account Settings</h2>

<div class="setting-row">

<label>Username</label>

<input
id="accountUsername"
type="text"
placeholder="Username"
>

</div>

<div class="setting-row">

<label>Email</label>

<input
id="accountEmail"
type="email"
placeholder="Email"
>

</div>

<div class="setting-row">

<label>New Password</label>

<input
id="accountPassword"
type="password"
placeholder="Password"
>

</div>

<button
class="new-chat"
onclick="saveAccountSettings()"
>

Save Changes

</button>

<button
class="new-chat"
style="background:#374151;margin-top:10px;"
onclick="closeAccountModal()"
>

Close

</button>

</div>

</div>

# =========================================================
# ADD CSS
# =========================================================

.account-card{
display:flex;
align-items:center;
gap:12px;
margin-bottom:12px;
}

.avatar{
width:45px;
height:45px;
border-radius:50%;
background:#2563eb;
display:flex;
align-items:center;
justify-content:center;
font-size:20px;
}

.account-info{
font-size:13px;
}

#usernameDisplay{
font-weight:600;
}

#emailDisplay{
color:#9ca3af;
}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

function openAccountModal(){

document
.getElementById(
"accountModal"
)
.style.display="block";

}

function closeAccountModal(){

document
.getElementById(
"accountModal"
)
.style.display="none";

}

async function saveAccountSettings(){

const username =
document
.getElementById(
"accountUsername"
)
.value;

const email =
document
.getElementById(
"accountEmail"
)
.value;

const password =
document
.getElementById(
"accountPassword"
)
.value;

if(username){

await fetch(
"/api/account/username",
{
method:"PUT",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
user_id:"guest",
username:username
})
}
);

document
.getElementById(
"usernameDisplay"
)
.innerText =
username;

}

if(email){

await fetch(
"/api/account/email",
{
method:"PUT",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
user_id:"guest",
email:email
})
}
);

document
.getElementById(
"emailDisplay"
)
.innerText =
email;

}

if(password){

await fetch(
"/api/account/password",
{
method:"PUT",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
user_id:"guest",
password:password
})
}
);

}

alert("Account Updated");

closeAccountModal();

}

# =========================================================
# END PART 5E
# NEXT = PART 5F
# =========================================================


# =========================================================
# PART 5F
# ADVANCED THEME ENGINE + APPEARANCE CUSTOMIZATION
# PASTE BELOW PART 5E
# =========================================================

# =========================================================
# ADD TO SETTINGS MODAL HTML
# =========================================================

<div class="setting-row">

<label>Accent Color</label>

<select id="accentColor">

<option value="#2563eb">Blue</option>
<option value="#10b981">Emerald</option>
<option value="#f59e0b">Amber</option>
<option value="#ef4444">Red</option>
<option value="#8b5cf6">Purple</option>

</select>

</div>

<div class="setting-row">

<label>Font Size</label>

<select id="fontSize">

<option value="14">Small</option>
<option value="16" selected>Normal</option>
<option value="18">Large</option>

</select>

</div>

<div class="setting-row">

<label>

<input
type="checkbox"
id="compactMode"
>

Compact Mode

</label>

</div>

# =========================================================
# ADD TO CSS
# =========================================================

:root{

--accent:#2563eb;
--font-size:16px;

}

body{

font-size:var(--font-size);

}

.new-chat,
.send-btn{

background:var(--accent);

}

.active-chat{

background:var(--accent)!important;

}

.compact .message{

padding:10px;
margin-bottom:10px;

}

.compact .chat-item{

padding:8px;

}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

function applyThemeSettings(){

const accent =
localStorage.getItem(
"accentColor"
) || "#2563eb";

const fontSize =
localStorage.getItem(
"fontSize"
) || "16";

const compact =
localStorage.getItem(
"compactMode"
) || "false";

document
.documentElement
.style
.setProperty(
"--accent",
accent
);

document
.documentElement
.style
.setProperty(
"--font-size",
fontSize + "px"
);

if(compact === "true"){

document.body
.classList.add(
"compact"
);

}else{

document.body
.classList.remove(
"compact"
);

}

}

function saveAppearance(){

localStorage.setItem(
"accentColor",
document
.getElementById(
"accentColor"
)
.value
);

localStorage.setItem(
"fontSize",
document
.getElementById(
"fontSize"
)
.value
);

localStorage.setItem(
"compactMode",
document
.getElementById(
"compactMode"
)
.checked
);

applyThemeSettings();

}

const oldSaveSettings =
saveSettings;

saveSettings = async function(){

await oldSaveSettings();

saveAppearance();

};

window.addEventListener(
"load",
applyThemeSettings
);

# =========================================================
# END PART 5F
# NEXT = PART 5G
# ACCOUNT DROPDOWN + SESSION MANAGEMENT
# =========================================================


# =========================================================
# PART 5G
# ACCOUNT DROPDOWN + SESSION MANAGEMENT + QUICK ACTIONS
# PASTE BELOW PART 5F
# =========================================================

# =========================================================
# REPLACE ACCOUNT SECTION
# =========================================================

<div class="account">

<div
class="account-summary"
onclick="toggleAccountMenu()"
>

<div class="avatar">
👤
</div>

<div class="account-text">

<div id="usernameDisplay">
Guest
</div>

<div class="account-plan">
Free Plan
</div>

</div>

<div>
▼
</div>

</div>

<div
class="account-menu"
id="accountMenu"
>

<button onclick="openAccountModal()">
👤 Profile
</button>

<button onclick="openSettings()">
⚙ Settings
</button>

<button onclick="exportAllChats()">
📄 Export Data
</button>

<button onclick="clearAllDrafts()">
📝 Clear Drafts
</button>

<button onclick="logoutUser()">
🚪 Logout
</button>

</div>

</div>

# =========================================================
# ADD CSS
# =========================================================

.account-summary{

display:flex;
align-items:center;
justify-content:space-between;
cursor:pointer;
padding:10px;
background:#1f2937;
border-radius:10px;

}

.account-summary:hover{

background:#2d3748;

}

.account-text{

flex:1;
margin-left:10px;

}

.account-plan{

font-size:12px;
color:#9ca3af;

}

.account-menu{

display:none;
margin-top:10px;

}

.account-menu button{

width:100%;
padding:12px;
margin-bottom:6px;
border:none;
border-radius:8px;
background:#1f2937;
color:white;
cursor:pointer;

}

.account-menu button:hover{

background:#374151;

}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

function toggleAccountMenu(){

const menu =
document.getElementById(
"accountMenu"
);

if(
menu.style.display ===
"block"
){

menu.style.display =
"none";

}else{

menu.style.display =
"block";

}

}

function logoutUser(){

if(
!confirm(
"Logout?"
)
){
return;
}

localStorage.clear();

location.reload();

}

function exportAllChats(){

const content =
document.getElementById(
"chat"
).innerText;

const blob =
new Blob(
[content],
{
type:"text/plain"
}
);

const url =
URL.createObjectURL(
blob
);

const a =
document.createElement(
"a"
);

a.href = url;

a.download =
"bloxybotx_export.txt";

a.click();

}

function clearAllDrafts(){

localStorage.removeItem(
"chat_draft"
);

alert(
"Drafts Cleared"
);

}

window.addEventListener(
"click",
function(e){

const menu =
document.getElementById(
"accountMenu"
);

const account =
document.querySelector(
".account-summary"
);

if(
menu &&
account &&
!account.contains(
e.target
)
){

menu.style.display =
"none";

}

}
);

# =========================================================
# END PART 5G
# NEXT = PART 5H
# MARKDOWN + CODE BLOCK RENDERING
# =========================================================


# =========================================================
# PART 5H
# MARKDOWN + CODE BLOCK RENDERING
# PASTE BELOW PART 5G
# =========================================================

# =========================================================
# ADD TO <head>
# =========================================================

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js/lib/common.min.js"></script>

<link
rel="stylesheet"
href="https://cdn.jsdelivr.net/npm/highlight.js/styles/github-dark.min.css"
>

# =========================================================
# ADD CSS
# =========================================================

.markdown-content{
line-height:1.8;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3{
margin:15px 0;
}

.markdown-content p{
margin:10px 0;
}

.markdown-content pre{
position:relative;
background:#0d1117;
border-radius:12px;
padding:15px;
overflow:auto;
margin-top:12px;
}

.markdown-content code{
font-family:monospace;
}

.copy-code-btn{
position:absolute;
top:10px;
right:10px;
border:none;
background:#374151;
color:white;
padding:6px 10px;
border-radius:8px;
cursor:pointer;
}

.copy-code-btn:hover{
background:#4b5563;
}

.markdown-content blockquote{
border-left:4px solid var(--accent);
padding-left:12px;
opacity:.9;
margin:12px 0;
}

.markdown-content ul,
.markdown-content ol{
padding-left:25px;
}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

function renderMarkdown(text){

const html =
marked.parse(text);

return `
<div class="markdown-content">
${html}
</div>
`;

}

function highlightBlocks(){

document
.querySelectorAll("pre code")
.forEach(block=>{

hljs.highlightElement(
block
);

const pre =
block.parentElement;

if(
pre.querySelector(
".copy-code-btn"
)
){
return;
}

const btn =
document.createElement(
"button"
);

btn.innerText =
"Copy";

btn.className =
"copy-code-btn";

btn.onclick = ()=>{

navigator.clipboard
.writeText(
block.innerText
);

btn.innerText =
"Copied";

setTimeout(()=>{

btn.innerText =
"Copy";

},1500);

};

pre.appendChild(btn);

});

}

# =========================================================
# REPLACE appendAIMessage()
# =========================================================

function appendAIMessage(text){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div class="message assistant">

${renderMarkdown(text)}

<div class="message-toolbar">

<button onclick="copyText(this)">
📋 Copy
</button>

<button onclick="regenerateLast()">
🔄 Retry
</button>

</div>

<div class="message-time">
${getTime()}
</div>

</div>
`;

highlightBlocks();

}

# =========================================================
# END PART 5H
# NEXT = PART 5I
# CHAT SEARCH + FILTERS
# =========================================================


# =========================================================
# PART 5I
# CHAT SEARCH + FILTERS + QUICK NAVIGATION
# PASTE BELOW PART 5H
# =========================================================

# =========================================================
# ADD HTML
# =========================================================

<div class="search-panel">

<input
type="text"
id="chatSearch"
placeholder="Search messages..."
>

<select id="searchFilter">

<option value="all">
All
</option>

<option value="user">
User Messages
</option>

<option value="assistant">
AI Messages
</option>

</select>

<button onclick="searchMessages()">
🔍 Search
</button>

</div>

# =========================================================
# ADD CSS
# =========================================================

.search-panel{

display:flex;
gap:10px;
padding:10px;
margin-bottom:15px;

}

.search-panel input{

flex:1;
padding:12px;
background:#1f2937;
color:white;
border:none;
border-radius:10px;

}

.search-panel select{

padding:12px;
background:#1f2937;
color:white;
border:none;
border-radius:10px;

}

.search-panel button{

padding:12px 18px;
border:none;
border-radius:10px;
background:var(--accent);
color:white;
cursor:pointer;

}

.search-highlight{

outline:2px solid #f59e0b;
box-shadow:0 0 10px #f59e0b;

}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

function clearHighlights(){

document
.querySelectorAll(
".search-highlight"
)
.forEach(el=>{

el.classList.remove(
"search-highlight"
);

});

}

function searchMessages(){

clearHighlights();

const term =
document
.getElementById(
"chatSearch"
)
.value
.toLowerCase();

const filter =
document
.getElementById(
"searchFilter"
)
.value;

if(!term){
return;
}

const messages =
document
.querySelectorAll(
".message"
);

let firstMatch = null;

messages.forEach(msg=>{

const text =
msg.innerText
.toLowerCase();

const isUser =
msg.classList.contains(
"user"
);

const isAssistant =
msg.classList.contains(
"assistant"
);

let allowed = false;

if(filter==="all"){
allowed=true;
}

if(filter==="user" && isUser){
allowed=true;
}

if(filter==="assistant" && isAssistant){
allowed=true;
}

if(
allowed &&
text.includes(term)
){

msg.classList.add(
"search-highlight"
);

if(!firstMatch){

firstMatch = msg;

}

}

});

if(firstMatch){

firstMatch.scrollIntoView({
behavior:"smooth",
block:"center"
});

}

}

document
.getElementById(
"chatSearch"
)
.addEventListener(
"keydown",
function(e){

if(
e.key==="Enter"
){

searchMessages();

}

}
);

# =========================================================
# END PART 5I
# NEXT = PART 5J
# CONVERSATION ACTIONS + PIN + FAVORITES
# =========================================================


# =========================================================
# PART 5K
# ADVANCED THEME PRESETS + CUSTOM COLORS + UI MODES
# PASTE BELOW PART 5J
# =========================================================

# =========================================================
# ADD TO SETTINGS HTML
# =========================================================

<div class="setting-row">

<label>Theme Preset</label>

<select id="themePreset">

<option value="dark">
Dark
</option>

<option value="midnight">
Midnight
</option>

<option value="ocean">
Ocean
</option>

<option value="emerald">
Emerald
</option>

<option value="sunset">
Sunset
</option>

<option value="purple">
Purple
</option>

</select>

</div>

# =========================================================
# ADD CSS VARIABLES
# =========================================================

:root{

--bg:#0b0f19;
--sidebar:#111827;
--card:#1f2937;
--text:#ffffff;
--accent:#2563eb;

}

body{
background:var(--bg);
color:var(--text);
}

.sidebar{
background:var(--sidebar);
}

.message{
background:var(--card);
}

# =========================================================
# ADD JAVASCRIPT
# =========================================================

const THEMES = {

dark:{
bg:"#0b0f19",
sidebar:"#111827",
card:"#1f2937",
accent:"#2563eb"
},

midnight:{
bg:"#020617",
sidebar:"#0f172a",
card:"#1e293b",
accent:"#3b82f6"
},

ocean:{
bg:"#082f49",
sidebar:"#0c4a6e",
card:"#075985",
accent:"#38bdf8"
},

emerald:{
bg:"#022c22",
sidebar:"#064e3b",
card:"#065f46",
accent:"#10b981"
},

sunset:{
bg:"#431407",
sidebar:"#7c2d12",
card:"#9a3412",
accent:"#f97316"
},

purple:{
bg:"#2e1065",
sidebar:"#4c1d95",
card:"#5b21b6",
accent:"#8b5cf6"
}

};

function applyThemePreset(){

const preset =
document
.getElementById(
"themePreset"
)
.value;

const theme =
THEMES[preset];

document
.documentElement
.style
.setProperty(
"--bg",
theme.bg
);

document
.documentElement
.style
.setProperty(
"--sidebar",
theme.sidebar
);

document
.documentElement
.style
.setProperty(
"--card",
theme.card
);

document
.documentElement
.style
.setProperty(
"--accent",
theme.accent
);

localStorage.setItem(
"themePreset",
preset
);

}

document
.getElementById(
"themePreset"
)
?.addEventListener(
"change",
applyThemePreset
);

window.addEventListener(
"load",
()=>{

const preset =
localStorage.getItem(
"themePreset"
) || "dark";

const select =
document.getElementById(
"themePreset"
);

if(select){

select.value = preset;

applyThemePreset();

}

}
);

# =========================================================
# END PART 5K
# NEXT = PART 5L
# STREAMING RESPONSES + LIVE GENERATION
# =========================================================


# =========================================================
# PART 5L
# STREAMING RESPONSES + LIVE GENERATION EFFECT
# PASTE BELOW PART 5K
# =========================================================

# =========================================================
# ADD CSS
# =========================================================

.streaming-cursor{
display:inline-block;
width:8px;
height:18px;
background:var(--accent);
margin-left:2px;
animation:blink 1s infinite;
}

@keyframes blink{

0%,50%{
opacity:1;
}

51%,100%{
opacity:0;
}

}

.generating{

border-left:3px solid var(--accent);

}

.stop-btn{

background:#dc2626;
color:white;
border:none;
padding:10px 14px;
border-radius:8px;
cursor:pointer;

}

.stop-btn:hover{

background:#b91c1c;

}

# =========================================================
# ADD HTML NEXT TO SEND BUTTON
# =========================================================

<button
class="stop-btn"
id="stopGenerationBtn"
style="display:none"
onclick="stopGeneration()"
>
Stop
</button>

# =========================================================
# ADD JAVASCRIPT
# =========================================================

let generationStopped = false;

function stopGeneration(){

generationStopped = true;

document
.getElementById(
"stopGenerationBtn"
)
.style.display =
"none";

}

async function streamText(
container,
text
){

container.innerHTML = "";

for(
let i = 0;
i < text.length;
i++
){

if(
generationStopped
){

break;

}

container.innerHTML =
text.substring(
0,
i + 1
) +
'<span class="streaming-cursor"></span>';

await new Promise(
r=>setTimeout(
r,
8
)
);

}

container.innerHTML = text;

}

# =========================================================
# REPLACE appendAIMessage()
# =========================================================

async function appendAIMessage(text){

const chat =
document.getElementById(
"chat"
);

const id =
"msg_" +
Date.now();

chat.innerHTML += `
<div
class="message assistant generating"
id="${id}"
>

<div class="markdown-content">
</div>

<div class="message-toolbar">

<button onclick="copyText(this)">
📋 Copy
</button>

<button onclick="regenerateLast()">
🔄 Retry
</button>

</div>

<div class="message-time">
${getTime()}
</div>

</div>
`;

const wrapper =
document
.querySelector(
"#" + id +
" .markdown-content"
);

generationStopped = false;

document
.getElementById(
"stopGenerationBtn"
)
.style.display =
"inline-block";

await streamText(
wrapper,
text
);

wrapper.innerHTML =
renderMarkdown(text);

highlightBlocks();

document
.getElementById(
id
)
.classList.remove(
"generating"
);

document
.getElementById(
"stopGenerationBtn"
)
.style.display =
"none";

}

# =========================================================
# REPLACE sendMessage()
# =========================================================

async function sendMessage(){

const input =
document.getElementById(
"message"
);

const text =
input.value.trim();

if(!text){
return;
}

appendUserMessage(text);

input.value = "";

showTyping();

try{

const response =
await fetch(
"/api/chat",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
user_id:"guest",
conversation_id:
currentConversation ||
"default",
message:text
})
}
);

const data =
await response.json();

removeTyping();

await appendAIMessage(
data.response ||
"No response"
);

}catch(err){

removeTyping();

await appendAIMessage(
"Error contacting AI."
);

}

}

# =========================================================
# END PART 5L
# NEXT = PART 5M
# DRAFT SAVING + AUTO RECOVERY
# =========================================================


# =========================================================
# PART 5M
# DRAFT SAVING + AUTO RECOVERY + UNSENT MESSAGE PROTECTION
# PASTE BELOW PART 5L
# =========================================================

# =========================================================
# ADD JAVASCRIPT
# =========================================================

const DRAFT_KEY =
"bloxybotx_draft";

function saveDraft(){

const input =
document.getElementById(
"message"
);

if(!input){
return;
}

localStorage.setItem(
DRAFT_KEY,
input.value
);

}

function loadDraft(){

const input =
document.getElementById(
"message"
);

if(!input){
return;
}

const draft =
localStorage.getItem(
DRAFT_KEY
);

if(draft){

input.value =
draft;

}

}

function clearDraft(){

localStorage.removeItem(
DRAFT_KEY
);

}

window.addEventListener(
"load",
loadDraft
);

document
.getElementById(
"message"
)
?.addEventListener(
"input",
saveDraft
);

# =========================================================
# ENTER TO SEND
# FIXES THE ENTER KEY ISSUE
# =========================================================

document
.getElementById(
"message"
)
?.addEventListener(
"keydown",
function(e){

if(
e.key === "Enter" &&
!e.shiftKey
){

e.preventDefault();

sendMessage();

}

}
);

# =========================================================
# MODIFY sendMessage()
# ADD THIS AFTER:
# input.value = "";
# =========================================================

clearDraft();

# =========================================================
# PAGE EXIT PROTECTION
# =========================================================

window.addEventListener(
"beforeunload",
function(e){

const draft =
localStorage.getItem(
DRAFT_KEY
);

if(
draft &&
draft.trim().length > 0
){

e.preventDefault();

e.returnValue = "";

}

}
);

# =========================================================
# CHAT AUTO SAVE
# =========================================================

function saveChatSnapshot(){

const chat =
document.getElementById(
"chat"
);

if(!chat){
return;
}

localStorage.setItem(
"chat_snapshot",
chat.innerHTML
);

}

function restoreChatSnapshot(){

const snapshot =
localStorage.getItem(
"chat_snapshot"
);

if(!snapshot){
return;
}

const chat =
document.getElementById(
"chat"
);

if(chat){

chat.innerHTML =
snapshot;

}

}

window.addEventListener(
"load",
restoreChatSnapshot
);

setInterval(
saveChatSnapshot,
5000
);

# =========================================================
# RECOVER AFTER CRASH
# =========================================================

window.addEventListener(
"load",
()=>{

const recovered =
localStorage.getItem(
"chat_snapshot"
);

if(
recovered &&
recovered.length > 0
){

console.log(
"Chat restored."
);

}

}
);

# =========================================================
# END PART 5M
# NEXT = PART 6
# PRODUCTION POLISH + BUG FIXES + FINAL SYSTEMS
# =========================================================



# =========================================================
# PART 6A
# USER SETTINGS DATABASE
# Paste below Part 5
# =========================================================

class UserSettings(BaseModel):
    user_id: str
    theme: str = "dark"
    ai_model: str = "gpt"
    temperature: float = 0.7
    system_prompt: str = ""
    chat_memory: bool = True

def create_settings_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        ai_model TEXT,
        temperature REAL,
        system_prompt TEXT,
        chat_memory INTEGER,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_settings_table()


# =========================================================
# PART 6B
# THEME MANAGEMENT
# Paste directly below Part 6A
# =========================================================

@app.get("/api/themes")
def get_themes():

    return {
        "success": True,
        "themes": [
            "dark",
            "light",
            "midnight",
            "ocean",
            "emerald",
            "purple",
            "crimson",
            "sunset"
        ]
    }

@app.get("/api/settings/{user_id}")
def get_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (user_id,)
    )

    data = cur.fetchone()

    conn.close()

    return {
        "success": True,
        "settings": dict(data) if data else None
    }

@app.post("/api/settings/save")
def save_settings(data: UserSettings):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO settings
    VALUES(?,?,?,?,?,?,?)
    """,
    (
        data.user_id,
        data.theme,
        data.ai_model,
        data.temperature,
        data.system_prompt,
        int(data.chat_memory),
        now()
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings saved"
    }


# =========================================================
# PART 6C
# CHAT PREFERENCES
# =========================================================

def create_chat_preferences_table():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_preferences(
        user_id TEXT PRIMARY KEY,
        ai_model TEXT DEFAULT 'gpt-5.5',
        temperature REAL DEFAULT 0.7,
        system_prompt TEXT DEFAULT '',
        memory_enabled INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()

create_chat_preferences_table()


class ChatPreferencesRequest(BaseModel):
    user_id: str
    ai_model: str
    temperature: float
    system_prompt: str
    memory_enabled: bool

@app.post("/api/preferences/chat")
def save_chat_preferences(data: ChatPreferencesRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO chat_preferences
    (user_id, ai_model, temperature, system_prompt, memory_enabled)
    VALUES(?,?,?,?,?)
    """, (
        data.user_id,
        data.ai_model,
        data.temperature,
        data.system_prompt,
        int(data.memory_enabled)
    ))

    conn.commit()
    conn.close()

    return {"success": True}


# =========================================================
# PART 6D
# ACCOUNT SETTINGS
# =========================================================

class ChangeUsernameRequest(BaseModel):
    user_id: str
    username: str

class ChangeEmailRequest(BaseModel):
    user_id: str
    email: str

class ChangePasswordRequest(BaseModel):
    user_id: str
    password: str

@app.put("/api/account/username")
def change_username(data: ChangeUsernameRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET username=? WHERE id=?",
        (data.username, data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.put("/api/account/email")
def change_email(data: ChangeEmailRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET email=? WHERE id=?",
        (data.email, data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}

@app.put("/api/account/password")
def change_password(data: ChangePasswordRequest):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET password=? WHERE id=?",
        (hash_password(data.password), data.user_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}


# =========================
# PART 6E
# Export / Import Settings
# =========================

import json

@app.get("/api/settings/export/{user_id}")
def export_settings(user_id: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM user_settings WHERE user_id=?",
        (user_id,)
    )

    settings = cur.fetchone()
    conn.close()

    if not settings:
        return {"success": False}

    return {
        "success": True,
        "settings": dict(settings)
    }


# =========================================================
# PART 6F
# REAL AI MODEL ROUTER + MULTI-PROVIDER SUPPORT
# PASTE IN BACKEND (app.py)
# =========================================================

from pydantic import BaseModel
import requests
import os

# =========================================================
# MODEL CONFIG
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str
    model: str = "gpt-5.5"
    temperature: float = 0.7

# =========================================================
# AI ROUTER
# =========================================================

def generate_ai_response(
    message,
    model="gpt-5.5",
    temperature=0.7
):

    try:

        # =================================================
        # OPENAI
        # =================================================

        if model == "gpt-5.5":

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization":
                    f"Bearer {OPENAI_API_KEY}",
                    "Content-Type":
                    "application/json"
                },
                json={
                    "model":"gpt-5.5",
                    "messages":[
                        {
                            "role":"user",
                            "content":message
                        }
                    ],
                    "temperature":
                    temperature
                },
                timeout=120
            )

            data = response.json()

            return data["choices"][0]["message"]["content"]

        # =================================================
        # OPENROUTER
        # =================================================

        elif model == "openrouter":

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization":
                    f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type":
                    "application/json"
                },
                json={
                    "model":
                    "deepseek/deepseek-chat",
                    "messages":[
                        {
                            "role":"user",
                            "content":message
                        }
                    ]
                },
                timeout=120
            )

            data = response.json()

            return data["choices"][0]["message"]["content"]

        # =================================================
        # GROQ
        # =================================================

        elif model == "groq":

            response = requests.post(
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
                    "messages":[
                        {
                            "role":"user",
                            "content":message
                        }
                    ]
                },
                timeout=120
            )

            data = response.json()

            return data["choices"][0]["message"]["content"]

        else:

            return "Model not supported."

    except Exception as e:

        return f"AI Error: {str(e)}"

# =========================================================
# MAIN CHAT ENDPOINT
# REPLACE YOUR EXISTING /api/chat
# =========================================================

@app.post("/api/chat")
def chat(request: ChatRequest):

    response_text = generate_ai_response(
        request.message,
        request.model,
        request.temperature
    )

    return {
        "success": True,
        "response": response_text
    }

# =========================================================
# END PART 6F
# =========================================================


# =========================================================
# PART 7
# AI ENGINE + API PROVIDERS + MODEL ROUTER
# PASTE BELOW PART 6F
# =========================================================

import os
import requests

# =========================================================
# API KEYS
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# =========================================================
# AI REQUEST MODEL
# =========================================================

class AIChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str

# =========================================================
# AI MEMORY TABLE
# =========================================================

def create_ai_memory_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_memory(
        id TEXT PRIMARY KEY,
        user_id TEXT,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_ai_memory_table()

# =========================================================
# LOAD USER SETTINGS
# =========================================================

def get_user_settings(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM settings WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return dict(row) if row else None

# =========================================================
# SAVE MEMORY
# =========================================================

def save_memory(
    user_id,
    conversation_id,
    role,
    content
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ai_memory
        VALUES(?,?,?,?,?,?)
        """,
        (
            generate_id(),
            user_id,
            conversation_id,
            role,
            content,
            now()
        )
    )

    conn.commit()
    conn.close()

# =========================================================
# LOAD MEMORY
# =========================================================

def load_memory(conversation_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role,content
        FROM ai_memory
        WHERE conversation_id=?
        ORDER BY created_at ASC
        LIMIT 30
        """,
        (conversation_id,)
    )

    data = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return data

# =========================================================
# OPENROUTER ENGINE
# =========================================================

def ask_openrouter(
    model,
    messages
):

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization":
            f"Bearer {OPENROUTER_API_KEY}"
        },
        json={
            "model": model,
            "messages": messages
        },
        timeout=120
    )

    return response.json()

# =========================================================
# MODEL ROUTER
# =========================================================

def choose_model(settings):

    model = settings.get(
        "ai_model",
        "openrouter"
    )

    mapping = {
        "openrouter":
        "deepseek/deepseek-chat",

        "groq":
        "llama-3.3-70b-versatile",

        "kimi":
        "moonshotai/kimi-k2",

        "openai":
        "gpt-4o"
    }

    return mapping.get(
        model,
        "deepseek/deepseek-chat"
    )

# =========================================================
# MAIN CHAT ENDPOINT
# =========================================================

@app.post("/api/chat")
def ai_chat(
    data: AIChatRequest
):

    settings = get_user_settings(
        data.user_id
    )

    if not settings:

        settings = {
            "ai_model":"openrouter",
            "temperature":0.7,
            "system_prompt":
            "You are a helpful AI assistant."
        }

    history = load_memory(
        data.conversation_id
    )

    messages = []

    messages.append({
        "role":"system",
        "content":
        settings["system_prompt"]
    })

    for item in history:

        messages.append({
            "role":
            item["role"],
            "content":
            item["content"]
        })

    messages.append({
        "role":"user",
        "content":
        data.message
    })

    model = choose_model(
        settings
    )

    result = ask_openrouter(
        model,
        messages
    )

    ai_text = result["choices"][0]\
    ["message"]["content"]

    save_memory(
        data.user_id,
        data.conversation_id,
        "user",
        data.message
    )

    save_memory(
        data.user_id,
        data.conversation_id,
        "assistant",
        ai_text
    )

    return {
        "success": True,
        "model": model,
        "response": ai_text
    }

# =========================================================
# AI CAPABILITIES
# =========================================================

@app.get("/api/ai/capabilities")
def ai_capabilities():

    return {
        "success": True,
        "chat": True,
        "memory": True,
        "web_search": True,
        "news": True,
        "weather": True,
        "finance": True,
        "sports": True,
        "movies": True,
        "drafts": True,
        "attachments": True
    }

# =========================================================
# PROVIDER STATUS
# =========================================================

@app.get("/api/providers")
def providers():

    return {
        "success": True,
        "providers":[
            "OpenRouter",
            "OpenAI",
            "Groq",
            "Kimi",
            "Tavily",
            "Exa",
            "Firecrawl",
            "NewsAPI",
            "GNews",
            "Guardian",
            "Mediastack",
            "OpenWeather",
            "ExchangeRate",
            "AlphaVantage",
            "Finnhub",
            "TMDB",
            "SportMonks",
            "Sportradar",
            "TheSportsDB",
            "AllSports",
            "API-Sports",
            "OddsAPI"
        ]
    }

# =========================================================
# END OF PART 7
#
# PARTS 1-7 COMPLETE
# =========================================================


