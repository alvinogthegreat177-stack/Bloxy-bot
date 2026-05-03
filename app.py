import os
import uuid
import redis
import requests

from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO

# =====================================================
# APP SETUP (NO EVENTLET)
# =====================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bloxy_secret")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# =====================================================
# REDIS (MEMORY + INDEXING)
# =====================================================
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

# =====================================================
# USERS SYSTEM
# =====================================================
USERS = {
    "admin": {"password": "123", "verified": True}
}

# =====================================================
# API KEYS
# =====================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# =====================================================
# AI ENGINE (GROQ)
# =====================================================
def groq(messages):
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return res.json()["choices"][0]["message"]["content"]

SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot. Be clear, structured, and helpful."
}

# =====================================================
# SOURCES
# =====================================================
def tavily(query):
    try:
        r1 = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 3
            }
        )
        data = r1.json()
        return " ".join([i["content"] for i in data.get("results", [])])
    except:
        return ""

def wikipedia(query):
    try:
        r1 = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}")
        return r1.json().get("extract", "")
    except:
        return ""

def dictionary(word):
    try:
        r1 = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        return r1.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return ""

# =====================================================
# MEMORY + REAL INDEXING
# =====================================================
def save(chat, role, msg):
    r.lpush(f"chat:{chat}", f"{role}:{msg}")
    r.ltrim(f"chat:{chat}", 0, 40)

    # 🔍 indexing for search
    for w in msg.lower().split():
        r.sadd(f"index:{w}", chat)

def memory(chat):
    data = r.lrange(f"chat:{chat}", 0, -1)
    return [
        {"role": m.split(":")[0], "content": m.split(":", 1)[1]}
        for m in reversed(data)
    ]

# =====================================================
# 🔥 FIXED AI ROUTER (IMPORTANT CHANGE YOU REQUESTED)
# =====================================================
def engine(chat, msg):
    q = msg.lower().strip()

    # 🌐 1. TAVILY FIRST (LIVE DATA)
    t = tavily(msg)
    if t:
        return "🌐 Web Results:\n" + t

    # 🤖 2. GROQ SECOND (MAIN INTELLIGENCE)
    msgs = [SYSTEM] + memory(chat)
    msgs.append({"role": "user", "content": msg})
    ai = groq(msgs)
    if ai:
        return ai

    # 📚 3. WIKIPEDIA THIRD
    w = wikipedia(msg)
    if w:
        return "📚 Wikipedia:\n" + w

    # 📖 4. DICTIONARY LAST
    if len(q.split()) == 1:
        d = dictionary(msg)
        if d:
            return "📖 Definition:\n" + d

    return "No result found."

# =====================================================
# SOCKET STREAMING
# =====================================================
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

# =====================================================
# CHAT SYSTEM
# =====================================================
@app.route("/new_chat", methods=["POST"])
def new_chat():
    cid = str(uuid.uuid4())
    r.set(f"title:{cid}", "New Chat")
    return jsonify({"id": cid})

@app.route("/rename_chat", methods=["POST"])
def rename_chat():
    d = request.json
    r.set(f"title:{d['id']}", d["title"])
    return jsonify({"ok": True})

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    d = request.json
    r.delete(f"chat:{d['id']}")
    r.delete(f"title:{d['id']}")
    return jsonify({"ok": True})

@app.route("/chats")
def chats():
    keys = r.keys("title:*")
    return jsonify([
        [k.replace("title:", ""), r.get(k)]
        for k in keys
    ])

# =====================================================
# 🔍 REAL INDEX SEARCH (NOT UI FILTER)
# =====================================================
@app.route("/search_chats")
def search_chats():
    q = request.args.get("q", "").lower().strip()

    if not q:
        return jsonify([])

    words = q.split()
    sets = [r.smembers(f"index:{w}") for w in words]

    if not sets:
        return jsonify([])

    result = set(sets[0])
    for s in sets[1:]:
        result = result.intersection(s)

    return jsonify([
        {
            "id": cid,
            "title": r.get(f"title:{cid}") or "Untitled"
        }
        for cid in list(result)
    ])

# =====================================================
# LOGIN + VERIFIED SYSTEM
# =====================================================
@app.route("/login", methods=["POST"])
def login():
    u = request.json["username"]

    if u in USERS:
        session["user"] = u
        return jsonify({"ok": True, "verified": USERS[u]["verified"]})

    return jsonify({"ok": False})

# =====================================================
# FULL UI (CHATGPT STYLE)
# =====================================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;display:flex;height:100vh;font-family:sans-serif;background:#0d0d0d;color:white}

/* SIDEBAR */
#sidebar{width:260px;background:#111;display:flex;flex-direction:column;resize:horizontal;overflow:auto}
.chat{padding:10px;border-bottom:1px solid #222;display:flex;justify-content:space-between;cursor:pointer}
.chat:hover{background:#222}
.search{padding:10px;background:#222;border:none;color:white}

/* MAIN */
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;padding:20px;overflow:auto}
.msg{padding:10px;margin:6px;border-radius:10px;max-width:70%}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

/* INPUT */
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;background:#2563eb;color:white;border:none;padding:10px}

/* FADED TEXT */
.faded{
position:absolute;bottom:60px;left:50%;transform:translateX(-50%);
color:#666;font-size:12px;
}
</style>
</head>

<body>

<div id="sidebar">
<input class="search" id="search" placeholder="Search chats...">
<button onclick="newChat()">+ New Chat</button>
<div id="list"></div>
</div>

<div id="main">
<div id="chat"></div>

<div class="faded">Bloxy-bot can make mistakes. Double check responses.</div>

<div id="input">
<input id="msg">
<button onclick="send()">Send</button>
</div>
</div>

<script>
const socket = io();
let current=null;
let aiMsg=null;

function add(r,t){
let d=document.createElement("div");
d.className="msg "+r;
d.textContent=t;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
return d;
}

socket.on("stream",d=>{
if(aiMsg) aiMsg.textContent=d.data;
});

function send(){
let m=msg.value;if(!m)return;
msg.value="";
add("user",m);
aiMsg=add("ai","Thinking...");
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

let t=document.createElement("span");
t.textContent=c[1];

let m=document.createElement("span");
m.textContent="⋮";

m.onclick=async(e)=>{
e.stopPropagation();
let a=prompt("rename / delete");

if(a==="rename"){
let n=prompt("new name");
await fetch("/rename_chat",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({id:c[0],title:n})});
load();
}

if(a==="delete"){
await fetch("/delete_chat",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({id:c[0]})});
load();
}
};

d.onclick=()=>{current=c[0];chat.innerHTML="";};

d.appendChild(t);
d.appendChild(m);
list.appendChild(d);
});
}

document.getElementById("search").addEventListener("input", async (e)=>{
let q=e.target.value;

if(!q){load();return;}

let r=await fetch("/search_chats?q="+q);
let data=await r.json();

list.innerHTML="";
data.forEach(c=>{
let d=document.createElement("div");
d.className="chat";
d.textContent=c.title;

d.onclick=()=>{
current=c.id;
chat.innerHTML="";
};

list.appendChild(d);
});
});

load();
</script>

</body>
</html>
""")

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
