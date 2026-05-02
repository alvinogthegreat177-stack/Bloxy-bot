# ================================
# IMPORTS (NO EVENTLET)
# ================================
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
import sqlite3, os, requests, uuid

app = Flask(__name__)

# ✅ THREADING MODE (stable)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ================================
# KEYS
# ================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# ================================
# DATABASE
# ================================
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# ================================
# SYSTEM PROMPT
# ================================
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Rules:
- Always answer clearly
- Use vertical formatting for lists
- Be accurate and helpful
"""
}

# ================================
# TOOLS
# ================================

def dictionary(q):
    try:
        if not any(x in q.lower() for x in ["define","meaning","what is"]):
            return None
        word = q.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

def wiki(q):
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}")
        if r.status_code == 200:
            return r.json().get("extract")
    except:
        return None

def tavily(q):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": q}
        )
        results = r.json().get("results", [])
        return " ".join([x["content"] for x in results[:3]])
    except:
        return None

def groq(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.4
            }
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ AI error: {str(e)}"

# ================================
# MEMORY
# ================================

def save(cid, role, content):
    cur.execute("INSERT INTO messages VALUES (?,?,?)", (cid, role, content))
    conn.commit()

def recent(cid):
    cur.execute(
        "SELECT role,content FROM messages WHERE chat_id=? ORDER BY rowid DESC LIMIT 10",
        (cid,)
    )
    return [{"role": r, "content": c} for r, c in reversed(cur.fetchall())]

def summary(cid):
    cur.execute("SELECT content FROM messages WHERE chat_id=?", (cid,))
    msgs = cur.fetchall()
    if len(msgs) < 20:
        return None
    text = " ".join([m[0] for m in msgs[-40:]])
    return f"Summary: {text[:700]}"

# ================================
# AI ROUTER
# ================================

def smart(q, cid):

    d = dictionary(q)
    if d:
        return f"📖 Definition:\n{d}"

    w = wiki(q.replace(" ", "_"))
    if w:
        return f"📚 {w[:400]}..."

    t = tavily(q)
    if t:
        return groq([
            SYSTEM,
            {"role": "user", "content": f"Summarize clearly:\n\n{t}"}
        ])

    msgs = [SYSTEM]
    s = summary(cid)
    if s:
        msgs.append({"role": "system", "content": s})

    msgs += recent(cid)
    msgs.append({"role": "user", "content": q})

    return groq(msgs)

# ================================
# WEBSOCKET STREAMING
# ================================

@socketio.on("send")
def handle(data):
    q = data["msg"]
    cid = data["chat"]

    reply = smart(q, cid)

    save(cid, "user", q)

    buffer = ""
    for word in reply.split():
        buffer += word + " "
        emit("stream", {"data": buffer})
        socketio.sleep(0.03)

    save(cid, "assistant", reply)

# ================================
# ROUTES
# ================================

@app.route("/new", methods=["POST"])
def new_chat():
    cid = str(uuid.uuid4())
    cur.execute("INSERT INTO chats VALUES (?,?)", (cid, "New Chat"))
    conn.commit()
    return jsonify({"id": cid})

@app.route("/chats")
def chats():
    cur.execute("SELECT * FROM chats")
    return jsonify(cur.fetchall())

# ================================
# UI
# ================================

@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:sans-serif}

/* Sidebar */
#sidebar{
width:260px;background:#111;display:flex;flex-direction:column;
resize:horizontal;overflow:auto
}
.chat{padding:10px;border-bottom:1px solid #222;cursor:pointer}
.chat:hover{background:#222}

/* Main */
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;padding:20px;overflow:auto}

/* Messages */
.msg{
padding:12px;margin:6px;border-radius:10px;
max-width:70%;white-space:pre-wrap;
animation:fade 0.3s ease;
}
@keyframes fade{from{opacity:0}to{opacity:1}}

.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

/* Input */
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;padding:10px;background:#2563eb;border:none;color:white}
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
<input id="msg" placeholder="Ask anything...">
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
if(aiMsg){aiMsg.textContent=d.data;}
});

function send(){
let m=msg.value;
if(!m)return;

msg.value="";
add("user",m);

aiMsg=add("ai","Processing your request... ⏳");

socket.emit("send",{msg:m,chat:current});
}

async function newChat(){
let r=await fetch("/new",{method:"POST"});
let d=await r.json();
current=d.id;
chat.innerHTML="";
loadChats();
}

async function loadChats(){
let r=await fetch("/chats");
let data=await r.json();

list.innerHTML="";
data.forEach(c=>{
let d=document.createElement("div");
d.className="chat";
d.textContent=c[1];
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

loadChats();
</script>

</body>
</html>
""")

# ================================
# RUN
# ================================
if __name__ == "__main__":
    socketio.run(app)
