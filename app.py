from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 💾 DB
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Rules:
- Always respond in clean structured format
- Use vertical lists for steps/options
- Never dump raw web pages
- Be clear, readable, and structured
"""
}

# 📖 DICTIONARY
def dictionary_lookup(query):
    if not any(x in query.lower() for x in ["define","meaning","what is"]):
        return None
    try:
        word = query.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# 📚 WIKIPEDIA
def wikipedia(query):
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}")
        return r.json().get("extract")
    except:
        return None

# 🌐 TAVILY
def tavily(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        results = r.json().get("results", [])
        return " ".join([r["content"] for r in results[:3]]) if results else None
    except:
        return None

# 🤖 GROQ
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model":"llama-3.3-70b-versatile","messages":messages}
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 AI ROUTER
def smart_answer(query, history):

    q = query.lower().strip()

    if q in ["hi","hello","hey"]:
        return "Hello 👋\n\nHow can I help you today?"

    d = dictionary_lookup(query)
    if d:
        return f"📖 Definition:\n{d}"

    w = wikipedia(query.replace(" ","_"))
    if w:
        return f"📚 {w[:500]}..."

    t = tavily(query)
    if t:
        return groq([SYSTEM, {"role":"user","content":f"Summarize clearly:\n\n{t}"}])

    return groq([SYSTEM] + history + [{"role":"user","content":query}])


# 🎨 FULL UI (CHATGPT-STYLE SIDEBAR)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>

<style>

body{
margin:0;
display:flex;
height:100vh;
background:#0d0d0d;
color:white;
font-family:Arial;
}

/* SIDEBAR */
#sidebar{
width:260px;
background:#111;
display:flex;
flex-direction:column;
transition:0.3s;
overflow:hidden;
}

#sidebar.collapsed{
width:70px;
}

#top{
display:flex;
justify-content:space-between;
padding:15px;
border-bottom:1px solid #222;
font-weight:bold;
}

#toggle{
cursor:pointer;
}

.chat-item{
padding:10px;
cursor:pointer;
display:flex;
justify-content:space-between;
position:relative;
}

.chat-item:hover{
background:#222;
}

/* dropdown */
.menu{
cursor:pointer;
}

.dropdown{
display:none;
position:absolute;
right:10px;
top:35px;
background:#222;
padding:5px;
border-radius:6px;
z-index:10;
}

.chat-item.active{
background:#2563eb;
}

/* MAIN */
#main{
flex:1;
display:flex;
flex-direction:column;
}

#header{
padding:15px;
border-bottom:1px solid #222;
font-weight:bold;
}

#chat{
flex:1;
padding:20px;
overflow-y:auto;
}

.msg{
max-width:70%;
padding:12px;
margin:6px;
border-radius:10px;
white-space:pre-wrap;
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
color:white;
border:none;
}

button{
margin-left:10px;
padding:10px;
background:#2563eb;
color:white;
border:none;
}

#footer{
text-align:center;
font-size:12px;
color:#777;
padding:5px;
}

</style>

</head>

<body>

<div id="sidebar">

<div id="top">
<span>Bloxy-bot 🤖</span>
<span id="toggle" onclick="toggle()">☰</span>
</div>

<button onclick="newChat()">+ New Chat</button>

<div id="list"></div>

</div>

<div id="main">

<div id="header">Bloxy-bot 🤖</div>

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot...">
<button onclick="send()">Send</button>
</div>

<div id="footer">
Bloxy-bot can make mistakes. Double-check just in case.
</div>

</div>

<script>

let current=null;

/* SIDEBAR TOGGLE */
function toggle(){
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
<div class="chat-item" onclick="openChat('${c.id}')">
<span>${c.title}</span>
<span class="menu" onclick="event.stopPropagation();toggleMenu(this)">⋮</span>

<div class="dropdown">
<div onclick="rename('${c.id}')">Rename</div>
<div onclick="del('${c.id}')">Delete</div>
</div>

</div>`;
});
}

/* CHAT OPEN */
async function openChat(id){
current=id;
document.getElementById("chat").innerHTML="";

let r=await fetch("/history?chat="+id);
let d=await r.json();

d.messages.forEach(m=>{
add(m.role,m.content);
});
}

/* ADD MSG */
function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
document.getElementById("chat").appendChild(d);
}

/* NEW CHAT */
async function newChat(){
let r=await fetch("/new",{method:"POST"});
let d=await r.json();
current=d.id;
document.getElementById("chat").innerHTML="";
load();
}

/* DELETE */
async function del(id){
await fetch("/delete",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id})});
load();
}

/* RENAME */
function rename(id){
let name=prompt("Rename chat:");
if(!name) return;
fetch("/rename",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id,name})});
load();
}

/* MENU */
function toggleMenu(el){
let d=el.parentElement.querySelector(".dropdown");
d.style.display = d.style.display==="block"?"none":"block";
}

/* SEND */
async function send(){
let input=document.getElementById("msg");
let msg=input.value;
if(!msg) return;

input.value="";

add("user",msg);
let ai=add("ai","Thinking... 🤖");

let r=await fetch("/ai",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,chat:current})});

let d=await r.json();

ai.textContent=d.response;
}

document.getElementById("msg").addEventListener("keypress",e=>{
if(e.key==="Enter"){e.preventDefault();send();}
});

load();

</script>

</body>
</html>
"""

# 🌐 ROUTES
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chats")
def chats():
    cur.execute("SELECT id,title FROM chats")
    return jsonify({"chats":[{"id":i,"title":t} for i,t in cur.fetchall()]})

@app.route("/new", methods=["POST"])
def new():
    cid=str(uuid.uuid4())
    cur.execute("INSERT INTO chats VALUES (?,?)",(cid,"New Chat"))
    conn.commit()
    return jsonify({"id":cid})

@app.route("/delete", methods=["POST"])
def delete():
    cid=request.json["id"]
    cur.execute("DELETE FROM chats WHERE id=?",(cid,))
    cur.execute("DELETE FROM messages WHERE chat_id=?",(cid,))
    conn.commit()
    return "ok"

@app.route("/rename", methods=["POST"])
def rename():
    data=request.json
    cur.execute("UPDATE chats SET title=? WHERE id=?",(data["name"],data["id"]))
    conn.commit()
    return "ok"

@app.route("/history")
def history():
    cid=request.args.get("chat")
    cur.execute("SELECT role,content FROM messages WHERE chat_id=?",(cid,))
    return jsonify({"messages":[{"role":r,"content":c} for r,c in cur.fetchall()]})

@app.route("/ai", methods=["POST"])
def ai():
    data=request.json
    msg=data["message"]

    cur.execute("SELECT role,content FROM messages")
    history=[{"role":r,"content":c} for r,c in cur.fetchall()]

    reply=smart_answer(msg, history[-10:])

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
