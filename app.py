from flask import Flask, request, jsonify, session, render_template_string
from groq import Groq
import wikipedia
import wolframalpha
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key")

# ---------------- SAFE API INIT (prevents Render crash) ----------------
groq_key = os.getenv("GROQ_API_KEY")
wolfram_key = os.getenv("WOLFRAM_APP_ID")
news_key = os.getenv("NEWS_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

groq_client = Groq(api_key=groq_key) if groq_key else None
wolfram = wolframalpha.Client(wolfram_key) if wolfram_key else None

# ---------------- MEMORY ----------------
chat_memory = {}

# ---------------- TOOLS (SAFE WRAPPED) ----------------

def use_wolfram(q):
    if not wolfram:
        return "Wolfram not configured."
    try:
        res = wolfram.query(q)
        return next(res.results).text
    except:
        return "Math error."

def use_news(topic="general"):
    if not news_key:
        return "News API not configured."
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=general&apiKey={news_key}"
        r = requests.get(url).json()
        return "\n".join([a["title"] for a in r.get("articles", [])[:3]])
    except:
        return "News error."

def use_wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "No Wikipedia result."

def use_dict(q):
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{q}").json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "No definition found."

# ---------------- UI ----------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body{margin:0;font-family:Arial;background:#0b0f1a;color:white;}
.sidebar{width:220px;height:100vh;position:fixed;background:#111827;padding:10px;}
.chat{margin-left:230px;padding:20px;}
.msg{padding:10px;margin:6px;border-radius:8px;}
.user{background:#2563eb;text-align:right;}
.ai{background:#1f2937;}
.fade{opacity:0.6;font-size:12px;}
</style>
</head>
<body>

<div class="sidebar">
<h3>Bloxy-bot</h3>
<p class="fade">AI can make mistakes</p>
<hr>
<button onclick="mode='ai'">AI</button><br>
<button onclick="mode='wiki'">Wiki</button><br>
<button onclick="mode='news'">News</button><br>
<button onclick="mode='math'">Math</button><br>
<button onclick="mode='dict'">Dict</button><br>
</div>

<div class="chat">
<div id="box"></div>
<input id="input">
<button onclick="send()">Send</button>
</div>

<script>
let mode="ai";

async function send(){
let msg=document.getElementById("input").value;
if(!msg)return;

add(msg,"user");

let res=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,mode:mode})
});

let data=await res.json();
add(data.reply,"ai");
}

function add(t,c){
let d=document.createElement("div");
d.className="msg "+c;
d.innerText=t;
document.getElementById("box").appendChild(d);
}
</script>

</body>
</html>
"""

# ---------------- ROUTER ----------------

def router(msg, mode):
    text = msg.lower()

    # dictionary ONLY when explicitly needed
    if mode == "dict" or "define" in text or "meaning" in text:
        return use_dict(msg)

    if mode == "math":
        return use_wolfram(msg)

    if mode == "news":
        return use_news(msg)

    if mode == "wiki":
        return use_wiki(msg)

    # fallback AI
    if groq_client:
        try:
            r = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role":"user","content":msg}]
            )
            return r.choices[0].message.content
        except:
            return "AI error."
    else:
        return "Groq not configured."

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data["message"]
    mode = data["mode"]

    user = session.get("user","guest")
    prefix = "✔ aTg (OWNER VERIFIED)" if user=="aTg" else user

    reply = router(msg, mode)

    return jsonify({"reply": f"{prefix}: {reply}"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run()
