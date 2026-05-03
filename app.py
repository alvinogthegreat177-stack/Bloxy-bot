import os
import redis
import uuid
import requests

from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO

# ================================
# APP SETUP
# ================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bloxy_secret")

# ================================
# REDIS (SCALE + MEMORY)
# ================================
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

# ================================
# SOCKET.IO (NO EVENTLET)
# ================================
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ================================
# GROQ AI
# ================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot. Be structured, clear, and concise with vertical formatting."
}

def ai(messages):
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return res.json()["choices"][0]["message"]["content"]

# ================================
# MEMORY (REDIS)
# ================================
def save(chat, role, msg):
    r.lpush(f"chat:{chat}", f"{role}:{msg}")
    r.ltrim(f"chat:{chat}", 0, 30)

def memory(chat):
    data = r.lrange(f"chat:{chat}", 0, -1)
    out = []
    for m in reversed(data):
        role, content = m.split(":", 1)
        out.append({"role": role, "content": content})
    return out

# ================================
# AI ENGINE
# ================================
def engine(chat, msg):
    messages = [SYSTEM]
    messages += memory(chat)
    messages.append({"role": "user", "content": msg})
    return ai(messages)

# ================================
# SOCKET STREAMING
# ================================
@socketio.on("send")
def handle(data):
    chat = data["chat"]
    msg = data["msg"]

    reply = engine(chat, msg)

    save(chat, "user", msg)

    buffer = ""

    for word in reply.split():
        buffer += word + " "
        socketio.emit("stream", {"data": buffer})
        socketio.sleep(0.02)

    save(chat, "assistant", reply)

# ================================
# ROUTES
# ================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<style>
body{margin:0;font-family:sans-serif;background:#0d0d0d;color:white;display:flex;height:100vh}
#sidebar{width:260px;background:#111;overflow:auto;resize:horizontal}
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;padding:20px;overflow:auto}
.msg{padding:10px;margin:6px;border-radius:10px;max-width:70%}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;background:#2563eb;color:white;border:none;padding:10px}
</style>
</head>

<body>

<div id="sidebar">
<button onclick="newChat()">+ New Chat</button>
<div id="list"></div>
</div>

<div id="main">
<div id="chat"></div>
<div id="input">
<input id="msg">
<button onclick="send()">Send</button>
</div>
</div>

<script>
const socket = io();
let current = null;
let aiMsg = null;

function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
return d;
}

socket.on("stream",d=>{
if(aiMsg) aiMsg.textContent=d.data;
});

function send(){
let m=msg.value;
if(!m)return;
msg.value="";

add("user",m);
aiMsg=add("ai","Thinking... 🤖");

socket.emit("send",{msg:m,chat:current});
}

async function newChat(){
let r=await fetch("/new_chat",{method:"POST"});
let d=await r.json();
current=d.chat;
chat.innerHTML="";
}
</script>

</body>
</html>
""")

@app.route("/new_chat", methods=["POST"])
def new_chat():
    return jsonify({"chat": str(uuid.uuid4())})

# ================================
# PRODUCTION ENTRY (IMPORTANT)
# ================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
