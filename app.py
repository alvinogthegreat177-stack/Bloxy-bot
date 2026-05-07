from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests, json, os, traceback

app = FastAPI()

# ================= KEYS =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

# ================= OWNER =================
OWNER_EMAIL = "alvinogthegreat177@gmail.com"

# ================= STORAGE =================
USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

def load(f, d):
    try:
        return json.load(open(f))
    except:
        return d

def save(f, d):
    try:
        json.dump(d, open(f,"w"))
    except:
        pass

users = load(USERS_FILE, {})
chats = load(CHATS_FILE, {})

# ================= MODELS =================
class Auth(BaseModel):
    email: str
    password: str

class Chat(BaseModel):
    email: str
    chat_id: str
    message: str

# ================= TOOLS =================
def wiki(q):
    try:
        return requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + q
        ).json().get("extract","")
    except:
        return ""

def tavily(q):
    try:
        if not TAVILY_API_KEY:
            return ""
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": TAVILY_API_KEY,
            "query": q,
            "max_results": 2
        })
        return "\n".join([i.get("content","") for i in r.json().get("results",[])])
    except:
        return ""

def news(q):
    try:
        if not NEWS_API_KEY:
            return ""
        r = requests.get("https://newsapi.org/v2/everything",
            params={"q": q, "apiKey": NEWS_API_KEY, "pageSize": 2})
        return "\n".join([a.get("title","") for a in r.json().get("articles",[])])
    except:
        return ""

def wolfram(q):
    try:
        if not WOLFRAM_API_KEY:
            return ""
        return requests.get(
            "http://api.wolframalpha.com/v1/result",
            params={"appid": WOLFRAM_API_KEY, "i": q}
        ).text
    except:
        return ""

# ================= CONTEXT =================
def context(msg):
    t = msg.lower()
    out = []

    if any(x in t for x in ["who","what","city","country"]):
        w = wiki(msg)
        if w: out.append("WIKI:\n"+w)

    if "news" in t:
        w = news(msg)
        if w: out.append("NEWS:\n"+w)

    if any(x in t for x in ["math","solve","equation"]):
        w = wolfram(msg)
        if w: out.append("MATH:\n"+w)

    if any(x in t for x in ["search","web"]):
        w = tavily(msg)
        if w: out.append("WEB:\n"+w)

    return "\n\n".join(out)

# ================= GROQ FIX =================
def ai(messages):
    if not GROQ_API_KEY:
        return "Missing API key"

    clean = []
    for m in messages:
        if not isinstance(m, dict): continue
        if "role" not in m or "content" not in m: continue
        if m["content"] is None: continue

        clean.append({
            "role": str(m["role"]),
            "content": str(m["content"])
        })

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": clean,
                "temperature": 0.7,
                "max_tokens": 1000000
            }
        )

        if r.status_code != 200:
            return f"AI ERROR {r.status_code}"

        return r.json()["choices"][0]["message"]["content"]

    except:
        return "AI error"

# ================= SIGNUP =================
@app.post("/signup")
def signup(d: Auth):
    if d.email in users:
        return {"ok": False, "error": "exists"}

    users[d.email] = {
        "password": d.password,
        "username": d.email.split("@")[0]
    }

    save(USERS_FILE, users)
    return {"ok": True}

# ================= LOGIN =================
@app.post("/login")
def login(d: Auth):

    if d.email not in users:
        return {"ok": False}

    if users[d.email]["password"] != d.password:
        return {"ok": False}

    return {
        "ok": True,
        "email": d.email,
        "username": users[d.email]["username"],
        "verified": d.email == OWNER_EMAIL
    }

# ================= CHAT =================
@app.post("/chat")
def chat(d: Chat):

    if d.email not in chats:
        chats[d.email] = {}

    if d.chat_id not in chats[d.email]:
        chats[d.email][d.chat_id] = []

    history = chats[d.email][d.chat_id]

    system = {
        "role": "system",
        "content": "Bloxy-bot enterprise AI\n\n" + context(d.message)
    }

    messages = [system] + history + [
        {"role":"user","content":d.message}
    ]

    reply = ai(messages)

    history.append({"role":"user","content":d.message})
    history.append({"role":"assistant","content":reply})

    save(CHATS_FILE, chats)

    return {"reply": reply}

# ================= UI =================
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot v6</title>
<style>
body{margin:0;font-family:Arial;background:#0f0f0f;color:white;}
.container{display:flex;height:100vh;}
.sidebar{width:280px;background:#111;display:flex;flex-direction:column;}
.main{flex:1;display:flex;flex-direction:column;}
.msg{padding:12px;margin:10px;background:#1a1a1a;border-radius:10px;}
.input{padding:10px;background:#111;display:flex;}
input{flex:1;padding:10px;}
button{padding:10px;background:orange;border:none;}
</style>
</head>
<body>

<div class="container">

<div class="sidebar">
<h3 style="padding:10px;">Bloxy-bot v6</h3>
</div>

<div class="main">

<div id="chat"></div>

<div class="input">
<input id="msg">
<button onclick="send()">Send</button>
</div>

</div>

</div>

<script>
let email="test@test.com";
let chat_id="main";

async function send(){
let m=document.getElementById("msg").value;

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({email,chat_id,message:m})
});

let d=await r.json();

document.getElementById("chat").innerHTML +=
"<div class='msg'>"+m+"</div><div class='msg'>"+d.reply+"</div>";
}
</script>

</body>
</html>
"""
