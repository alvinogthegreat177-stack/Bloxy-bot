import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO, emit
from flask_session import Session
import redis, sqlite3, requests, uuid, os

# ================================
# APP
# ================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "bloxy_secret"

# Redis sessions (multi-user SaaS)
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_REDIS"] = redis.Redis(host="localhost", port=6379)

Session(app)

socketio = SocketIO(app, cors_allowed_origins="*", message_queue="redis://")

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ================================
# DATABASE
# ================================
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS messages (user TEXT, chat TEXT, role TEXT, content TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT, user TEXT, title TEXT)")
conn.commit()

# ================================
# AI (GROQ)
# ================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot. Use structured, clean, vertical responses."
}

def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# ================================
# MEMORY SYSTEM
# ================================
def save(user, chat, role, content):
    cur.execute("INSERT INTO messages VALUES (?,?,?,?)", (user, chat, role, content))
    conn.commit()

    r.lpush(f"chat:{chat}", f"{role}:{content}")
    r.ltrim(f"chat:{chat}", 0, 25)

def memory(chat):
    data = r.lrange(f"chat:{chat}", 0, -1)
    out = []
    for m in reversed(data):
        role, content = m.split(":", 1)
        out.append({"role": role, "content": content})
    return out

def smart(chat, msg):
    msgs = [SYSTEM]
    msgs += memory(chat)
    msgs.append({"role": "user", "content": msg})
    return groq(msgs)

# ================================
# SOCKET STREAMING
# ================================
@socketio.on("send")
def handle(data):
    chat = data["chat"]
    msg = data["msg"]
    user = session.get("user_id")

    reply = smart(chat, msg)

    save(user, chat, "user", msg)

    buffer = ""
    for word in reply.split():
        buffer += word + " "
        emit("stream", {"data": buffer})
        socketio.sleep(0.02)

    save(user, chat, "assistant", reply)

# ================================
# CHAT API
# ================================
@app.route("/new_chat", methods=["POST"])
def new_chat():
    cid = str(uuid.uuid4())
    user = session.get("user_id")

    cur.execute("INSERT INTO chats VALUES (?,?,?)", (cid, user, "New Chat"))
    conn.commit()

    return jsonify({"id": cid})

@app.route("/chats")
def chats():
    user = session.get("user_id")
    cur.execute("SELECT * FROM chats WHERE user=?", (user,))
    return jsonify(cur.fetchall())

# ================================
# SIMPLE LOGIN (AUTO USER)
# ================================
@app.route("/login")
def login():
    session["user_id"] = str(uuid.uuid4())
    return jsonify({"ok": True})

# ================================
# UI (CHATGPT STYLE)
# ================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{
margin:0;
display:flex;
height:100vh;
font-family:sans-serif;
background:#0d0d0d;
color:white;
}

/* SIDEBAR */
#sidebar{
width:260px;
background:#111;
display:flex;
flex-direction:column;
resize:horizontal;
overflow:auto;
}

.chat{
padding:10px;
border-bottom:1px solid #222;
cursor:pointer;
}
.chat:hover{background:#222}

.title{
padding:10px;
font-weight:bold;
}

/* MAIN */
#main{
flex:1;
display:flex;
flex-direction:column;
}

#chat{
flex:1;
padding:20px;
overflow:auto;
}

.msg{
padding:10px;
margin:6px;
border-radius:10px;
max-width:70%;
white-space:pre-wrap;
animation:fade 0.2s ease;
}

@keyframes fade{
from{opacity:0;transform:translateY(5px)}
to{opacity:1;transform:translateY(0)}
}

.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

/* INPUT */
#input{
display:flex;
padding:10px;
background:#111;
}

input{
flex:1;
padding:10px;
background:#222;
border:none;
color:white;
outline:none;
}

button{
margin-left:10px;
padding:10px;
background:#2563eb;
border:none;
color:white;
cursor:pointer;
}

/* FADED TEXT */
.faded{
position:absolute;
bottom:70px;
left:50%;
transform:translateX(-50%);
color:#666;
font-size:12px;
}
</style>
</head>

<body>

<div id="sidebar">
<div class="title">💬 Bloxy-bot</div>
<button onclick="newChat()">+ New Chat</button>
<div id="list"></div>
</div>

<div id="main">
<div id="chat"></div>

<div class="faded">Bloxy-bot can make mistakes. Double check important info.</div>

<div id="input">
<input id="msg" placeholder="Message Bloxy-bot...">
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
current=d.id;
chat.innerHTML="";
load();
}

async function load(){
let r=await fetch("/chats");
let data=await r.json();

list.innerHTML="";
data.forEach(c=>{
let d=document.createElement("div");
d.className="chat";
d.textContent=c[2];
d.onclick=()=>{
current=c[0];
chat.innerHTML="";
};
list.appendChild(d);
});
}

document.getElementById("msg").addEventListener("keypress",e=>{
if(e.key==="Enter") send();
});

load();
</script>

</body>
</html>
""")

# ================================
# RUN (NO app.run)
# ================================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
