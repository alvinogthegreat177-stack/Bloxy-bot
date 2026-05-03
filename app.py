from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os, uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY","dev")

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ================= MEMORY =================
conversations = {}  
# format:
# {conv_id: {"title": "...", "messages":[...] }}

# ================= AI =================

def generate_title(text):
    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role":"user",
                "content":f"Summarize this in 4 words max for a chat title: {text}"
            }]
        )
        return r.choices[0].message.content.strip()
    except:
        return "New Chat"

def ai(msg):
    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role":"user","content":msg}]
        )
        return r.choices[0].message.content
    except Exception as e:
        return "AI temporarily unavailable."

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

/* ACCOUNT BADGE */
.account{
padding:10px;
background:#0f172a;
}

.badge{
width:28px;
height:28px;
border-radius:50%;
background:linear-gradient(135deg,#3b82f6,#f97316);
display:flex;
align-items:center;
justify-content:center;
font-size:14px;
font-weight:bold;
}

/* FOOTER */
.footer{
text-align:center;
font-size:12px;
opacity:0.6;
padding:5px;
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

async function newChat(){
let r=await fetch("/new_chat",{method:"POST"});
let d=await r.json();
current=d.id;
loadConversations();
document.getElementById("box").innerHTML="";
}

async function loadConversations(){
let r=await fetch("/conversations");
let d=await r.json();

document.getElementById("conv").innerHTML=
d.map(c=>`<div class='item' onclick="openChat('${c.id}')">${c.title}</div>`).join("");
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
loadConversations();
}

function add(t,c){
let d=document.createElement("div");
d.className="msg "+c;
d.innerText=t;
document.getElementById("box").appendChild(d);
}

function key(e){if(e.key==="Enter")send();}

loadConversations();

</script>

</body>
</html>
"""

# ================= BACKEND =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/new_chat",methods=["POST"])
def new_chat():
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
        conversations[cid]={
            "title":"New Chat",
            "messages":[]
        }

    conv=conversations[cid]

    # first message → generate title
    if len(conv["messages"])==0:
        conv["title"]=generate_title(msg)

    reply=ai(msg)

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

# ================= RUN =================
if __name__=="__main__":
    app.run()
