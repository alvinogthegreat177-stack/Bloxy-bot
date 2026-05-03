import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from groq import Groq
from tavily import TavilyClient
import wikipedia
import requests

app = Flask(__name__)
CORS(app)

# 🔑 KEYS
groq = Groq(api_key="YOUR_GROQ_API_KEY")
tavily = TavilyClient(api_key="YOUR_TAVILY_API_KEY")

# --------------------------
# 🧠 GROQ (MAIN BRAIN)
# --------------------------
def groq_ai(message):
    res = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are Bloxy-bot, a smart AI assistant."},
            {"role": "user", "content": message}
        ]
    )
    return res.choices[0].message.content

# --------------------------
# 📚 WIKIPEDIA (FACTS)
# --------------------------
def wiki(query):
    try:
        return wikipedia.summary(query, sentences=2)
    except:
        return None

# --------------------------
# 🌐 TAVILY (SEARCH)
# --------------------------
def tavily_search(query):
    try:
        res = tavily.search(query=query)
        return res["results"][0]["content"]
    except:
        return None

# --------------------------
# 📖 DICTIONARY (NOT MAIN BRAIN)
# --------------------------
def dictionary(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# --------------------------
# 🤖 SMART ROUTER (PRIORITY SYSTEM)
# --------------------------
def agent(message):
    msg = message.lower()

    # 📖 DICTIONARY FIRST (ONLY IF USER WANTS DEFINITIONS)
    if msg.startswith("define "):
        word = msg.replace("define ", "")
        return dictionary(word) or groq_ai(message)

    # 📚 WIKIPEDIA SECOND
    wiki_result = wiki(message)
    if wiki_result and ("who is" in msg or "what is" in msg):
        return wiki_result

    # 🌐 TAVILY THIRD (SEARCH / CURRENT INFO)
    if "latest" in msg or "search" in msg:
        return tavily_search(message) or groq_ai(message)

    # 🧠 GROQ ALWAYS DEFAULT BRAIN
    return groq_ai(message)

# --------------------------
# 🌐 API ENDPOINT
# --------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    reply = agent(message)
    return jsonify({"reply": reply})

# --------------------------
# 🎨 WEB UI WITH SIDEBAR
# --------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot AI</title>
<style>
body {
    margin:0;
    font-family:Arial;
    display:flex;
    height:100vh;
    background:#0f0f0f;
    color:white;
}

/* SIDEBAR */
.sidebar {
    width:240px;
    background:#1a1a1a;
    padding:20px;
}

.sidebar h2 {
    color:#00b7ff;
}

.fade {
    opacity:0.5;
    font-size:13px;
    margin-top:10px;
}

/* CHAT AREA */
.chat {
    flex:1;
    display:flex;
    flex-direction:column;
}

.messages {
    flex:1;
    padding:20px;
    overflow-y:auto;
}

.input {
    display:flex;
}

input {
    flex:1;
    padding:15px;
    border:none;
    outline:none;
}

button {
    width:120px;
    border:none;
    background:#00b7ff;
    color:white;
}

.msg {
    margin:8px 0;
}

.user { color:#00b7ff; }
.bot { color:white; }
</style>
</head>

<body>

<div class="sidebar">
<h2>Bloxy-bot</h2>

<div class="fade">🧠 Groq = Main Brain</div>
<div class="fade">📚 Wikipedia = Facts</div>
<div class="fade">🌐 Tavily = Search</div>
<div class="fade">📖 Dictionary = Definitions</div>
<div class="fade">⚡ Smart Routing System</div>
</div>

<div class="chat">

<div class="messages" id="chat"></div>

<div class="input">
<input id="msg" placeholder="Type message...">
<button onclick="send()">Send</button>
</div>

</div>

<script>
async function send(){
    let msg = document.getElementById("msg").value;
    let chat = document.getElementById("chat");

    chat.innerHTML += "<div class='msg user'>You: "+msg+"</div>";

    let res = await fetch("/chat", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message:msg})
    });

    let data = await res.json();

    chat.innerHTML += "<div class='msg bot'>Bot: "+data.reply+"</div>";

    document.getElementById("msg").value = "";
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return HTML

# --------------------------
# 🚀 RUN SERVER
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
