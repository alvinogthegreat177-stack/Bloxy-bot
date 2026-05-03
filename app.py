from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import wikipedia
import wolframalpha
import requests
import os
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# ================= AI =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
wolfram = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID"))

NEWS_KEY = os.getenv("NEWS_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# ================= MEMORY =================
conversations = {}

# ================= TOOLS =================

def wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "Wikipedia result not found."

def math(q):
    try:
        return next(wolfram.query(q).results).text
    except:
        return "Math error."

def news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}"
        r = requests.get(url).json()
        return "\n".join([a["title"] for a in r["articles"][:5]])
    except:
        return "News unavailable."

def web(q):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": q}
        ).json()
        return r.get("answer", "No result.")
    except:
        return "Web search failed."

def dictionary(word):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        ).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "No definition found."

# ================= SMART ROUTER =================

def route(msg):

    t = msg.lower()

    if "define" in t or "meaning" in t:
        return dictionary(msg)

    if any(x in t for x in ["solve", "+", "-", "/", "equation"]):
        return math(msg)

    if "who is" in t or "what is" in t:
        return wiki(msg)

    if "news" in t or "latest" in t:
        return news()

    if "search" in t or "find" in t:
        return web(msg)

    return None

# ================= AI =================

def ai(msg):
    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role":"system","content":"Respond in formal diplomatic structured tone."},
                {"role":"user","content":msg}
            ]
        )
        return r.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return "⚠️ AI temporarily unavailable."

# ================= CORE RESPONSE =================

def get_response(msg):

    tool = route(msg)

    if tool:
        return tool

    return ai(msg)

# ================= TITLE =================

def make_title(text):
    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role":"user",
                "content":f"Summarize in 3-5 words: {text}"
            }]
        )
        return r.choices[0].message.content
    except:
        return "New Chat"

# ================= UI =================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

<style>
body{
margin:0;
font-family:Arial;
background:#0b0f1a;
color:white;
display:flex;
height:100vh;
}

/* SIDEBAR */
.sidebar{
width:280px;
background:#111827;
display:flex;
flex-direction:column;
}

.newchat{
margin:10px;
padding:10px;
background:#2563eb;
border:none;
color:white;
border-radius:6px;
cursor:pointer;
}

.conv{
flex:1;
overflow-y:auto;
padding:10px;
}

.item{
padding:8px;
margin:5px;
background:#1f2937;
border-radius:6px;
cursor:pointer;
display:flex;
justify-content:space-between;
}

/* CHAT */
.chat{
flex:1;
display:flex;
flex-direction:column;
}

.box{
flex:1;
overflow-y:auto;
padding:15px;
}

.msg{
padding:10px;
margin:8px;
border-radius:10px;
max-width:75%;
white-space:pre-line;
}

.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f2937;}

/* INPUT */
.input{
display:flex;
padding:10px;
background:#111827;
}

input{
flex:1;
padding:10px;
border:none;
outline:none;
}

button{
padding:10px;
background:#2563eb;
color:white;
border:none;
cursor:pointer;
}

/* FOOTER */
.footer{
text-align:center;
font-size:12px;
opacity:0.6;
padding:5px;
}

/* ACCOUNT */
.account{
padding:10px;
background:#0f172a;
}

/* VERIFIED BADGE */
.badge{
width:28px;
height:28px;
border-radius:50%;
background:#f97316;
display:flex;
align-items:center;
justify-content:center;
font-weight:bold;
box-shadow:
inset 2px 2px 4px rgba(255,255,255,0.3),
inset -2px -2px 4px rgba(0,0,0,0.4),
0 2px 6px rgba(0,0,0,0.4);
}
</style>
</head>

<body>

<div class="sidebar">

<button class="newchat" onclick="newChat()">+ New Chat</button>

<div class="conv" id="conv"></div>

<div class="account">
<div>✔ aTg</div>
<div class="badge">✔</div>
</div>

</div>

<div class="chat">

<div class="box" id="box"></div>

<div class="input">
<input id="input" onkeypress="key(event)">
<button onclick="send()">Send</button>
</div>

<div class="footer">
Bloxy-bot can make mistakes. Double check important information.
</div>

</div>

<script>

let current="default";

function key(e){
if(e.key==="Enter")send();
}

async function newChat(){
let r=await fetch("/new");
let d=await r.json();
current=d.id;
load();
document.getElementById("box").innerHTML="";
}

async function load(){
let r=await fetch("/conversations");
let d=await r.json();

document.getElementById("conv").innerHTML=
d.map(c=>`
<div class="item">
<span onclick="openChat('${c.id}')">${c.title}</span>
<span>
<button onclick="renameChat('${c.id}')">✏</button>
<button onclick="deleteChat('${c.id}')">🗑</button>
</span>
</div>
`).join("");
}

async function openChat(id){
current=id;
let r=await fetch("/load?id="+id);
let d=await r.json();

document.getElementById("box").innerHTML="";
d.forEach(m=>add(m.role+": "+m.text,m.role));
}

async function send(){

let input=document.getElementById("input");
let msg=input.value;
if(!msg)return;

add(msg,"user");
input.value="";

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,id:current})
});

let d=await r.json();
add(d.reply,"ai");
load();
}

function add(t,c){
let d=document.createElement("div");
d.className="msg "+c;
d.innerText=t;
document.getElementById("box").appendChild(d);
}

async function renameChat(id){
let n=prompt("Rename:");
if(!n)return;

await fetch("/rename",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id,name:n})
});

load();
}

async function deleteChat(id){
await fetch("/delete",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({id})
});

load();
document.getElementById("box").innerHTML="";
}

load();

</script>

</body>
</html>
"""

# ================= ROUTES =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/new")
def new():
    cid=str(uuid.uuid4())

    conversations[cid]={
        "title":"New Chat",
        "messages":[]
    }

    return jsonify({"id":cid})

@app.route("/chat",methods=["POST"])
def chat():

    data=request.json
    msg=data["message"]
    cid=data["id"]

    if cid not in conversations:
        conversations[cid]={"title":"New Chat","messages":[]}

    conv=conversations[cid]

    if len(conv["messages"])==0:
        conv["title"]=make_title(msg)

    reply=get_response(msg)

    conv["messages"].append({"role":"user","text":msg})
    conv["messages"].append({"role":"ai","text":reply})

    return jsonify({"reply":reply})

@app.route("/conversations")
def convs():
    return jsonify([
        {"id":k,"title":v["title"]}
        for k,v in conversations.items()
    ])

@app.route("/load")
def load():
    cid=request.args.get("id")
    return jsonify(conversations.get(cid,{"messages":[]})["messages"])

@app.route("/rename",methods=["POST"])
def rename():
    d=request.json
    if d["id"] in conversations:
        conversations[d["id"]]["title"]=d["name"]
    return jsonify({"ok":True})

@app.route("/delete",methods=["POST"])
def delete():
    cid=request.json["id"]
    conversations.pop(cid,None)
    return jsonify({"ok":True})

# ================= RUN =================
if __name__=="__main__":
    app.run()
