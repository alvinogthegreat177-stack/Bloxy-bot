from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# 💾 DB
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

SYSTEM = {
    "role": "system",
    "content": "Be structured, clear, and concise."
}

# 🧠 AI
def ask(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.3
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# 🎨 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Chat</title>

<style>
body{
margin:0;
display:flex;
height:100vh;
font-family:Arial;
background:#0d0d0d;
color:white;
}

/* SIDEBAR */
#sidebar{
width:260px;
background:#111;
overflow-y:auto;
transition:0.3s;
padding:10px;
}

#sidebar.collapsed{
width:60px;
}

.chat-item{
padding:10px;
display:flex;
justify-content:space-between;
align-items:center;
border-radius:8px;
cursor:pointer;
}

.chat-item:hover{background:#222;}
.active{background:#333;}

.actions{
display:flex;
gap:5px;
font-size:12px;
opacity:0.7;
}

.actions span{
cursor:pointer;
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
overflow-y:auto;
}

/* MSG */
.msg{
max-width:70%;
padding:12px;
margin:6px;
border-radius:10px;
white-space:pre-wrap;
}

.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f1f1f;}

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
color:white;
border:none;
}

button{
margin-left:10px;
}

/* TOGGLE */
#toggle{
cursor:pointer;
padding:8px;
margin-bottom:10px;
background:#222;
border-radius:6px;
text-align:center;
}
</style>

</head>

<body>

<div id="sidebar">

<div id="toggle" onclick="toggleSidebar()">☰</div>

<button onclick="newChat()">+ New</button>

<div id="list"></div>
</div>

<div id="main">

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Message..." />
<button onclick="send()">Send</button>
</div>

</div>

<script>

let current=null;

/* SIDEBAR TOGGLE */
function toggleSidebar(){
document.getElementById("sidebar").classList.toggle("collapsed");
}

/* LOAD CHATS */
async function load(){
let r=await fetch("/chats");
let d=await r.json();

let list=document.getElementById("list");
list.innerHTML="";

d.chats.forEach(c=>{
list.innerHTML+=`
<div class="chat-item ${c.id===current?"active":""}">
<span onclick="switchChat('${c.id}')">${c.title}</span>

<div class="actions">
<span onclick="rename('${c.id}')">✏️</span>
<span onclick="del('${c.id}')">🗑️</span>
</div>

</div>`;
});
}

/* SWITCH CHAT (FIXED - NO LOSS) */
async function switchChat(id){
current=id;

let r=await fetch("/history?chat="+id);
let d=await r.json();

let chat=document.getElementById("chat");
chat.innerHTML="";

d.messages.forEach(m=>{
add(m.role,m.content);
});
}

/* NEW CHAT */
async function newChat(){
let r=await fetch("/new_chat",{method:"POST"});
let d=await r.json();
current=d.id;
document.getElementById("chat").innerHTML="";
load();
}

/* ADD MESSAGE */
function add(role,text){
let div=document.createElement("div");
div.className="msg "+(role==="user"?"user":"ai");
div.textContent=text;
document.getElementById("chat").appendChild(div);
}

/* SEND */
async function send(){
let input=document.getElementById("msg");
let m=input.value;
if(!m)return;

input.value="";

add("user",m);

let r=await fetch("/ai",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:m,chat:current})
});

let d=await r.json();
add("ai",d.response);
}

/* ENTER */
document.getElementById("msg").addEventListener("keypress",e=>{
if(e.key==="Enter"){
e.preventDefault();
send();
}
});

/* RENAME INLINE */
function rename(id){
let name=prompt("New name:");
fetch("/rename",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id,name})
}).then(load);
}

/* DELETE INLINE */
function del(id){
fetch("/delete",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id})
}).then(load);
}

load();

</script>

</body>
</html>
"""

# ROUTES
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chats")
def chats():
    cur.execute("SELECT id,title FROM chats")
    return jsonify({"chats":[{"id":i,"title":t} for i,t in cur.fetchall()]})

@app.route("/new_chat", methods=["POST"])
def new_chat():
    cid=str(uuid.uuid4())
    cur.execute("INSERT INTO chats VALUES (?,?)",(cid,"New Chat"))
    conn.commit()
    return jsonify({"id":cid})

@app.route("/history")
def history():
    cid=request.args.get("chat")
    cur.execute("SELECT role,content FROM messages WHERE chat_id=?",(cid,))
    return jsonify({"messages":[{"role":r,"content":c} for r,c in cur.fetchall()]})

@app.route("/rename", methods=["POST"])
def rename():
    d=request.json
    cur.execute("UPDATE chats SET title=? WHERE id=?",(d["name"],d["id"]))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/delete", methods=["POST"])
def delete():
    cid=request.json["id"]
    cur.execute("DELETE FROM chats WHERE id=?",(cid,))
    cur.execute("DELETE FROM messages WHERE chat_id=?",(cid,))
    conn.commit()
    return jsonify({"ok":True})

@app.route("/ai", methods=["POST"])
def ai():
    d=request.json
    msg=d["message"]
    cid=d["chat"]

    cur.execute("SELECT role,content FROM messages WHERE chat_id=?",(cid,))
    history=[{"role":r,"content":c} for r,c in cur.fetchall()]

    reply=ask([SYSTEM]+history[-10:]+[
        {"role":"user","content":msg}
    ])

    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"user",msg))
    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"assistant",reply))
    conn.commit()

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
