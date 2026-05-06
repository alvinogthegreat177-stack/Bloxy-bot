\from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import uuid
import os

app = FastAPI()

# =====================
# ENV KEYS
# =====================
GROQ = os.getenv("GROQ_API_KEY")
NEWS = os.getenv("NEWS_API_KEY")
TAVILY = os.getenv("TAVILY_API_KEY")
WOLFRAM = os.getenv("WOLFRAM_APP_ID")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"

# =====================
# STORAGE
# =====================
users = {}
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
# AUTH
# =====================
@app.post("/signup")
def signup(data: Auth):
    if data.email in users:
        return {"error": "User exists"}

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0]
    }
    return {"ok": True}

@app.post("/login")
def login(data: Auth):
    if data.email not in users:
        return {"error": "No user"}

    if users[data.email]["password"] != data.password:
        return {"error": "Wrong password"}

    sid = str(uuid.uuid4())
    sessions[sid] = data.email

    verified = data.email == OWNER_EMAIL

    return {
        "session_id": sid,
        "username": "aTg" if verified else users[data.email]["username"],
        "verified": verified
    }

# =====================
# TOOLS (SAFE OPTIONAL USE)
# =====================
def wiki(q):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
        ).json()
        return r.get("extract")
    except:
        return None

def news(q):
    try:
        r = requests.get(
            f"https://newsapi.org/v2/everything?q={q}&apiKey={NEWS}"
        ).json()
        return str([a["title"] for a in r.get("articles", [])[:2]])
    except:
        return None

# =====================
# SAFE GROQ CALL
# =====================
def call_ai(messages):

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
            timeout=20
        )

        res = r.json()

        if isinstance(res, dict):
            choices = res.get("choices")
            if choices:
                return choices[0].get("message", {}).get("content")

        return None

    except:
        return None

# =====================
# CHAT ENGINE
# =====================
@app.post("/chat")
def chat(data: Chat):

    if data.chat_id not in chats:
        chats[data.chat_id] = []

    history = chats[data.chat_id]

    # optional tools (NOT blocking AI)
    tool_context = ""

    w = wiki(data.message)
    n = news(data.message)

    if w:
        tool_context += f"Wikipedia: {w}\n"
    if n:
        tool_context += f"News: {n}\n"

    system_prompt = """
You are Bloxy-bot AI.

Rules:
- Formal and diplomatic tone
- Always format lists vertically
- Never use labels like AI: or user:
- Be structured and clear
"""

    messages = [
        {"role": "system", "content": system_prompt + "\n\nTOOLS:\n" + tool_context}
    ] + history + [
        {"role": "user", "content": data.message}
    ]

    reply = call_ai(messages)

    if not reply:
        reply = "I am currently unable to respond. Please try again."

    chats[data.chat_id].append({"role": "user", "content": data.message})
    chats[data.chat_id].append({"role": "assistant", "content": reply})

    return {"reply": reply}

# =====================
# FRONTEND (CHATGPT STYLE + SIDEBAR + VERIFIED BADGE)
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
  animation:fade .15s ease;
}

@keyframes fade {
  from {opacity:0; transform:translateY(6px);}
  to {opacity:1; transform:translateY(0);}
}

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

/* VERIFIED BADGE */
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
  <div>
    <b>Bloxy-bot</b>
    <div id="chats"></div>
    <button onclick="newChat()">+ New Chat</button>
  </div>

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
let current="main";
let chats={"main":[]};

function signup(){
 fetch("/signup",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({email:email.value,password:password.value})});
}

function login(){
 fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({email:email.value,password:password.value})})
 .then(r=>r.json())
 .then(d=>{
   session=d.session_id;
   document.getElementById("login").style.display="none";

   document.getElementById("user").innerHTML =
     d.username + (d.verified ? `
<svg class="badge" viewBox="0 0 24 24">
<circle cx="12" cy="12" r="10" fill="#ff8c00"></circle>
<path d="M7 12l3 3 7-7" stroke="white" stroke-width="2" fill="none"/>
</svg>` : "");
 });
}

function newChat(){
 let id="chat_"+Date.now();
 chats[id]=[];
 current=id;
 renderChats();
 render();
}

function renderChats(){
 let box=document.getElementById("chats");
 box.innerHTML="";
 for(let c in chats){
   let d=document.createElement("div");
   d.className="chat";
   d.innerText=c;
   d.onclick=()=>{current=c; render();};
   box.appendChild(d);
 }
}

function send(){
 let msg=input.value;
 input.value="";

 chats[current].push({role:"user",content:msg});
 render();

 fetch("/chat",{
   method:"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify({session_id:session,chat_id:current,message:msg})
 })
 .then(r=>r.json())
 .then(d=>{
   chats[current].push({role:"assistant",content:d.reply});
   render();
 });
}

function render(){
 let box=document.getElementById("messages");
 box.innerHTML="";
 for(let m of chats[current]){
   let d=document.createElement("div");
   d.className="msg";
   d.innerHTML="<b>"+m.role+":</b> "+m.content;
   box.appendChild(d);
 }
 box.scrollTop=box.scrollHeight;
}

renderChats();

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
