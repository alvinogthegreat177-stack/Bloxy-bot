from flask import Flask, request, jsonify, render_template_string
import os
import requests
import sqlite3
import uuid

app = Flask(__name__)

# 🔐 KEYS (set these in Render env vars)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 🧠 SAFE TAVILY
tavily = None
if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except:
        tavily = None

# 💾 DB (persistent chats)
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS chats(
    id TEXT PRIMARY KEY,
    title TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS messages(
    chat_id TEXT,
    role TEXT,
    content TEXT
)
""")
conn.commit()

# 🧠 SYSTEM PROMPT (clean formatting)
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot.

RULES:
- Answer directly
- NEVER say you lack access
- Use provided info

FORMAT:
- Use vertical lists
- Each item on a new line
- Keep answers clean and readable
"""
}

# 🌐 SEARCH
def web_search(query):
    if not tavily:
        return ""
    try:
        res = tavily.search(query=query, search_depth="basic", max_results=3)
        return "\n".join([r.get("content","") for r in res.get("results",[])])
    except:
        return ""

def wiki(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ','_')}"
        return requests.get(url).json().get("extract","")
    except:
        return ""

# 🧠 GROQ
def ask_groq(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":"application/json"
            },
            json={
                "model":"llama-3.3-70b-versatile",
                "messages":messages,
                "temperature":0.3
            }
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Error: {e}"

# 🧠 TITLE GENERATOR
def make_title(msg):
    try:
        return ask_groq([
            {"role":"user","content":f"Make a short 3 word title: {msg}"}
        ]).strip()
    except:
        return "New Chat"

# 🎨 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body{margin:0;font-family:Arial;display:flex;height:100vh}
#sidebar{width:250px;background:#111;color:white;padding:10px}
.chat-item{padding:10px;cursor:pointer}
.chat-item:hover{background:#333}
.active{background:#444}
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;overflow-y:auto;padding:10px;background:#f4f4f4}
.msg{padding:10px;margin:5px;border-radius:8px;max-width:70%}
.user{background:#4a90e2;color:white;margin-left:auto}
.ai{background:white}
#input{display:flex;padding:10px}
input{flex:1;padding:10px}
button{margin-left:10px}
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
<input id="msg" placeholder="Type..." />
<button onclick="send()">Send</button>
</div>
</div>

<script>
let current=null;

// LOAD CHATS
async function load(){
 let r=await fetch("/chats");
 let d=await r.json();
 let list=document.getElementById("list");
 list.innerHTML="";

 d.chats.forEach(c=>{
   list.innerHTML+=`
   <div class='chat-item ${c.id===current?"active":""}'
   onclick="switchChat('${c.id}')">${c.title}</div>`;
 });

 if(!current && d.chats.length>0){
    current=d.chats[0].id;
 }
}

// SWITCH CHAT
async function switchChat(id){
 current=id;
 let r=await fetch("/history?chat="+id);
 let d=await r.json();

 let chat=document.getElementById("chat");
 chat.innerHTML="";

 d.messages.forEach(m=>{
   chat.innerHTML+=`<div class='msg ${m.role==="user"?"user":"ai"}'>${m.content}</div>`;
 });
}

// NEW CHAT (FIXED)
async function newChat(){
 let r=await fetch("/new_chat",{method:"POST"});
 let d=await r.json();
 current=d.id;
 load();
 document.getElementById("chat").innerHTML="";
}

// SEND MESSAGE (FIXED)
async function send(){
 let input=document.getElementById("msg");
 let m=input.value;
 if(!m)return;

 input.value=""; // ✅ clear immediately

 let chat=document.getElementById("chat");
 chat.innerHTML+=`<div class='msg user'>${m}</div>`;

 let r=await fetch("/ai",{
 method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({message:m,chat:current})
 });

 let d=await r.json();
 chat.innerHTML+=`<div class='msg ai'>${d.response}</div>`;
 chat.scrollTop=chat.scrollHeight;

 load();
}

// ENTER KEY FIX
document.getElementById("msg").addEventListener("keypress", function(e){
 if(e.key==="Enter"){
  e.preventDefault();
  send();
 }
});

load();
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chats")
def chats_list():
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

@app.route("/ai", methods=["POST"])
def ai():
    data=request.json
    msg=data["message"]
    cid=data["chat"]

    # 🌐 get context
    context=web_search(msg)
    if not context:
        context=wiki(msg)

    prompt=f"User: {msg}\n\nInfo:\n{context}"

    cur.execute("SELECT role,content FROM messages WHERE chat_id=?",(cid,))
    history=[{"role":r,"content":c} for r,c in cur.fetchall()]

    reply=ask_groq([SYSTEM]+history[-10:]+[{"role":"user","content":prompt}])

    # 💾 save
    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"user",msg))
    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"assistant",reply))

    # 🧠 AUTO TITLE (FIRST MESSAGE)
    cur.execute("SELECT COUNT(*) FROM messages WHERE chat_id=?",(cid,))
    count=cur.fetchone()[0]

    if count<=2:
        title=make_title(msg)
        cur.execute("UPDATE chats SET title=? WHERE id=?",(title,cid))

    conn.commit()

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
