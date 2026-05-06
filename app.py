from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import uuid
import os
import json

app = FastAPI()

# =====================
# CONFIG
# =====================
GROQ = os.getenv("GROQ_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

DB_FILE = "users.json"

# =====================
# PERSISTENT STORAGE
# =====================
def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users():
    with open(DB_FILE, "w") as f:
        json.dump(users, f)

users = load_users()
sessions = {}
chats = {}

# =====================
# MODELS
# =====================
class Auth(BaseModel):
    email: str
    password: str

class Chat(BaseModel):
    session_id: str
    chat_id: str
    message: str

# =====================
# SIGNUP
# =====================
@app.post("/signup")
def signup(data: Auth):

    if data.email in users:
        return {"ok": False, "error": "User already exists"}

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0]
    }

    save_users()
    return {"ok": True}

# =====================
# LOGIN
# =====================
@app.post("/login")
def login(data: Auth):

    # aTg special account
    if data.email == OWNER_EMAIL:
        if data.password != OWNER_PASSWORD:
            return {"ok": False, "error": "Wrong password"}

        sid = str(uuid.uuid4())
        sessions[sid] = data.email

        return {
            "ok": True,
            "session_id": sid,
            "username": "aTg",
            "verified": True
        }

    # normal users
    if data.email not in users:
        return {"ok": False, "error": "User not found"}

    if users[data.email]["password"] != data.password:
        return {"ok": False, "error": "Wrong password"}

    sid = str(uuid.uuid4())
    sessions[sid] = data.email

    return {
        "ok": True,
        "session_id": sid,
        "username": users[data.email]["username"],
        "verified": False
    }

# =====================
# AI (STABLE)
# =====================
def ask_ai(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": messages
            },
            timeout=30
        )

        data = r.json()

        if isinstance(data, dict) and "choices" in data:
            return data["choices"][0]["message"]["content"]

        return "AI error: invalid response."

    except:
        return "AI error: service unavailable."

# =====================
# CHAT
# =====================
@app.post("/chat")
def chat(data: Chat):

    if data.chat_id not in chats:
        chats[data.chat_id] = []

    history = chats[data.chat_id]

    system_prompt = """
You are Bloxy-bot AI.

Rules:
- Be formal
- Always format lists vertically
- No labels like AI:
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": data.message})

    reply = ask_ai(messages)

    chats[data.chat_id].append({"role": "user", "content": data.message})
    chats[data.chat_id].append({"role": "assistant", "content": reply})

    return {"reply": reply}

# =====================
# FRONTEND
# =====================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

<style>
body {
    margin:0;
    font-family:Arial;
    background:#0f0f0f;
    color:white;
}

.container {
    display:flex;
    height:100vh;
}

/* SIDEBAR */
.sidebar {
    width:260px;
    background:#111;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    padding:10px;
}

.chat {
    padding:8px;
    margin:5px;
    background:#1a1a1a;
    border-radius:6px;
    cursor:pointer;
}

/* MAIN */
.main {
    flex:1;
    display:flex;
    flex-direction:column;
}

.messages {
    flex:1;
    padding:20px;
    overflow:auto;
}

.msg {
    margin:8px 0;
    padding:10px;
    background:#222;
    border-radius:8px;
}

/* INPUT */
.input {
    padding:10px;
    background:#111;
}

input {
    width:100%;
    padding:12px;
    background:#222;
    border:none;
    color:white;
    outline:none;
}

/* LOGIN */
#login {
    position:fixed;
    top:0;left:0;right:0;bottom:0;
    background:#000000cc;
    display:flex;
    align-items:center;
    justify-content:center;
}

.box {
    background:#1a1a1a;
    padding:20px;
    width:300px;
}

/* SPIKY VERIFIED BADGE */
.badge {
    width:14px;
    height:14px;
    margin-left:6px;
    vertical-align:middle;
}
</style>

</head>

<body>

<div id="login">
    <div class="box">
        <h3>Login / Signup</h3>
        <input id="email" placeholder="email">
        <input id="password" placeholder="password">
        <button onclick="signup()">Signup</button>
        <button onclick="login()">Login</button>
    </div>
</div>

<div class="container">

<div class="sidebar">
    <div><b>Bloxy-bot</b></div>
    <div id="user">Guest</div>
</div>

<div class="main">

    <div id="messages" class="messages"></div>

    <div class="input">
        <input id="input" placeholder="Message..." onkeydown="if(event.key==='Enter'){send()}">
    </div>

</div>

</div>

<script>

let session="none";
let chat_id="main";
let chats={"main":[]};

function signup(){
    fetch("/signup",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:email.value,password:password.value})
    });
}

function login(){
    fetch("/login",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:email.value,password:password.value})
    })
    .then(r=>r.json())
    .then(d=>{

        if(!d.ok){
            alert(d.error);
            return;
        }

        session=d.session_id;
        document.getElementById("login").style.display="none";

        let badge = d.verified ? `
<svg class="badge" viewBox="0 0 24 24">
<path fill="#ff8c00" d="M12 2 L15 8 L22 9 L17 13 L18 20 L12 16 L6 20 L7 13 L2 9 L9 8 Z"/>
<path d="M9 12l2 2 4-5" stroke="white" stroke-width="2" fill="none"/>
</svg>` : "";

        document.getElementById("user").innerHTML =
            d.username + badge;
    });
}

function send(){

    let msg=input.value;
    input.value="";

    chats[chat_id].push({role:"user",content:msg});
    render();

    fetch("/chat",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({session_id:session,chat_id:chat_id,message:msg})
    })
    .then(r=>r.json())
    .then(d=>{
        chats[chat_id].push({role:"assistant",content:d.reply});
        render();
    });
}

function render(){
    let box=document.getElementById("messages");
    box.innerHTML="";
    for(let m of chats[chat_id]){
        let d=document.createElement("div");
        d.className="msg";
        d.innerHTML="<b>"+m.role+":</b> "+m.content;
        box.appendChild(d);
    }
    box.scrollTop=box.scrollHeight;
}

render();

</script>

</body>
</html>
"""

# =====================
# RUN
# =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
