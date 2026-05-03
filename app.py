import os
import requests
from flask import Flask, render_template_string
from flask_socketio import SocketIO

# =====================================================
# SAFE INIT
# =====================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "bloxy_v2"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# =====================================================
# OPTIONAL KEYS
# =====================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# =====================================================
# AI FUNCTIONS (SAFE)
# =====================================================

def groq_ai(msg):
    if not GROQ_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are Bloxy-bot."},
                    {"role": "user", "content": msg}
                ]
            }
        )
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None


def tavily(msg):
    if not TAVILY_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": msg,
                "max_results": 2
            }
        )
        data = r.json().get("results", [])
        return " ".join([x["content"] for x in data])
    except:
        return None


def wiki(msg):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{msg}"
        )
        return r.json().get("extract")
    except:
        return None

# =====================================================
# AI ENGINE (SAFE ROUTING)
# =====================================================

def ai_engine(msg):

    web = tavily(msg)
    if web:
        return "🌐 Web:\n" + web

    ai = groq_ai(msg)
    if ai:
        return ai

    w = wiki(msg)
    if w:
        return "📚 Wikipedia:\n" + w

    return f"You said: {msg}"

# =====================================================
# SOCKET HANDLER
# =====================================================

@socketio.on("msg")
def handle(data):
    msg = data.get("text", "")

    reply = ai_engine(msg)

    buffer = ""
    for w in reply.split():
        buffer += w + " "
        socketio.emit("reply", {"text": buffer})
        socketio.sleep(0.02)

# =====================================================
# SIMPLE UI (SAFE TEST UI)
# =====================================================

@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{margin:0;background:#0b0f19;color:white;font-family:sans-serif;display:flex;height:100vh}
#chat{flex:1;padding:10px;overflow:auto}
.msg{margin:5px;padding:8px;border-radius:6px}
.user{background:#2563eb;margin-left:auto}
.bot{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px}
button{padding:10px}
</style>
</head>

<body>

<div id="chat"></div>

<div id="input">
<input id="msg">
<button onclick="send()">Send</button>
</div>

<script>
const socket = io();

socket.on("reply", d=>{
    add("bot", d.text);
});

function add(t,x){
let d=document.createElement("div");
d.className="msg "+t;
d.textContent=x;
chat.appendChild(d);
}

function send(){
let m=msg.value;
if(!m)return;
msg.value="";
add("user",m);
socket.emit("msg",{text:m});
}
</script>

</body>
</html>
""")

# =====================================================
# RUN SAFE
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
