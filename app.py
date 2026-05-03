import os
import uuid
import redis
import requests

from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO

# =====================================================
# APP SETUP
# =====================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bloxy_secret")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# =====================================================
# REDIS
# =====================================================
r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

# =====================================================
# API KEYS
# =====================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# =====================================================
# AUTH SYSTEM (REAL)
# =====================================================
def create_user(u, p):
    r.hset(f"user:{u}", mapping={"password": p, "verified": "0"})

def get_user(u):
    return r.hgetall(f"user:{u}")

# =====================================================
# AI (GROQ)
# =====================================================
def groq(messages):
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages}
    )
    return res.json()["choices"][0]["message"]["content"]

SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot. Be clear, structured, and helpful."
}

# =====================================================
# SOURCES
# =====================================================
def tavily(q):
    try:
        r1 = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": q, "max_results": 3}
        )
        return " ".join([i["content"] for i in r1.json().get("results", [])])
    except:
        return ""

def wikipedia(q):
    try:
        r1 = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}")
        return r1.json().get("extract", "")
    except:
        return ""

def dictionary(w):
    try:
        r1 = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{w}")
        return r1.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return ""

# =====================================================
# MEMORY + INDEXING (PER USER)
# =====================================================
def save(chat, role, msg):
    user = session.get("user", "guest")

    r.lpush(f"chat:{user}:{chat}", f"{role}:{msg}")
    r.ltrim(f"chat:{user}:{chat}", 0, 40)

    for w in msg.lower().split():
        r.sadd(f"index:{user}:{w}", chat)

def memory(chat):
    user = session.get("user", "guest")
    data = r.lrange(f"chat:{user}:{chat}", 0, -1)

    return [{"role": m.split(":")[0], "content": m.split(":", 1)[1]} for m in reversed(data)]

# =====================================================
# AI ROUTER (FIXED PRIORITY)
# =====================================================
def engine(chat, msg):

    # 🌐 Tavily FIRST
    t = tavily(msg)
    if t:
        return "🌐 Web:\n" + t

    # 🤖 Groq SECOND
    msgs = [SYSTEM] + memory(chat)
    msgs.append({"role": "user", "content": msg})
    ai = groq(msgs)
    if ai:
        return ai

    # 📚 Wikipedia THIRD
    w = wikipedia(msg)
    if w:
        return "📚 Wikipedia:\n" + w

    # 📖 Dictionary LAST
    if len(msg.split()) == 1:
        d = dictionary(msg)
        if d:
            return "📖 Definition:\n" + d

    return "No result found."

# =====================================================
# SOCKET STREAM
# =====================================================
@socketio.on("send")
def handle(data):
    chat = data["chat"]
    msg = data["msg"]

    reply = engine(chat, msg)

    save(chat, "user", msg)

    buffer = ""

    for w in reply.split():
        buffer += w + " "
        socketio.emit("stream", {"data": buffer})
        socketio.sleep(0.02)

    save(chat, "assistant", reply)

# =====================================================
# AUTH ROUTES
# =====================================================
@app.route("/register", methods=["POST"])
def register():
    d = request.json
    if r.exists(f"user:{d['username']}"):
        return jsonify({"ok": False})
    create_user(d["username"], d["password"])
    return jsonify({"ok": True})

@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u = get_user(d["username"])

    if not u:
        return jsonify({"ok": False})

    if u["password"] != d["password"]:
        return jsonify({"ok": False})

    session["user"] = d["username"]
    return jsonify({"ok": True})

@app.route("/me")
def me():
    u = session.get("user")
    if not u:
        return jsonify({"logged": False})

    return jsonify({"logged": True, "user": u})

# =====================================================
# CHAT SYSTEM
# =====================================================
@app.route("/new_chat", methods=["POST"])
def new_chat():
    user = session.get("user", "guest")
    cid = str(uuid.uuid4())
    r.set(f"title:{user}:{cid}", "New Chat")
    return jsonify({"id": cid})

@app.route("/chats")
def chats():
    user = session.get("user", "guest")

    keys = r.keys(f"title:{user}:*")

    return jsonify([[k.split(":")[-1], r.get(k)] for k in keys])

@app.route("/rename_chat", methods=["POST"])
def rename():
    d = request.json
    user = session.get("user", "guest")
    r.set(f"title:{user}:{d['id']}", d["title"])
    return jsonify({"ok": True})

@app.route("/delete_chat", methods=["POST"])
def delete():
    d = request.json
    user = session.get("user", "guest")
    r.delete(f"chat:{user}:{d['id']}")
    r.delete(f"title:{user}:{d['id']}")
    return jsonify({"ok": True})

# =====================================================
# REAL SEARCH (INDEXED)
# =====================================================
@app.route("/search_chats")
def search():
    q = request.args.get("q", "").lower()
    user = session.get("user", "guest")

    words = q.split()
    sets = []

    for w in words:
        sets.append(r.smembers(f"index:{user}:{w}"))

    if not sets:
        return jsonify([])

    res = set(sets[0])
    for s in sets[1:]:
        res = res.intersection(s)

    return jsonify([
        {"id": cid, "title": r.get(f"title:{user}:{cid}")}
        for cid in list(res)
    ])

# =====================================================
# UI
# =====================================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:sans-serif}

/* SIDEBAR */
#sidebar{width:260px;background:#111;display:flex;flex-direction:column;resize:horizontal;overflow:auto}
.chat{padding:10px;border-bottom:1px solid #222;cursor:pointer;display:flex;justify-content:space-between}
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
input{flex:1;padding:10px;background:#222;border:none;color:white}
button{margin-left:10px;background:#2563eb;border:none;color:white;padding:10px}

/* FADED */
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

document.getElementById("msg").addEventListener("keydown", e=>{
    if(e.key==="Enter") send();
});

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
</script>

</body>
</html>
""")

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
