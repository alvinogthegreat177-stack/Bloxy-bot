from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 💾 DATABASE
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM
SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot 🤖. Be clear, structured, and helpful."
}

# 📖 DICTIONARY
def dictionary_lookup(query):
    try:
        word = query.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if r.status_code == 200:
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
        if results:
            return "\\n".join([i["content"] for i in results[:3]])
    except:
        return None

# 🤖 GROQ
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages}
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 ROUTER
def smart_answer(query, history):
    d = dictionary_lookup(query)
    if d:
        return f"📖 Definition:\\n{d}"

    w = wikipedia(query.replace(" ", "_"))
    if w:
        return f"📚 {w}"

    t = tavily(query)
    if t:
        return f"🌐 {t}"

    return groq([SYSTEM] + history + [{"role": "user", "content": query}])

# 🎨 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}
#sidebar{width:250px;background:#111;padding:10px;overflow-y:auto}
#chat{flex:1;padding:20px;overflow-y:auto}
.msg{max-width:70%;padding:12px;margin:6px;border-radius:10px;white-space:pre-wrap}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;background:#2563eb;color:white;border:none;padding:10px}
</style>
</head>

<body>

<div id="sidebar">
<button onclick="newChat()">+ New Chat 🤖</button>
<div id="list"></div>
</div>

<div style="flex:1;display:flex;flex-direction:column">
<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot 🤖...">
<button onclick="send()">Send</button>
</div>
</div>

<script>

let current=null;
const chat=document.getElementById("chat");

/* ADD MESSAGE */
function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
return d;
}

/* STREAM */
function streamTo(el,text){
let i=0;
let t=setInterval(()=>{
el.textContent=text.slice(0,i++);
if(i>text.length) clearInterval(t);
},8);
}

/* LOAD CHATS */
async function load(){
let r=await fetch("/chats");
let d=await r.json();
let list=document.getElementById("list");
list.innerHTML="";
d.chats.forEach(c=>{
list.innerHTML+=`<div onclick="switchChat('${c.id}')">${c.title}</div>`;
});
}

/* SWITCH */
async function switchChat(id){
current=id;
chat.innerHTML="";
let r=await fetch("/history?chat="+id);
let d=await r.json();
d.messages.forEach(m=>add(m.role,m.content));
}

/* NEW CHAT */
async function newChat(){
let r=await fetch("/new",{method:"POST"});
let d=await r.json();
current=d.id;
chat.innerHTML="";
load();
}

/* SEND */
async function send(){
let input=document.getElementById("msg");
let msg=input.value;
if(!msg) return;

input.value="";

add("user",msg);

/* INLINE PROCESSING MESSAGE */
let aiMsg = add("ai","Bloxy-bot is thinking... 🤖");

let r=await fetch("/ai",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,chat:current})
});

let d=await r.json();

/* REPLACE WITH STREAM */
aiMsg.textContent="";
streamTo(aiMsg,d.response);
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
    cur.execute("INSERT INTO chats VALUES (?,?)",(cid,"Bloxy Chat 🤖"))
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
    cid=data["chat"]
    msg=data["message"]

    cur.execute("SELECT role,content FROM messages WHERE chat_id=?",(cid,))
    history=[{"role":r,"content":c} for r,c in cur.fetchall()]

    reply=smart_answer(msg, history[-10:])

    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"user",msg))
    cur.execute("INSERT INTO messages VALUES (?,?,?)",(cid,"assistant",reply))
    conn.commit()

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
