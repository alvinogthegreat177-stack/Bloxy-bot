from flask import Flask, request, jsonify, session, render_template_string
from groq import Groq
import wikipedia
import wolframalpha
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= AI + TOOLS =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
wolfram = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID"))

NEWS_KEY = os.getenv("NEWS_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# ================= MEMORY =================
users = {}
chat_memory = {}

# ================= TOOLS =================

def use_wolfram(q):
    try:
        res = wolfram.query(q)
        return next(res.results).text
    except:
        return "Math error."

def use_news(q):
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=general&apiKey={NEWS_KEY}"
        r = requests.get(url).json()
        return "\n".join([a["title"] for a in r.get("articles", [])[:3]])
    except:
        return "News error."

def use_wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "No wiki result."

def use_dict(q):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{q}"
        ).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "No definition found."

def use_tavily(q):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": q}
        ).json()
        return r.get("answer", "No web result.")
    except:
        return "Web error."

# ================= UI =================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

<style>
body {
margin:0;
font-family:Arial;
background:#0b0f1a;
color:white;
display:flex;
}

.sidebar {
width:260px;
background:#111827;
height:100vh;
padding:15px;
}

.chat {
flex:1;
display:flex;
flex-direction:column;
height:100vh;
}

.topbar {
padding:10px;
background:#111827;
}

.messages {
flex:1;
overflow-y:auto;
padding:20px;
}

.msg {
margin:8px;
padding:10px;
border-radius:10px;
max-width:70%;
}

.user { background:#2563eb; margin-left:auto; }
.ai { background:#1f2937; }

.inputbox {
display:flex;
padding:10px;
background:#111827;
}

input {
flex:1;
padding:10px;
}

button {
padding:10px;
}

.fade { opacity:0.6; font-size:12px; }

.badge {
background:linear-gradient(45deg,#3b82f6,#f97316);
padding:3px 6px;
border-radius:6px;
font-size:11px;
}

</style>
</head>

<body>

<div class="sidebar">
<h3>Bloxy-bot</h3>
<p class="fade">⚠ AI can make mistakes</p>

<hr>

<button onclick="mode='ai'">AI Chat</button><br>
<button onclick="mode='wiki'">Wikipedia</button><br>
<button onclick="mode='news'">News</button><br>
<button onclick="mode='math'">Math</button><br>
<button onclick="mode='web'">Web</button><br>
<button onclick="mode='dict'">Dictionary</button><br>

</div>

<div class="chat">

<div class="topbar">
<span class="badge">✔ aTg VERIFIED OWNER</span>
</div>

<div class="messages" id="box"></div>

<div class="inputbox">
<input id="input" placeholder="Message..." />
<button onclick="send()">Send</button>
</div>

</div>

<script>
let mode="ai";

async function send(){
let msg=document.getElementById("input").value;
if(!msg) return;

add(msg,"user");

let res=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,mode:mode})
});

let data=await res.json();
add(data.reply,"ai");

document.getElementById("input").value="";
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

# ================= ROUTING ENGINE =================

def router(msg, mode):

    text = msg.lower()

    # ✅ STRICT RULE: dictionary ONLY if explicitly asked
    if mode == "dict" or "define" in text or "meaning of" in text:
        return use_dict(msg)

    # math
    if mode == "math":
        return use_wolfram(msg)

    # news
    if mode == "news":
        return use_news(msg)

    # wiki
    if mode == "wiki":
        return use_wiki(msg)

    # web
    if mode == "web":
        return use_tavily(msg)

    # default AI brain
    response = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role":"user","content":msg}]
    )
    return response.choices[0].message.content

# ================= CHAT =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data["message"]
    mode = data["mode"]

    user = session.get("user","guest")

    # OWNER CHECK
    prefix = "✔ aTg (OWNER VERIFIED)" if user=="aTg" else user

    reply = router(msg, mode)

    return jsonify({"reply": f"{prefix}: {reply}"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
