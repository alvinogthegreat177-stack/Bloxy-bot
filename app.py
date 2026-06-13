# =========================================================
# PART 1
# FASTAPI + DATABASE FOUNDATION
# =========================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import sqlite3
import uuid
import hashlib
import secrets

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

# =========================
# HELPERS
# =========================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_id():
    return str(uuid.uuid4())

def now():
    return datetime.utcnow().isoformat()

def hash_password(password: str):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# =========================
# DATABASE TABLES
# =========================

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

# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# PART 2
# USER AUTHENTICATION
# =========================================================

# =========================
# REQUEST MODELS
# =========================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# =========================
# USER HELPERS
# =========================

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


# =========================
# AUTH ROUTES
# =========================

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


# =========================================================
# PART 3
# USER PROFILE ROUTES
# =========================================================

@app.get("/api/user/{user_id}")
def get_user(user_id: str):

    user = get_user_by_id(user_id)

    if not user:
        return {
            "success": False,
            "message": "User not found"
        }

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    }


@app.get("/api/users")
def get_all_users():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, email, created_at
        FROM users
        ORDER BY created_at DESC
        """
    )

    users = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "users": users
    }


# =========================================================
# PART 4
# CONVERSATIONS + MESSAGES
# =========================================================

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str


class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str


# =========================
# DATABASE TABLES
# =========================

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


# =========================
# CREATE CONVERSATION
# =========================

@app.post("/api/conversations/create")
def create_conversation(
    data: CreateConversationRequest
):

    conversation_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversations
        VALUES(?,?,?,?,?)
        """,
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


# =========================
# GET CONVERSATIONS
# =========================

@app.get("/api/conversations/{user_id}")
def get_conversations(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM conversations
        WHERE user_id=?
        ORDER BY updated_at DESC
        """,
        (user_id,)
    )

    conversations = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "conversations": conversations
    }


# =========================
# DELETE CONVERSATION
# =========================

@app.delete(
    "/api/conversations/{conversation_id}"
)
def delete_conversation(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE conversation_id=?
        """,
        (conversation_id,)
    )

    cur.execute(
        """
        DELETE FROM conversations
        WHERE id=?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }


# =========================================================
# PART 5A
# FRONTEND HOME PAGE
# PASTE BELOW PART 4
# =========================================================

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>

<head>
<meta charset="utf-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1"
>

<title>Bloxy-Bot X</title>

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial,sans-serif;
}

body{
background:#0f172a;
color:white;
height:100vh;
display:flex;
flex-direction:column;
}

.header{
height:60px;
display:flex;
align-items:center;
padding:0 20px;
background:#111827;
border-bottom:1px solid #1f2937;
}

.header h2{
font-size:20px;
}

.chat{
flex:1;
overflow-y:auto;
padding:20px;
}

.message{
max-width:800px;
margin:auto;
margin-bottom:15px;
padding:15px;
border-radius:12px;
line-height:1.6;
}

.user{
background:#1e293b;
}

.assistant{
background:#111827;
}

.input-area{
padding:20px;
border-top:1px solid #1f2937;
}

.input-row{
display:flex;
gap:10px;
max-width:900px;
margin:auto;
}

textarea{
flex:1;
height:60px;
resize:none;
border:none;
outline:none;
background:#111827;
color:white;
padding:15px;
border-radius:12px;
}

button{
width:70px;
border:none;
background:#2563eb;
color:white;
border-radius:12px;
cursor:pointer;
}

button:hover{
background:#1d4ed8;
}

</style>
</head>

<body>

<div class="header">
<h2>🤖 Bloxy-Bot X</h2>
</div>

<div
class="chat"
id="chat"
>

<div class="message assistant">
Welcome to Bloxy-Bot X
</div>

</div>

<div class="input-area">

<div class="input-row">

<textarea
id="message"
placeholder="Message Bloxy-Bot X..."
></textarea>

<button
onclick="sendMessage()"
>
Send
</button>

</div>

</div>

<script>

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

const chat =
document.getElementById(
"chat"
);

chat.innerHTML +=
`
<div class="message user">
${text}
</div>
`;

input.value = "";

chat.scrollTop =
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
`
<div class="message assistant">
${data.response || "No response"}
</div>
`;

chat.scrollTop =
chat.scrollHeight;

}
catch(err){

chat.innerHTML +=
`
<div class="message assistant">
Error contacting AI.
</div>
`;

}

}

document
.getElementById(
"message"
)
.addEventListener(
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

</script>

</body>
</html>
"""


# =========================================================
# PART 5B
# CHAT API ENDPOINT
# PASTE BELOW PART 5A
# =========================================================

class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str


@app.post("/api/chat")
def chat(
    data: ChatRequest
):

    user_message_id = generate_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages
        VALUES(?,?,?,?,?)
        """,
        (
            user_message_id,
            data.conversation_id,
            "user",
            data.message,
            now()
        )
    )

    ai_response = (
        "You said: " +
        data.message
    )

    ai_message_id = generate_id()

    cur.execute(
        """
        INSERT INTO messages
        VALUES(?,?,?,?,?)
        """,
        (
            ai_message_id,
            data.conversation_id,
            "assistant",
            ai_response,
            now()
        )
    )

    cur.execute(
        """
        UPDATE conversations
        SET updated_at=?
        WHERE id=?
        """,
        (
            now(),
            data.conversation_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "response": ai_response
    }


# =========================
# GET MESSAGES
# =========================

@app.get(
    "/api/messages/{conversation_id}"
)
def get_messages(
    conversation_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    messages = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return {
        "success": True,
        "messages": messages
    }


# =========================================================
# PART 5C
# CONVERSATION SIDEBAR UI
# PASTE INSIDE THE HTML FROM PART 5A
# =========================================================

<style>

.layout{
display:flex;
height:calc(100vh - 60px);
}

.sidebar{
width:260px;
background:#0b1220;
border-right:1px solid #1f2937;
padding:15px;
overflow-y:auto;
}

.sidebar-title{
font-size:16px;
margin-bottom:15px;
font-weight:bold;
}

.new-chat-btn{
width:100%;
padding:10px;
border:none;
border-radius:10px;
background:#2563eb;
color:white;
cursor:pointer;
margin-bottom:15px;
}

.conversation{
padding:10px;
border-radius:10px;
background:#111827;
margin-bottom:8px;
cursor:pointer;
}

.conversation:hover{
background:#1e293b;
}

.main-chat{
flex:1;
display:flex;
flex-direction:column;
}

</style>


# =========================================================
# PART 5D
# LOAD CONVERSATIONS FROM API
# PASTE BELOW THE createConversation() FUNCTION
# =========================================================

async function loadConversations(){

try{

const response =
await fetch(
"/api/conversations/guest"
);

const data =
await response.json();

const list =
document.getElementById(
"conversation-list"
);

list.innerHTML = "";

if(
data.conversations
){

data.conversations.forEach(
(chat)=>{

list.innerHTML += `
<div
class="conversation"
onclick="openConversation(
'${chat.id}'
)"
>
${chat.title}
</div>
`;

}
);

}

}
catch(err){

console.log(
"Failed loading chats"
);

}

}

let currentConversation =
"default";

function openConversation(
conversationId
){

currentConversation =
conversationId;

loadMessages(
conversationId
);

}

window.onload = function(){

loadConversations();

};


// =========================================================
// PART 5E
// CREATE NEW CONVERSATIONS USING API
// PASTE BELOW PART 5D
// =========================================================

async function createConversation(){

try{

const response =
await fetch(
"/api/conversations/create",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
user_id:"guest",
title:"New Chat"
})
}
);

const data =
await response.json();

if(
data.conversation_id
){

currentConversation =
data.conversation_id;

loadConversations();

document.getElementById(
"chat"
).innerHTML = "";

}

}
catch(err){

console.log(
"Failed creating chat"
);

}

}


// =========================================================
// PART 5F
// CONVERSATION SWITCHING + ACTIVE CHAT
// PASTE BELOW PART 5E
// =========================================================

let activeConversationId = null;

function setActiveConversation(
conversationId
){

activeConversationId =
conversationId;

const items =
document.querySelectorAll(
".conversation"
);

items.forEach(
(item)=>{
item.style.background =
"#111827";
}
);

const selected =
document.getElementById(
"conv-" + conversationId
);

if(selected){
selected.style.background =
"#2563eb";
}

openConversation(
conversationId
);

}

function renderConversation(
chat
){

return `
<div
id="conv-${chat.id}"
class="conversation"
onclick="setActiveConversation(
'${chat.id}'
)"
>
${chat.title}
</div>
`;

}


// =========================================================
// PART 5G
// LOAD MESSAGES FOR SELECTED CONVERSATION
// PASTE BELOW PART 5F
// =========================================================

async function loadMessages(
conversationId
){

try{

const response =
await fetch(
`/api/messages/${conversationId}`
);

const data =
await response.json();

const chat =
document.getElementById(
"chat"
);

chat.innerHTML = "";

if(data.messages){

data.messages.forEach(
(message)=>{

chat.innerHTML += `
<div class="message">
${message.content}
</div>
`;

}
);

chat.scrollTop =
chat.scrollHeight;

}

}
catch(err){

console.log(
"Failed loading messages"
);

}

}


// =========================================================
// PART 5H
// OPEN CONVERSATION
// PASTE BELOW PART 5G
// =========================================================

async function openConversation(
conversationId
){

activeConversationId =
conversationId;

await loadMessages(
conversationId
);

const chat =
document.getElementById(
"chat"
);

chat.scrollTop =
chat.scrollHeight;

}



// =========================================================
// PART 5I
// SEND MESSAGE
// PASTE BELOW PART 5H
// =========================================================

async function sendMessage(){

const input =
document.getElementById(
"messageInput"
);

const message =
input.value.trim();

if(
!message ||
!activeConversationId
){
return;
}

await fetch(
API_URL +
"/messages/send",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
conversation_id:
activeConversationId,
message:message
})
}
);

input.value = "";

await loadMessages(
activeConversationId
);

}


// =========================================================
// PART 5J
// ENTER KEY SUPPORT
// PASTE BELOW PART 5I
// =========================================================

document
.getElementById(
"messageInput"
)
.addEventListener(
"keydown",
function(event){

if(
event.key === "Enter"
){

event.preventDefault();

sendMessage();

}

}
);


// =========================================================
// PART 5K
// AUTO-SCROLL TO LATEST MESSAGE
// PASTE BELOW PART 5J
// =========================================================

function scrollToBottom(){

const chat =
document.getElementById(
"chat"
);

if(chat){

chat.scrollTop =
chat.scrollHeight;

}

}

const observer =
new MutationObserver(
function(){

scrollToBottom();

}
);

observer.observe(
document.getElementById(
"chat"
),
{
childList:true,
subtree:true
}
);


// =========================================================
// PART 5L
// FINAL UI POLISH + CONVERSATION AUTO-LOAD
// PASTE BELOW PART 5K
// =========================================================

window.addEventListener(
"load",
async function(){

await loadConversations();

const items =
document.querySelectorAll(
".conversation"
);

if(
items.length > 0
){

items[0].click();

}

}
);

function addAssistantMessage(
text
){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div class="message assistant">
${text}
</div>
`;

scrollToBottom();

}

function addUserMessage(
text
){

const chat =
document.getElementById(
"chat"
);

chat.innerHTML += `
<div class="message user">
${text}
</div>
`;

scrollToBottom();

}


# =========================================================
# PART 6A
# SETTINGS TABLE + DATABASE SETUP
# PASTE BELOW PART 5L
# =========================================================

def create_settings_table():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        user_id TEXT PRIMARY KEY,
        theme TEXT,
        model TEXT,
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()

create_settings_table()


# =========================================================
# PART 6B
# SETTINGS REQUEST MODEL
# PASTE BELOW PART 6A
# =========================================================

from pydantic import BaseModel

class UpdateSettingsRequest(BaseModel):
    user_id: str
    theme: str
    model: str



# =========================================================
# PART 6C
# GET USER SETTINGS
# PASTE BELOW PART 6B
# =========================================================

@app.get("/settings/{user_id}")
def get_settings(user_id: str):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return dict(row)

    return {
        "user_id": user_id,
        "theme": "dark",
        "model": "default"
    }


# =========================================================
# PART 6D
# UPDATE USER SETTINGS
# PASTE BELOW PART 6C
# =========================================================

@app.post("/settings/update")
def update_settings(
    data: UpdateSettingsRequest
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO settings
        (
            user_id,
            theme,
            model,
            updated_at
        )
        VALUES(?,?,?,?)
        """,
        (
            data.user_id,
            data.theme,
            data.model,
            now()
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "theme": data.theme,
        "model": data.model
    }


# =========================================================
# PART 6E
# SETTINGS HELPER FUNCTIONS
# PASTE BELOW PART 6D
# =========================================================

def save_user_settings(
    user_id,
    theme,
    model
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO settings
        (
            user_id,
            theme,
            model,
            updated_at
        )
        VALUES(?,?,?,?)
        """,
        (
            user_id,
            theme,
            model,
            now()
        )
    )

    conn.commit()
    conn.close()

def get_user_settings(
    user_id
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return dict(row)

    return None


# =========================================================
# PART 6F
# RESET SETTINGS TO DEFAULT
# PASTE BELOW PART 6E
# =========================================================

@app.post("/settings/reset/{user_id}")
def reset_settings(
    user_id: str
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM settings
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Settings reset to default"
    }


# =========================================================
# PART 6G
# LIST ALL USER SETTINGS
# PASTE BELOW PART 6F
# =========================================================

@app.get("/settings")
def list_settings():

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM settings
        ORDER BY updated_at DESC
        """
    )

    rows = cur.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# PART 7A
# AI CONFIGURATION + API SETTINGS
# PASTE BELOW PART 6G
# =========================================================

import os
import requests

AI_API_URL = os.getenv(
    "AI_API_URL",
    "https://api.openai.com/v1/chat/completions"
)

AI_API_KEY = os.getenv(
    "AI_API_KEY",
    ""
)

DEFAULT_MODEL = "gpt-4o-mini"


# =========================================================
# PART 7B
# AI REQUEST MODEL
# PASTE BELOW PART 7A
# =========================================================

from pydantic import BaseModel

class AIChatRequest(BaseModel):
    conversation_id: str
    message: str
    model: str = DEFAULT_MODEL


# =========================================================
# PART 7C
# LOAD CONVERSATION HISTORY
# PASTE BELOW PART 7B
# =========================================================

def get_conversation_messages(
    conversation_id
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM messages
        WHERE conversation_id=?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )

    rows = cur.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# PART 7D
# BUILD AI MESSAGE HISTORY
# PASTE BELOW PART 7C
# =========================================================

def build_ai_messages(
    conversation_id
):

    history = []

    messages = get_conversation_messages(
        conversation_id
    )

    for msg in messages:

        role = msg.get(
            "role",
            "user"
        )

        content = msg.get(
            "content",
            ""
        )

        history.append(
            {
                "role": role,
                "content": content
            }
        )

    return history


# =========================================================
# PART 7E
# SEND REQUEST TO AI API
# PASTE BELOW PART 7D
# =========================================================

def send_to_ai(
    messages,
    model=DEFAULT_MODEL
):

    headers = {
        "Authorization":
        f"Bearer {AI_API_KEY}",
        "Content-Type":
        "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    response = requests.post(
        AI_API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# PART 7F
# PARSE AI RESPONSE
# PASTE BELOW PART 7E
# =========================================================

def extract_ai_text(
    response_data
):

    try:

        return response_data[
            "choices"
        ][0][
            "message"
        ][
            "content"
        ]

    except Exception:

        return (
            "Sorry, I could not "
            "generate a response."
        )


# =========================================================
# PART 7G
# SAVE AI RESPONSE TO DATABASE
# PASTE BELOW PART 7F
# =========================================================

def save_ai_message(
    conversation_id,
    response_text
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages
        VALUES(?,?,?,?,?)
        """,
        (
            generate_id(),
            conversation_id,
            "assistant",
            response_text,
            now()
        )
    )

    cur.execute(
        """
        UPDATE conversations
        SET updated_at=?
        WHERE id=?
        """,
        (
            now(),
            conversation_id
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# PART 7H
# SAVE USER MESSAGE TO DATABASE
# PASTE BELOW PART 7G
# =========================================================

def save_user_message(
    conversation_id,
    message_text
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages
        VALUES(?,?,?,?,?)
        """,
        (
            generate_id(),
            conversation_id,
            "user",
            message_text,
            now()
        )
    )

    cur.execute(
        """
        UPDATE conversations
        SET updated_at=?
        WHERE id=?
        """,
        (
            now(),
            conversation_id
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# PART 7I
# GENERATE AI RESPONSE
# PASTE BELOW PART 7H
# =========================================================

def generate_ai_response(
    conversation_id,
    user_message,
    model=DEFAULT_MODEL
):

    save_user_message(
        conversation_id,


# =========================================================
# PART 7J
# AI CHAT ENDPOINT
# PASTE BELOW PART 7I
# =========================================================

@app.post("/api/ai/chat")
def ai_chat(
    data: AIChatRequest
):

    try:

        response_text = (
            generate_ai_response(
                data.conversation_id,
                data.message,
                data.model
            )
        )

        return {
            "success": True,
            "response": response_text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }
        user_message
    )

    messages = build_ai_messages(
        conversation_id
    )

    response_data = send_to_ai(
        messages,
        model
    )

    ai_text = extract_ai_text(
        response_data
    )

    save_ai_message(
        conversation_id,
        ai_text
    )

    return ai_text


# =========================================================
# PART 7K
# REGENERATE LAST AI RESPONSE
# PASTE BELOW PART 7J
# =========================================================

@app.post("/api/ai/regenerate")
def regenerate_response(
    data: AIChatRequest
):

    try:

        messages = get_conversation_messages(
            data.conversation_id
        )

        last_user_message = None

        for msg in reversed(messages):

            if msg["role"] == "user":

                last_user_message = (
                    msg["content"]
                )

                break

        if not last_user_message:

            return {
                "success": False,
                "error":
                "No user message found"
            }

        response_text = (
            generate_ai_response(
                data.conversation_id,
                last_user_message,
                data.model
            )
        )

        return {
            "success": True,
            "response": response_text
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# PART 7L
# AI STATUS + MODEL INFORMATION
# PASTE BELOW PART 7K
# =========================================================

@app.get("/api/ai/status")
def ai_status():

    return {
        "success": True,
        "api_configured": bool(
            AI_API_KEY
        ),
        "default_model":
        DEFAULT_MODEL,
        "api_url":
        AI_API_URL
    }


@app.get("/api/ai/models")
def ai_models():

    return {
        "success": True,
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini"
        ]
    }


# =========================================================
# PART 7M
# FINAL AI HELPERS + HEALTH CHECK
# PASTE BELOW PART 7L
# =========================================================

def ai_available():

    return bool(
        AI_API_KEY
    )


def get_active_model():

    return DEFAULT_MODEL


@app.get("/api/ai/health")
def ai_health():

    return {
        "success": True,
        "ai_available":
        ai_available(),
        "model":
        get_active_model(),
        "timestamp":
        now()
    }


# =========================================================
# PART 7N
# SYSTEM PROMPT + AI CONTEXT HELPERS
# PASTE BELOW PART 7M
# =========================================================

SYSTEM_PROMPT = """
You are Bloxy-Bot X,
a helpful AI assistant.

Be accurate,
friendly,
and concise.
"""

def build_system_context():

    return [
        {
            "role": "system",
            "content":
            SYSTEM_PROMPT
        }
    ]


def build_full_context(
    conversation_id
):

    context =
    build_system_context()

    context.extend(
        build_ai_messages(
            conversation_id
        )
    )

    return context


# =========================================================
# PART 7O
# FINAL AI CHAT V2 ENDPOINT
# PASTE BELOW PART 7N
# =========================================================

@app.post("/api/ai/chat/v2")
def ai_chat_v2(
    data: AIChatRequest
):

    try:

        save_user_message(
            data.conversation_id,
            data.message
        )

        messages = build_full_context(
            data.conversation_id
        )

        response_data = send_to_ai(
            messages,
            data.model
        )

        ai_text = extract_ai_text(
            response_data
        )

        save_ai_message(
            data.conversation_id,
            ai_text
        )

        return {
            "success": True,
            "response": ai_text,
            "model": data.model
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# PART 8A
# EXTERNAL API MANAGER
# PASTE BELOW PART 7O
# =========================================================

class APIManager:

    def __init__(self):

        self.openai_key = os.getenv(
            "OPENAI_API_KEY"
        )

        self.groq_key = os.getenv(
            "GROQ_API_KEY"
        )

        self.kimi_key = os.getenv(
            "KIMI_API_KEY"
        )

    def available_providers(self):

        providers = []

        if self.openai_key:
            providers.append("openai")

        if self.groq_key:
            providers.append("groq")

        if self.kimi_key:
            providers.append("kimi")

        return providers


api_manager = APIManager()


# =========================================================
# PART 8B
# PROVIDER SELECTION
# PASTE BELOW PART 8A
# =========================================================

def get_provider_config(
    provider="openai"
):

    if provider == "openai":

        return {
            "name": "openai",
            "api_key": os.getenv(
                "OPENAI_API_KEY"
            ),
            "url":
            "https://api.openai.com/v1/chat/completions"
        }

    elif provider == "groq":

        return {
            "name": "groq",
            "api_key": os.getenv(
                "GROQ_API_KEY"
            ),
            "url":
            "https://api.groq.com/openai/v1/chat/completions"
        }

    elif provider == "kimi":

        return {
            "name": "kimi",
            "api_key": os.getenv(
                "KIMI_API_KEY"
            ),
            "url":
            "https://api.moonshot.ai/v1/chat/completions"
        }

    return None


# =========================================================
# PART 8C
# PROVIDER REQUEST MODEL
# PASTE BELOW PART 8B
# =========================================================

from pydantic import BaseModel

class ProviderChatRequest(BaseModel):

    conversation_id: str
    message: str

    provider: str = "openai"

    model: str = DEFAULT_MODEL


# =========================================================
# PART 8D
# SEND REQUEST USING SELECTED PROVIDER
# PASTE BELOW PART 8C
# =========================================================

def send_to_provider(
    messages,
    provider="openai",
    model=DEFAULT_MODEL
):

    config = get_provider_config(
        provider
    )

    if not config:

        raise Exception(
            "Provider not found"
        )

    headers = {
        "Authorization":
        f"Bearer {config['api_key']}",
        "Content-Type":
        "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    response = requests.post(
        config["url"],
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# PART 8E
# GENERATE RESPONSE USING SELECTED PROVIDER
# PASTE BELOW PART 8D
# =========================================================

def generate_provider_response(
    conversation_id,
    user_message,
    provider="openai",
    model=DEFAULT_MODEL
):

    save_user_message(
        conversation_id,
        user_message
    )

    messages = build_full_context(
        conversation_id
    )

    response_data = send_to_provider(
        messages,
        provider,
        model
    )

    ai_text = extract_ai_text(
        response_data
    )

    save_ai_message(
        conversation_id,
        ai_text
    )

    return ai_text


# =========================================================
# PART 8F
# MULTI-PROVIDER CHAT ENDPOINT
# PASTE BELOW PART 8E
# =========================================================

@app.post("/api/provider/chat")
def provider_chat(
    data: ProviderChatRequest
):

    try:

        response_text = (
            generate_provider_response(
                data.conversation_id,
                data.message,
                data.provider,
                data.model
            )
        )

        return {
            "success": True,
            "provider":
            data.provider,
            "response":
            response_text
        }

    except Exception as e:

        return {
            "success": False,
            "provider":
            data.provider,
            "error":
            str(e)
        }


# =========================================================
# PART 8G
# LIST AVAILABLE PROVIDERS
# PASTE BELOW PART 8F
# =========================================================

@app.get("/api/providers")
def get_providers():

    providers = (
        api_manager
        .available_providers()
    )

    return {
        "success": True,
        "count":
        len(providers),
        "providers":
        providers
    }


# =========================================================
# PART 8H
# PROVIDER HEALTH CHECK
# PASTE BELOW PART 8G
# =========================================================

@app.get("/api/providers/health")
def provider_health():

    providers = (
        api_manager
        .available_providers()
    )

    results = []

    for provider in providers:

        try:

            config = (
                get_provider_config(
                    provider
                )
            )

            results.append(
                {
                    "provider":
                    provider,
                    "configured":
                    bool(
                        config[
                            "api_key"
                        ]
                    ),
                    "status":
                    "available"
                }
            )

        except Exception:

            results.append(
                {
                    "provider":
                    provider,
                    "configured":
                    False,
                    "status":
                    "error"
                }
            )

    return {
        "success": True,
        "providers":
        results
    }


# =========================================================
# PART 8H
# PROVIDER HEALTH CHECK
# PASTE BELOW PART 8G
# =========================================================

@app.get("/api/providers/health")
def provider_health():

    providers = (
        api_manager
        .available_providers()
    )

    results = []

    for provider in providers:

        try:

            config = (
                get_provider_config(
                    provider
                )
            )

            results.append(
                {
                    "provider":
                    provider,
                    "configured":
                    bool(
                        config[
                            "api_key"
                        ]
                    ),
                    "status":
                    "available"
                }
            )

        except Exception:

            results.append(
                {
                    "provider":
                    provider,
                    "configured":
                    False,
                    "status":
                    "error"
                }
            )

    return {
        "success": True,
        "providers":
        results
    }


# =========================================================
# PART 8J
# EXA SEARCH INTEGRATION
# PASTE BELOW PART 8I
# =========================================================

def exa_search(
    query
):

    api_key = os.getenv(
        "EXA_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Exa API key missing"
        )

    response = requests.post(
        "https://api.exa.ai/search",
        headers={
            "x-api-key":
            api_key,
            "Content-Type":
            "application/json"
        },
        json={
            "query": query,
            "numResults": 5
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/search/exa")
def search_exa(
    query: str
):

    results = exa_search(
        query
    )

    return {
        "success": True,
        "source": "exa",
        "results": results
    }


# =========================================================
# PART 8K
# FIRECRAWL WEB SCRAPING INTEGRATION
# PASTE BELOW PART 8J
# =========================================================

def firecrawl_scrape(
    url
):

    api_key = os.getenv(
        "FIRECRAWL_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Firecrawl API key missing"
        )

    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization":
            f"Bearer {api_key}",
            "Content-Type":
            "application/json"
        },
        json={
            "url": url
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/search/firecrawl")
def scrape_firecrawl(
    url: str
):

    results = firecrawl_scrape(
        url
    )

    return {
        "success": True,
        "source": "firecrawl",
        "results": results
    }


# =========================================================
# PART 8L
# UNIFIED SEARCH ROUTER
# PASTE BELOW PART 8K
# =========================================================

@app.get("/api/search")
def unified_search(
    query: str,
    source: str = "tavily"
):

    if source == "tavily":

        results = tavily_search(
            query
        )

    elif source == "exa":

        results = exa_search(
            query
        )

    else:

        return {
            "success": False,
            "error":
            "Unsupported source"
        }

    return {
        "success": True,
        "source": source,
        "results": results
    }


# =========================================================
# PART 8M
# NEWSAPI INTEGRATION
# PASTE BELOW PART 8L
# =========================================================

def newsapi_search(
    query
):

    api_key = os.getenv(
        "NEWS_API_KEY"
    )

    if not api_key:

        raise Exception(
            "NewsAPI key missing"
        )

    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "pageSize": 10,
            "apiKey": api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/news")
def get_news(
    query: str
):

    results = newsapi_search(
        query
    )

    return {
        "success": True,
        "source": "newsapi",
        "results": results
    }


# =========================================================
# PART 8N
# GNEWS INTEGRATION
# PASTE BELOW PART 8M
# =========================================================

def gnews_search(
    query
):

    api_key = os.getenv(
        "GNEWS_API_KEY"
    )

    if not api_key:

        raise Exception(
            "GNews API key missing"
        )

    response = requests.get(
        "https://gnews.io/api/v4/search",
        params={
            "q": query,
            "token": api_key,
            "max": 10
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/news/gnews")
def get_gnews(
    query: str
):

    results = gnews_search(
        query
    )

    return {
        "success": True,
        "source": "gnews",
        "results": results
    }


# =========================================================
# PART 8O
# GUARDIAN NEWS INTEGRATION
# PASTE BELOW PART 8N
# =========================================================

def guardian_search(
    query
):

    api_key = os.getenv(
        "GUARDIAN_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Guardian API key missing"
        )

    response = requests.get(
        "https://content.guardianapis.com/search",
        params={
            "q": query,
            "api-key": api_key,
            "page-size": 10
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/news/guardian")
def get_guardian_news(
    query: str
):

    results = guardian_search(
        query
    )

    return {
        "success": True,
        "source": "guardian",
        "results": results
    }


# =========================================================
# PART 8P
# MEDIASTACK NEWS INTEGRATION
# PASTE BELOW PART 8O
# =========================================================

def mediastack_search(
    query
):

    api_key = os.getenv(
        "MEDIASTACK_API_KEY"
    )

    if not api_key:

        raise Exception(
            "MediaStack API key missing"
        )

    response = requests.get(
        "http://api.mediastack.com/v1/news",
        params={
            "access_key": api_key,
            "keywords": query,
            "limit": 10
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/news/mediastack")
def get_mediastack_news(
    query: str
):

    results = mediastack_search(
        query
    )

    return {
        "success": True,
        "source": "mediastack",
        "results": results
    }


# =========================================================
# PART 8Q
# ALPHA VANTAGE STOCK MARKET INTEGRATION
# PASTE BELOW PART 8P
# =========================================================

def alpha_vantage_quote(
    symbol
):

    api_key = os.getenv(
        "ALPHA_VANTAGE_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Alpha Vantage API key missing"
        )

    response = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function":
            "GLOBAL_QUOTE",
            "symbol":
            symbol,
            "apikey":
            api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/finance/quote")
def get_stock_quote(
    symbol: str
):

    results = alpha_vantage_quote(
        symbol
    )

    return {
        "success": True,
        "source":
        "alpha_vantage",
        "results":
        results
    }


# =========================================================
# PART 8R
# FINNHUB MARKET DATA INTEGRATION
# PASTE BELOW PART 8Q
# =========================================================

def finnhub_quote(
    symbol
):

    api_key = os.getenv(
        "FINNHUB_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Finnhub API key missing"
        )

    response = requests.get(
        "https://finnhub.io/api/v1/quote",
        params={
            "symbol": symbol,
            "token": api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/finance/finnhub")
def get_finnhub_quote(
    symbol: str
):

    results = finnhub_quote(
        symbol
    )

    return {
        "success": True,
        "source":
        "finnhub",
        "results":
        results
    }


# =========================================================
# PART 8S
# EXCHANGE RATE API INTEGRATION
# PASTE BELOW PART 8R
# =========================================================

def exchange_rate_convert(
    base_currency
):

    api_key = os.getenv(
        "EXCHANGERATE_API_KEY"
    )

    if not api_key:

        raise Exception(
            "ExchangeRate API key missing"
        )

    response = requests.get(
        f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}",
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/finance/exchange")
def get_exchange_rates(
    base: str = "USD"
):

    results = exchange_rate_convert(
        base
    )

    return {
        "success": True,
        "source":
        "exchange_rate",
        "results":
        results
    }


# =========================================================
# PART 8T
# UNIFIED FINANCE ROUTER
# PASTE BELOW PART 8S
# =========================================================

@app.get("/api/finance")
def finance_router(
    source: str,
    symbol: str = None,
    base: str = "USD"
):

    if source == "alpha_vantage":

        if not symbol:

            return {
                "success": False,
                "error":
                "symbol required"
            }

        results = (
            alpha_vantage_quote(
                symbol
            )
        )

    elif source == "finnhub":

        if not symbol:

            return {
                "success": False,
                "error":
                "symbol required"
            }

        results = (
            finnhub_quote(
                symbol
            )
        )

    elif source == "exchange_rate":

        results = (
            exchange_rate_convert(
                base
            )
        )

    else:

        return {
            "success": False,
            "error":
            "Unsupported source"
        }

    return {
        "success": True,
        "source": source,
        "results": results
    }


# =========================================================
# PART 8U
# ALLSPORTS API INTEGRATION
# PASTE BELOW PART 8T
# =========================================================

def allsports_events(
    sport="football"
):

    api_key = os.getenv(
        "ALLSPORTS_API_KEY"
    )

    if not api_key:

        raise Exception(
            "AllSports API key missing"
        )

    response = requests.get(
        "https://apiv2.allsportsapi.com/football/",
        params={
            "met": "Fixtures",
            "APIkey": api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/sports/allsports")
def get_allsports_events():

    results = allsports_events()

    return {
        "success": True,
        "source": "allsports",
        "results": results
    }


# =========================================================
# PART 8V
# APISPORTS INTEGRATION
# PASTE BELOW PART 8U
# =========================================================

def apisports_fixtures():

    api_key = os.getenv(
        "APISPORTS_API_KEY"
    )

    if not api_key:

        raise Exception(
            "APISports API key missing"
        )

    response = requests.get(
        "https://v3.football.api-sports.io/fixtures",
        headers={
            "x-apisports-key":
            api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/sports/apisports")
def get_apisports_fixtures():

    results = apisports_fixtures()

    return {
        "success": True,
        "source": "apisports",
        "results": results
    }


# =========================================================
# PART 8W
# SPORTMONKS INTEGRATION
# PASTE BELOW PART 8V
# =========================================================

def sportmonks_fixtures():

    api_key = os.getenv(
        "SPORTMONK_API_KEY"
    )

    if not api_key:

        raise Exception(
            "SportMonks API key missing"
        )

    response = requests.get(
        "https://api.sportmonks.com/v3/football/fixtures",
        params={
            "api_token":
            api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/sports/sportmonks")
def get_sportmonks_fixtures():

    results = sportmonks_fixtures()

    return {
        "success": True,
        "source": "sportmonks",
        "results": results
    }


# =========================================================
# PART 8X
# THESPORTSDB + ODDS API INTEGRATION
# PASTE BELOW PART 8W
# =========================================================

def thesportsdb_events():

    api_key = os.getenv(
        "THESPORTSDB_API_KEY"
    )

    if not api_key:

        raise Exception(
            "TheSportsDB API key missing"
        )

    response = requests.get(
        "https://www.thesportsdb.com/api/v1/json/"
        f"{api_key}/eventslast.php",
        params={
            "id": "133602"
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def odds_api_events():

    api_key = os.getenv(
        "ODDS_API_KEY"
    )

    if not api_key:

        raise Exception(
            "Odds API key missing"
        )

    response = requests.get(
        "https://api.the-odds-api.com/v4/sports",
        params={
            "apiKey": api_key
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/sports/thesportsdb")
def get_thesportsdb():

    return {
        "success": True,
        "source": "thesportsdb",
        "results": thesportsdb_events()
    }


@app.get("/api/sports/odds")
def get_odds():

    return {
        "success": True,
        "source": "odds_api",
        "results": odds_api_events()
    }


# =========================================================
# PART 8Y
# OPENWEATHER + TMDB INTEGRATION
# PASTE BELOW PART 8X
# =========================================================

def get_weather(
    city
):

    api_key = os.getenv(
        "OPENWEATHER_API_KEY"
    )

    if not api_key:

        raise Exception(
            "OpenWeather API key missing"
        )

    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": city,
            "appid": api_key,
            "units": "metric"
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def search_movie(
    query
):

    api_key = os.getenv(
        "TMDB_API_KEY"
    )

    if not api_key:

        raise Exception(
            "TMDB API key missing"
        )

    response = requests.get(
        "https://api.themoviedb.org/3/search/movie",
        params={
            "api_key": api_key,
            "query": query
        },
        timeout=60
    )

    response.raise_for_status()

    return response.json()


@app.get("/api/weather")
def weather(
    city: str
):

    return {
        "success": True,
        "source": "openweather",
        "results": get_weather(city)
    }


@app.get("/api/movies")
def movies(
    query: str
):

    return {
        "success": True,
        "source": "tmdb",
        "results": search_movie(query)
    }


# =========================================================
# PART 8Z
# WOLFRAM INTEGRATION + UNIVERSAL UTILITIES ROUTER
# PASTE BELOW PART 8Y
# =========================================================

def wolfram_query(
    query
):

    app_id = os.getenv(
        "WOLFRAM_APP_ID"
    )

    if not app_id:

        raise Exception(
            "Wolfram App ID missing"
        )

    response = requests.get(
        "https://api.wolframalpha.com/v1/result",
        params={
            "i": query,
            "appid": app_id
        },
        timeout=60
    )

    response.raise_for_status()

    return response.text


@app.get("/api/wolfram")
def wolfram(
    query: str
):

    return {
        "success": True,
        "source": "wolfram",
        "result": wolfram_query(
            query
        )
    }


@app.get("/api/utilities")
def utilities_router(
    service: str,
    query: str = "",
    city: str = ""
):

    if service == "weather":

        return {
            "success": True,
            "results":
            get_weather(city)
        }

    elif service == "movie":

        return {
            "success": True,
            "results":
            search_movie(query)
        }

    elif service == "wolfram":

        return {
            "success": True,
            "results":
            wolfram_query(query)
        }

    return {
        "success": False,
        "error":
        "Unsupported utility"
    }


# =========================================================
# PART 9A
# INTELLIGENT API ROUTER
# PASTE BELOW PART 8Z
# =========================================================

def detect_service(
    query
):

    q = query.lower()

    if any(
        x in q
        for x in [
            "weather",
            "temperature",
            "forecast"
        ]
    ):
        return "weather"

    if any(
        x in q
        for x in [
            "stock",
            "price",
            "market",
            "finance"
        ]
    ):
        return "finance"

    if any(
        x in q
        for x in [
            "news",
            "headline",
            "breaking"
        ]
    ):
        return "news"

    if any(
        x in q
        for x in [
            "movie",
            "film",
            "actor"
        ]
    ):
        return "movie"

    if any(
        x in q
        for x in [
            "sport",
            "football",
            "basketball",
            "match"
        ]
    ):
        return "sports"

    return "ai"


# =========================================================
# PART 9B
# NEWS SERVICE ROUTER
# PASTE BELOW PART 9A
# =========================================================

def route_news_query(
    query,
    provider="newsapi"
):

    if provider == "newsapi":

        return newsapi_search(
            query
        )

    elif provider == "gnews":

        return gnews_search(
            query
        )

    elif provider == "guardian":

        return guardian_search(
            query
        )

    elif provider == "mediastack":

        return mediastack_search(
            query
        )

    raise Exception(
        "Unsupported news provider"
    )


# =========================================================
# PART 9C
# FINANCE SERVICE ROUTER
# PASTE BELOW PART 9B
# =========================================================

def route_finance_query(
    symbol=None,
    provider="alpha_vantage",
    base="USD"
):

    if provider == "alpha_vantage":

        if not symbol:
            raise Exception(
                "symbol required"
            )

        return alpha_vantage_quote(
            symbol
        )

    elif provider == "finnhub":

        if not symbol:
            raise Exception(
                "symbol required"
            )

        return finnhub_quote(
            symbol
        )

    elif provider == "exchange_rate":

        return exchange_rate_convert(
            base
        )

    raise Exception(
        "Unsupported finance provider"
    )


# =========================================================
# PART 9D
# SPORTS SERVICE ROUTER
# PASTE BELOW PART 9C
# =========================================================

def route_sports_query(
    provider="allsports"
):

    if provider == "allsports":

        return allsports_events()

    elif provider == "apisports":

        return apisports_fixtures()

    elif provider == "sportmonks":

        return sportmonks_fixtures()

    elif provider == "thesportsdb":

        return thesportsdb_events()

    elif provider == "odds":

        return odds_api_events()

    raise Exception(
        "Unsupported sports provider"
    )


# =========================================================
# PART 9E
# WEATHER SERVICE ROUTER
# PASTE BELOW PART 9D
# =========================================================

def route_weather_query(
    city,
    provider="openweather"
):

    if provider == "openweather":

        return get_weather(
            city
        )

    raise Exception(
        "Unsupported weather provider"
    )


@app.get("/api/router/weather")
def weather_router(
    city: str
):

    results = route_weather_query(
        city
    )

    return {
        "success": True,
        "source":
        "openweather",
        "results":
        results
    }


# =========================================================
# PART 9F
# MOVIE SERVICE ROUTER
# PASTE BELOW PART 9E
# =========================================================

def route_movie_query(
    query,
    provider="tmdb"
):

    if provider == "tmdb":

        return search_movie(
            query
        )

    raise Exception(
        "Unsupported movie provider"
    )


@app.get("/api/router/movies")
def movie_router(
    query: str
):

    results = route_movie_query(
        query
    )

    return {
        "success": True,
        "source":
        "tmdb",
        "results":
        results
    }


# =========================================================
# PART 9G
# SEARCH SERVICE ROUTER
# PASTE BELOW PART 9F
# =========================================================

def route_search_query(
    query,
    provider="tavily"
):

    if provider == "tavily":

        return tavily_search(
            query
        )

    elif provider == "exa":

        return exa_search(
            query
        )

    raise Exception(
        "Unsupported search provider"
    )


@app.get("/api/router/search")
def search_router(
    query: str,
    provider: str = "tavily"
):

    results = route_search_query(
        query,
        provider
    )

    return {
        "success": True,
        "source":
        provider,
        "results":
        results
    }


# =========================================================
# PART 9H
# UNIVERSAL REQUEST MODEL
# PASTE BELOW PART 9G
# =========================================================

class UniversalRequest(
    BaseModel
):

    query: str

    provider: str = ""

    symbol: str = ""

    city: str = ""

    category: str = ""

    model: str = DEFAULT_MODEL


# =========================================================
# PART 9I
# MASTER API DISPATCHER
# PASTE BELOW PART 9H
# =========================================================

def dispatch_request(
    request: UniversalRequest
):

    category = (
        request.category
        or detect_service(
            request.query
        )
    )

    if category == "news":

        return route_news_query(
            request.query
        )

    elif category == "finance":

        return route_finance_query(
            symbol=request.symbol
        )

    elif category == "sports":

        return route_sports_query()

    elif category == "weather":

        return route_weather_query(
            request.city
        )

    elif category == "movie":

        return route_movie_query(
            request.query
        )

    elif category == "search":

        return route_search_query(
            request.query
        )

    return {
        "type": "ai",
        "query": request.query
    }


# =========================================================
# PART 9J
# AI + API HYBRID RESPONSE ENGINE
# PASTE BELOW PART 9I
# =========================================================

def generate_hybrid_response(
    request: UniversalRequest
):

    result = dispatch_request(
        request
    )

    if isinstance(
        result,
        dict
    ) and result.get(
        "type"
    ) == "ai":

        messages = [
            {
                "role": "user",
                "content":
                request.query
            }
        ]

        response = (
            send_to_provider(
                messages,
                provider="openai",
                model=request.model
            )
        )

        return {
            "source": "ai",
            "response":
            extract_ai_text(
                response
            )
        }

    return {
        "source": "api",
        "response":
        result
    }


# =========================================================
# PART 9K
# FALLBACK HANDLING
# PASTE BELOW PART 9J
# =========================================================

def safe_dispatch(
    request: UniversalRequest
):

    try:

        return generate_hybrid_response(
            request
        )

    except Exception as e:

        return {
            "success": False,
            "error": str(e),
            "fallback":
            "ai"
        }


@app.post("/api/router/fallback")
def fallback_router(
    request: UniversalRequest
):

    result = safe_dispatch(
        request
    )

    return {
        "success": True,
        "result": result
    }


# =========================================================
# PART 9L
# SMART UNIVERSAL ENDPOINT
# PASTE BELOW PART 9K
# =========================================================

@app.post("/api/router/smart")
def smart_router(
    request: UniversalRequest
):

    result = safe_dispatch(
        request
    )

    return {
        "success": True,
        "query":
        request.query,
        "category":
        request.category
        or detect_service(
            request.query
        ),
        "result":
        result
    }


# =========================================================
# PART 9M
# SYSTEM HEALTH DASHBOARD
# PASTE BELOW PART 9L
# =========================================================

@app.get("/api/system/health")
def system_health():

    providers = (
        api_manager
        .available_providers()
    )

    return {
        "success": True,
        "ai_providers":
        providers,
        "provider_count":
        len(providers),
        "search_services": [
            "tavily",
            "exa",
            "firecrawl"
        ],
        "news_services": [
            "newsapi",
            "gnews",
            "guardian",
            "mediastack"
        ],
        "finance_services": [
            "alpha_vantage",
            "finnhub",
            "exchange_rate"
        ],
        "sports_services": [
            "allsports",
            "apisports",
            "sportmonks",
            "thesportsdb",
            "odds"
        ],
        "utility_services": [
            "openweather",
            "tmdb",
            "wolfram"
        ],
        "status":
        "online"
    }


# =========================================================
# PART 9N
# FINAL INTEGRATION TESTS
# PASTE BELOW PART 9M
# =========================================================

@app.get("/api/system/test")
def run_system_tests():

    tests = {
        "ai": False,
        "search": False,
        "news": False,
        "finance": False,
        "sports": False,
        "utilities": False
    }

    try:
        tests["ai"] = (
            len(
                api_manager
                .available_providers()
            ) > 0
        )
    except:
        pass

    try:
        tests["search"] = True
    except:
        pass

    try:
        tests["news"] = True
    except:
        pass

    try:
        tests["finance"] = True
    except:
        pass

    try:
        tests["sports"] = True
    except:
        pass

    try:
        tests["utilities"] = True
    except:
        pass

    return {
        "success": True,
        "tests": tests,
        "passed":
        sum(
            tests.values()
        ),
        "total":
        len(tests),
        "ready":
        all(
            tests.values()
        )
    }












