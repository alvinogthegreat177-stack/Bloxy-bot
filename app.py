from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# ======================
# 🔑 CONFIG
# ======================
GROQ = os.getenv("GROQ_API_KEY")
OWNER_EMAIL = "alvinogthegreat177@gmail.com"

# simple in-memory chat storage
memory = {}

# ======================
# MODELS
# ======================
class Login(BaseModel):
    email: str

class Chat(BaseModel):
    email: str
    message: str
    chat_id: str

# ======================
# LOGIN SYSTEM
# ======================
@app.post("/login")
def login(data: Login):
    return {
        "username": "aTg" if data.email == OWNER_EMAIL else "Guest",
        "verified": data.email == OWNER_EMAIL
    }

# ======================
# CHAT SYSTEM
# ======================
@app.post("/chat")
def chat(data: Chat):

    history = memory.get(data.chat_id, [])

    messages = history + [
        {"role": "user", "content": data.message}
    ]

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": messages[-10:]
            }
        )

        reply = r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"Error: {str(e)}"

    memory.setdefault(data.chat_id, []).append({"role": "user", "content": data.message})
    memory.setdefault(data.chat_id, []).append({"role": "assistant", "content": reply})

    return {"reply": reply}

# ======================
# FRONTEND (CHAT UI)
# ======================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>aTg AI</title>

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
  width:240px;
  background:#171717;
  padding:15px;
  position:relative;
}

.user {
  margin-top:10px;
  font-size:15px;
}

/* 🔶 ORANGE VERIFIED BADGE */
.verified {
  width:16px;
  height:16px;
  margin-left:6px;
  vertical-align:middle;
}

.verified path {
  fill:#ff8c00; /* ORANGE */
}

/* LOGIN BOX */
.login {
  position:absolute;
  bottom:20px;
  left:15px;
  right:15px;
}

.login input {
  width:100%;
  padding:8px;
  border:none;
  border-radius:8px;
}

/* CHAT AREA */
.chat {
  flex:1;
  display:flex;
  flex-direction:column;
}

.messages {
  flex:1;
  overflow-y:auto;
  padding:20px;
}

.msg {
  background:#222;
  padding:10px;
  margin:10px 0;
  border-radius:10px;
}

input.chatbox {
  width:100%;
  padding:12px;
  border:none;
  outline:none;
}
</style>

</head>

<body>

<div class="container">

  <!-- SIDEBAR -->
  <div class="sidebar">

    <h3>aTg AI</h3>

    <div id="user" class="user">Guest</div>

    <div class="login">
      <input id="email" placeholder="Enter email..."
      onkeydown="if(event.key==='Enter'){login()}">
    </div>

  </div>

  <!-- CHAT -->
  <div class="chat">

    <div class="messages" id="messages"></div>

    <input class="chatbox" id="input"
      placeholder="Message..."
      onkeydown="if(event.key==='Enter'){send()}">

  </div>

</div>

<script>

let email = "";
let user = "Guest";
let verified = false;

function login(){
  email = document.getElementById("email").value;

  fetch("/login",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({email})
  })
  .then(r=>r.json())
  .then(d=>{
    user = d.username;
    verified = d.verified;

    renderUser();
  });
}

function renderUser(){
  document.getElementById("user").innerHTML =
    user +
    (verified
      ? `<svg class="verified" viewBox="0 0 24 24">
           <path d="M9 12l2 2 4-4"></path>
         </svg>`
      : "");
}

function send(){
  const input = document.getElementById("input");
  const msg = input.value;
  input.value = "";

  add(user, msg, true);

  fetch("/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      email,
      message:msg,
      chat_id:"main"
    })
  })
  .then(r=>r.json())
  .then(d=>{
    add("AI", d.reply, false);
  });
}

function add(name,text,isUser){
  const div = document.createElement("div");
  div.className="msg";
  div.innerHTML = "<b>" + name + ":</b> " + text;
  document.getElementById("messages").appendChild(div);
}

</script>

</body>
</html>
"""

# ======================
# RUN
# ======================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
