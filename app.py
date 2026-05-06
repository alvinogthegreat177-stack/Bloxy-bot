from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os
import uuid

app = FastAPI()

# =====================
# API KEYS
# =====================
GROQ = os.getenv("GROQ_API_KEY")
TAVILY = os.getenv("TAVILY_API_KEY")
NEWS = os.getenv("NEWS_API_KEY")
WOLFRAM = os.getenv("WOLFRAM_APP_ID")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvinthegreatdev17.og"

# =====================
# MEMORY STORE
# =====================
chats = {}  # chat_id -> messages
titles = {}  # chat_id -> title

# =====================
# MODELS
# =====================
class Login(BaseModel):
    email: str
    password: str

class Chat(BaseModel):
    email: str
    message: str
    chat_id: str

# =====================
# LOGIN
# =====================
@app.post("/login")
def login(data: Login):
    verified = (data.email == OWNER_EMAIL and data.password == OWNER_PASSWORD)

    return {
        "username": "aTg" if verified else data.email.split("@")[0],
        "verified": verified
    }

# =====================
# TOOLS ENGINE
# =====================
def tools(query):
    out = []

    try:
        w = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        ).json().get("extract")
        if w:
            out.append("Wikipedia: " + w)
    except:
        pass

    try:
        n = requests.get(
            f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS}"
        ).json().get("articles", [])[:2]
        out.append("News: " + str([a["title"] for a in n]))
    except:
        pass

    try:
        t = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY, "query": query}
        ).json().get("results", [])[:2]
        out.append("Search: " + str(t))
    except:
        pass

    try:
        w = requests.get(
            f"http://api.wolframalpha.com/v1/result?i={query}&appid={WOLFRAM}"
        ).text
        out.append("Math: " + w)
    except:
        pass

    return "\n".join(out)

# =====================
# CHAT
# =====================
@app.post("/chat")
def chat(data: Chat):

    if data.chat_id not in chats:
        chats[data.chat_id] = []

    history = chats[data.chat_id]

    tool_data = tools(data.message)

    messages = history + [
        {
            "role": "user",
            "content": data.message + "\n\nTOOLS:\n" + tool_data
        }
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
                "messages": messages
            }
        )

        res = r.json()

        if "choices" not in res:
            reply = str(res)
        else:
            reply = res["choices"][0]["message"]["content"]

    except Exception as e:
        reply = str(e)

    chats[data.chat_id].append({"role": "user", "content": data.message})
    chats[data.chat_id].append({"role": "assistant", "content": reply})

    # auto-title
    if data.chat_id not in titles:
        titles[data.chat_id] = data.message[:25]

    return {"reply": reply}

# =====================
# FRONTEND (CHATGPT STYLE UI)
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
  background:#0d0d0d;
  color:white;
}

/* LAYOUT */
.container {
  display:flex;
  height:100vh;
}

/* SIDEBAR */
.sidebar {
  width:280px;
  background:#111;
  padding:10px;
  overflow-y:auto;
}

.chat-item {
  padding:10px;
  margin:5px;
  background:#1a1a1a;
  border-radius:8px;
  cursor:pointer;
}

.chat-item:hover {
  background:#222;
}

/* MAIN CHAT */
.main {
  flex:1;
  display:flex;
  flex-direction:column;
}

/* MESSAGES */
.messages {
  flex:1;
  padding:20px;
  overflow-y:auto;
}

.msg {
  margin:10px 0;
  padding:10px;
  border-radius:10px;
  background:#1f1f1f;
}

/* INPUT */
.input-area {
  display:flex;
  padding:10px;
  background:#111;
}

input {
  flex:1;
  padding:12px;
  border:none;
  border-radius:8px;
  outline:none;
}

/* VERIFIED */
.verified {
  width:14px;
  height:14px;
  margin-left:6px;
}

.verified circle {
  fill:#ff8c00;
}

.verified path {
  fill:none;
  stroke:white;
  stroke-width:2;
}
</style>
</head>

<body>

<div class="container">

<div class="sidebar">
  <button onclick="newChat()">+ New Chat</button>
  <div id="chatList"></div>
</div>

<div class="main">

  <div id="messages" class="messages"></div>

  <div class="input-area">
    <input id="input" placeholder="Message..." onkeydown="if(event.key==='Enter'){send()}">
  </div>

</div>

</div>

<script>

let currentChat = "main";
let chats = {"main":[]};

function newChat(){
  let id = "chat_" + Date.now();
  chats[id] = [];
  currentChat = id;
  renderChats();
}

function renderChats(){
  let box = document.getElementById("chatList");
  box.innerHTML = "";

  for(let c in chats){
    let div = document.createElement("div");
    div.className = "chat-item";
    div.innerText = c;
    div.onclick = ()=>{currentChat=c; renderMessages();};
    box.appendChild(div);
  }
}

function renderMessages(){
  let box = document.getElementById("messages");
  box.innerHTML = "";

  for(let m of chats[currentChat]){
    let div = document.createElement("div");
    div.className = "msg";
    div.innerHTML = "<b>"+m.role+":</b> "+m.content;
    box.appendChild(div);
  }
}

function send(){

  let input = document.getElementById("input");
  let msg = input.value;
  input.value = "";

  add("user", msg);

  fetch("/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      email:"test",
      message:msg,
      chat_id:currentChat
    })
  })
  .then(r=>r.json())
  .then(d=>{
    add("AI", d.reply);
  });
}

function add(role,text){
  chats[currentChat].push({role,text});
  renderMessages();
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
