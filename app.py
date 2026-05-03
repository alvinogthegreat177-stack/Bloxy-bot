# ================================
# CORE IMPORTS
# ================================
from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, requests, uuid

app = Flask(__name__)
app.secret_key = "bloxy_secret_key"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ================================
# DATABASE
# ================================
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT, password TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, user_id TEXT, title TEXT, folder TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# ================================
# AI KEYS
# ================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM = {
"role":"system",
"content":"""
You are Bloxy-bot 🤖.
- structured answers
- vertical formatting
- concise responses
"""
}

# ================================
# AUTH HELPERS
# ================================
def current_user():
    return session.get("user_id")

# ================================
# AUTH ROUTES
# ================================
@app.route("/register", methods=["POST"])
def register():
    data=request.json
    uid=str(uuid.uuid4())
    cur.execute("INSERT INTO users VALUES (?,?,?)",
                (uid,data["username"],generate_password_hash(data["password"])))
    conn.commit()
    return jsonify({"status":"registered"})

@app.route("/login", methods=["POST"])
def login():
    data=request.json
    cur.execute("SELECT * FROM users WHERE username=?",(data["username"],))
    u=cur.fetchone()

    if u and check_password_hash(u[2],data["password"]):
        session["user_id"]=u[0]
        return jsonify({"status":"ok"})
    return jsonify({"status":"fail"})

# ================================
# CHAT SYSTEM
# ================================
@app.route("/new_chat", methods=["POST"])
def new_chat():
    cid=str(uuid.uuid4())
    uid=current_user()
    cur.execute("INSERT INTO chats VALUES (?,?,?,?)",(cid,uid,"New Chat","default"))
    conn.commit()
    return jsonify({"id":cid})

@app.route("/rename_chat", methods=["POST"])
def rename():
    d=request.json
    cur.execute("UPDATE chats SET title=? WHERE id=?",(d["title"],d["id"]))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/delete_chat", methods=["POST"])
def delete():
    d=request.json
    cur.execute("DELETE FROM chats WHERE id=?",(d["id"],))
    cur.execute("DELETE FROM messages WHERE chat_id=?",(d["id"],))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/chats")
def chats():
    uid=current_user()
    cur.execute("SELECT * FROM chats WHERE user_id=?",(uid,))
    return jsonify(cur.fetchall())

# ================================
# MEMORY SYSTEM (IMPROVED)
# ================================
def save(cid,role,content):
    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,role,content))
    conn.commit()

def memory(cid):
    cur.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY rowid DESC LIMIT 15",(cid,))
    return [{"role":r,"content":c} for r,c in reversed(cur.fetchall())]

def long_memory(uid):
    cur.execute("SELECT content FROM messages m JOIN chats c ON m.chat_id=c.id WHERE c.user_id=?",(uid,))
    data=cur.fetchall()
    if len(data)<30:
        return None
    text=" ".join([x[0] for x in data[-60:]])
    return text[:1000]

# ================================
# AI ENGINE
# ================================
def groq(messages):
    r=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_API_KEY}"},
        json={"model":"llama-3.3-70b-versatile","messages":messages}
    )
    return r.json()["choices"][0]["message"]["content"]

def smart(q,cid,uid):

    msgs=[SYSTEM]

    mem=long_memory(uid)
    if mem:
        msgs.append({"role":"system","content":"User history: "+mem})

    msgs+=memory(cid)
    msgs.append({"role":"user","content":q})

    return groq(msgs)

# ================================
# WEBSOCKET STREAM
# ================================
@socketio.on("send")
def handle(data):
    uid=current_user()
    q=data["msg"]
    cid=data["chat"]

    reply=smart(q,cid,uid)

    save(cid,"user",q)

    buffer=""
    for w in reply.split():
        buffer+=w+" "
        emit("stream",{"data":buffer})
        socketio.sleep(0.02)

    save(cid,"assistant",reply)

# ================================
# UI (SIMPLE SAAS DASHBOARD)
# ================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<style>
body{margin:0;display:flex;height:100vh;font-family:sans-serif;background:#0d0d0d;color:white}

/* sidebar */
#sidebar{width:260px;background:#111;overflow:auto;resize:horizontal}
.chat{padding:10px;border-bottom:1px solid #222;cursor:pointer}
.chat:hover{background:#222}

/* main */
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;padding:20px;overflow:auto}

.msg{padding:10px;margin:5px;border-radius:8px;max-width:70%}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;background:#2563eb;color:white;border:none;padding:10px}
</style>
</head>

<body>

<div id="sidebar">
<button onclick="newChat()">+ New</button>
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
const socket=io();
let current=null;
let aiMsg=null;

function add(r,t){
let d=document.createElement("div");
d.className="msg "+r;
d.textContent=t;
chat.appendChild(d);
return d;
}

socket.on("stream",d=>{
if(aiMsg) aiMsg.textContent=d.data;
chat.scrollTop=chat.scrollHeight;
});

function send(){
let m=msg.value;
if(!m)return;
msg.value="";

add("user",m);
aiMsg=add("ai","...");
socket.emit("send",{msg:m,chat:current});
}

async function newChat(){
let r=await fetch("/new_chat",{method:"POST"});
let d=await r.json();
current=d.id;
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
d.onclick=()=>{current=c[0];chat.innerHTML="";}
list.appendChild(d);
});
}

load();
</script>

</body>
</html>
""")

# ================================
# RUN
# ================================
if __name__=="__main__":
    socketio.run(app)

