from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import json
import os
import uuid

app = FastAPI()

# =========================================================
# KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

# =========================================================
# SAFE STORAGE (ANTI-CORRUPTION)
# =========================================================

def load(path, default):
    try:
        with open(path,"r") as f:
            return json.load(f)
    except:
        return default

def save(path,data):
    tmp = path + ".tmp"
    with open(tmp,"w") as f:
        json.dump(data,f)
    os.replace(tmp,path)

users = load(USERS_FILE,{})
chats = load(CHATS_FILE,{})

# =========================================================
# MODELS (SAFE AGAINST 400/422)
# =========================================================

class ChatRequest(BaseModel):
    email: str = "guest"
    chat_id: str = "main"
    message: str = ""

# =========================================================
# TOOLS
# =========================================================

def wiki(q):
    try:
        r=requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}")
        return r.json().get("extract","")
    except:
        return ""

def news(q):
    try:
        r=requests.get("https://newsapi.org/v2/everything",
            params={"q":q,"apiKey":NEWS_API_KEY})
        return "\n".join([a["title"] for a in r.json().get("articles",[])])
    except:
        return ""

def tavily(q):
    try:
        r=requests.post("https://api.tavily.com/search",
            json={"api_key":TAVILY_API_KEY,"query":q,"max_results":2})
        return "\n".join([x.get("content","") for x in r.json().get("results",[])])
    except:
        return ""

def wolfram(q):
    try:
        r=requests.get("http://api.wolframalpha.com/v1/result",
            params={"appid":WOLFRAM_API_KEY,"i":q})
        return r.text
    except:
        return ""

# =========================================================
# CONTEXT ENGINE
# =========================================================

def context(msg):
    t=msg.lower()
    out=[]

    if any(x in t for x in ["who is","what is","history","country"]):
        w=wiki(msg)
        if w: out.append("WIKI:\n"+w)

    if "news" in t:
        w=news(msg)
        if w: out.append("NEWS:\n"+w)

    if "search" in t:
        w=tavily(msg)
        if w: out.append("WEB:\n"+w)

    if any(x in t for x in ["math","solve","equation"]):
        w=wolfram(msg)
        if w: out.append("MATH:\n"+w)

    return "\n\n".join(out)

# =========================================================
# GROQ STREAM (FIXED PROPERLY)
# =========================================================

def groq_stream(messages):

    r=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization":f"Bearer {GROQ_API_KEY}",
            "Content-Type":"application/json"
        },
        json={
            "model":"llama3-70b-8192",
            "messages":messages,
            "temperature":0.7,
            "stream":True
        },
        stream=True
    )

    for line in r.iter_lines():
        if not line:
            continue

        line=line.decode()

        if "content" in line:
            try:
                yield line.split('"content":"')[1].split('"')[0]
            except:
                pass

# =========================================================
# CHAT STORAGE ENGINE
# =========================================================

def ensure_user(email):
    if email not in chats:
        chats[email] = {
            "active":"main",
            "list":{
                "main":{
                    "title":"Main Chat",
                    "messages":[]
                }
            }
        }

# =========================================================
# CHAT API
# =========================================================

@app.post("/chat")
def chat(data:ChatRequest):

    email=data.email or "guest"
    chat_id=data.chat_id or "main"
    msg=data.message or ""

    if msg.strip()=="":
        return {"reply":"Empty message"}

    ensure_user(email)

    if chat_id not in chats[email]["list"]:
        chats[email]["list"][chat_id]={
            "title":"New Chat",
            "messages":[]
        }

    history = chats[email]["list"][chat_id]["messages"]

    ctx=context(msg)

    system={
        "role":"system",
        "content":"You are Bloxy-bot AI.\n\nContext:\n"+ctx
    }

    messages=[system]+history+[{"role":"user","content":msg}]

    def stream():

        full=""

        for chunk in groq_stream(messages):
            full+=chunk
            yield chunk

        history.append({"role":"user","content":msg})
        history.append({"role":"assistant","content":full})

        save(CHATS_FILE,chats)

    return StreamingResponse(stream(),media_type="text/plain")

# =========================================================
# CHAT MANAGEMENT (SIDEBAR FEATURES)
# =========================================================

@app.post("/rename")
def rename(d:dict):

    email=d.get("email","guest")
    chat_id=d.get("chat_id")
    name=d.get("name")

    ensure_user(email)

    if chat_id in chats[email]["list"]:
        chats[email]["list"][chat_id]["title"]=name

    save(CHATS_FILE,chats)

    return {"ok":True}

@app.post("/delete")
def delete(d:dict):

    email=d.get("email","guest")
    chat_id=d.get("chat_id")

    ensure_user(email)

    if chat_id in chats[email]["list"]:
        del chats[email]["list"][chat_id]

    save(CHATS_FILE,chats)

    return {"ok":True}

@app.get("/list")
def list_chats(email:str="guest"):

    ensure_user(email)

    return chats[email]["list"]

# =========================================================
# UI (FULL SIDEBAR + CHAT + STREAM FIXED)
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot v3</title>
<style>
body{margin:0;background:#0f0f0f;color:white;font-family:Arial;}
.container{display:flex;height:100vh;}
.sidebar{width:260px;background:#111;padding:10px;}
.main{flex:1;display:flex;flex-direction:column;}
.box{flex:1;overflow:auto;padding:20px;}
.msg{margin:10px;padding:10px;border-radius:10px;}
.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f1f1f;}
.input{display:flex;padding:10px;background:#111;}
input{flex:1;padding:10px;}
button{padding:10px;background:#2563eb;color:white;}
.chatitem{padding:8px;background:#1a1a1a;margin:5px;cursor:pointer;}
</style>
</head>
<body>

<div class="container">

<div class="sidebar">
<h3>Chats</h3>
<div id="list"></div>
<button onclick="newChat()">+ New</button>
</div>

<div class="main">

<div class="box" id="box"></div>

<div class="input">
<input id="msg">
<button onclick="send()">Send</button>
</div>

</div>

</div>

<script>

let email="guest";
let current="main";

async function load(){

let r=await fetch("/list?email="+email);
let d=await r.json();

let box=document.getElementById("list");
box.innerHTML="";

for(let id in d){

let div=document.createElement("div");
div.className="chatitem";
div.innerText=d[id].title;

div.onclick=()=>{current=id;render();};

box.appendChild(div);
}
}

async function send(){

let m=document.getElementById("msg").value;
document.getElementById("msg").value="";

let box=document.getElementById("box");

let div=document.createElement("div");
div.className="msg ai";
box.appendChild(div);

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({email:email,chat_id:current,message:m})
});

const reader=r.body.getReader();
const decoder=new TextDecoder();

while(true){
const {value,done}=await reader.read();
if(done)break;
div.innerText+=decoder.decode(value);
}

load();
}

function newChat(){

current="chat_"+Date.now();

fetch("/rename",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({email:email,chat_id:current,name:"New Chat"})
});

load();
}

load();

</script>

</body>
</html>
"""

# =========================================================
# RUN
# =========================================================

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)
