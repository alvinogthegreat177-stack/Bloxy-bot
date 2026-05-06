from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os
import uuid

app = FastAPI()

# =====================
# CONFIG
# =====================
GROQ = os.getenv("GROQ_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "1234"

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
# SIGNUP
# =====================
@app.post("/signup")
def signup(data: Auth):

    if data.email in users:
        return {"error": "User already exists"}

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0]
    }

    return {"ok": True}

# =====================
# LOGIN
# =====================
@app.post("/login")
def login(data: Auth):

    if data.email not in users:
        return {"error": "User not found"}

    if users[data.email]["password"] != data.password:
        return {"error": "Wrong password"}

    session_id = str(uuid.uuid4())

    sessions[session_id] = data.email

    verified = (data.email == OWNER_EMAIL)

    return {
        "session_id": session_id,
        "username": "aTg" if verified else users[data.email]["username"],
        "verified": verified
    }

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
- Respond in a formal, diplomatic, and professional tone
- Be clear and structured
- Always format lists vertically like:

1. Item one
2. Item two
3. Item three

- Never use inline lists
- Never include usernames or labels like "AI:" or "user:"
- Avoid repetition or messy formatting
- Use emojis only when naturally appropriate
"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt}
                ] + history + [
                    {"role": "user", "content": data.message}
                ]
            }
        )

        res = r.json()

        if "choices" not in res:
            reply = "AI error occurred."
        else:
            reply = res["choices"][0]["message"]["content"]

    except Exception as e:
        reply = "Server error."

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
  width:280px;
  background:#111;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  padding:10px;
}

.title {
  font-weight:bold;
}

.chat-item {
  padding:8px;
  margin:5px;
  background:#1a1a1a;
  border-radius:6px;
  cursor:pointer;
}

.chat-item:hover {
  background:#222;
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
  background:#222;
  margin:10px 0;
  padding:10px;
  border-radius:8px;
}

input {
  width:100%;
  padding:12px;
  border:none;
  outline:none;
  background:#111;
  color:white;
}

/* FOOTER */
.footer {
  font-size:11px;
  color:#777;
  text-align:center;
  padding:5px;
}
</style>

</head>

<body>

<div class="container">

<!-- SIDEBAR -->
<div class="sidebar">

  <div>
    <div class="title">Bloxy-bot</div>
    <div id="chatList"></div>
    <button onclick="newChat()">+ New Chat</button>
  </div>

  <div>
    <div id="user">Guest</div>
  </div>

</div>

<!-- MAIN -->
<div class="main">

  <div id="messages" class="messages"></div>

  <input id="input" placeholder="Message..." onkeydown="if(event.key==='Enter'){send()}">

  <div class="footer">
    Bloxy-bot can make mistakes. Double check just incase
  </div>

</div>

</div>

<script>

let chats = {"main": []};
let current = "main";

function newChat(){
  let id = "chat_" + Date.now();
  chats[id] = [];
  current = id;
  renderChats();
  renderMessages();
}

function renderChats(){
  let box = document.getElementById("chatList");
  box.innerHTML = "";

  for(let c in chats){
    let div = document.createElement("div");
    div.className="chat-item";
    div.innerText=c;
    div.onclick=()=>{current=c; renderMessages();};
    box.appendChild(div);
  }
}

function renderMessages(){
  let box = document.getElementById("messages");
  box.innerHTML="";

  for(let m of chats[current]){
    let div=document.createElement("div");
    div.className="msg";
    div.innerHTML="<b>"+m.role+":</b> "+m.content;
    box.appendChild(div);
  }
}

function send(){

  let input=document.getElementById("input");
  let msg=input.value;
  input.value="";

  chats[current].push({role:"user",content:msg});
  renderMessages();

  fetch("/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      chat_id:current,
      message:msg,
      session_id:"none"
    })
  })
  .then(r=>r.json())
  .then(d=>{
    chats[current].push({role:"assistant",content:d.reply});
    renderMessages();
  });

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
