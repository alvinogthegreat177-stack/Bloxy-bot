from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# 🔐 API KEY (Render environment variable)
API_KEY = os.environ.get("GROQ_API_KEY")

print("🔥 GROQ KEY LOADED:", "FOUND" if API_KEY else "MISSING")

# 🧠 System prompt (THIS FIXES LONG/UGLY ANSWERS)
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Bloxy-bot, a modern ChatGPT-style assistant.

Rules:
- Be short, clear, and direct
- No long paragraphs
- No websites unless necessary
- No knowledge cutoff talk
- Answer like a real chat assistant
- Use light emojis only
"""
}

# 🧠 Memory per chat
chats = {
    "🤖 New dialogue": [SYSTEM_PROMPT]
}

# 🌐 UI (ChatGPT-style dark + sidebar)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
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
#sidebar {
    width:260px;
    background:#1a1a1a;
    padding:10px;
    overflow-y:auto;
}

.chat-item {
    padding:10px;
    border-radius:8px;
    cursor:pointer;
}
.chat-item:hover {
    background:#2a2a2a;
}

/* MAIN */
#main {
    flex:1;
    display:flex;
    flex-direction:column;
}

/* CHAT */
#chat {
    flex:1;
    padding:15px;
    overflow-y:auto;
}

.msg {
    padding:12px;
    margin:8px;
    border-radius:12px;
    max-width:70%;
}

.user {
    background:#2b6fff;
    margin-left:auto;
}

.ai {
    background:#2a2a2a;
}

/* INPUT */
#input {
    display:flex;
    padding:10px;
    background:#1a1a1a;
}

#msg {
    flex:1;
    padding:10px;
    border-radius:8px;
    border:none;
    outline:none;
}

button {
    margin-left:8px;
    padding:10px;
    border-radius:8px;
    border:none;
    background:#2b6fff;
    color:white;
    cursor:pointer;
}
</style>
</head>

<body>

<div id="sidebar">
    <button onclick="newChat()">+ New Chat</button>
    <div id="chatList"></div>
</div>

<div id="main">

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Type message..." />
<button onclick="send()">Send</button>
</div>

</div>

<script>

let currentChat = "🤖 Chat 1";

async function loadChats() {
    const res = await fetch("/chats");
    const data = await res.json();

    let list = document.getElementById("chatList");
    list.innerHTML = "";

    data.chats.forEach(c => {
        list.innerHTML += `
        <div class="chat-item" onclick="switchChat('${c}')">
            ${c}
        </div>`;
    });
}

function switchChat(name) {
    currentChat = name;
    document.getElementById("chat").innerHTML = "";
}

async function newChat() {
    await fetch("/new_chat", {method:"POST"});
    loadChats();
}

async function send() {
    let msg = document.getElementById("msg").value;
    if (!msg) return;

    document.getElementById("chat").innerHTML +=
        "<div class='msg user'>" + msg + "</div>";

    const res = await fetch("/ai", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({message: msg, chat: currentChat})
    });

    const data = await res.json();

    document.getElementById("chat").innerHTML +=
        "<div class='msg ai'>" + data.response + "</div>";

    document.getElementById("msg").value = "";
    document.getElementById("chat").scrollTop =
        document.getElementById("chat").scrollHeight;
}

document.addEventListener("keydown", e => {
    if (e.key === "Enter") send();
});

loadChats();

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chats")
def get_chats():
    return jsonify({"chats": list(chats.keys())})

@app.route("/new_chat", methods=["POST"])
def new_chat():
    name = f"🤖 Chat {len(chats)+1}"
    chats[name] = [SYSTEM_PROMPT]
    return jsonify({"ok": True})

@app.route("/ai", methods=["POST"])
def ai():
    if not API_KEY:
        return jsonify({"response": "⚠️ Missing API key in Render environment"})

    data = request.json
    msg = data["message"]
    chat = data["chat"]

    chats[chat].append({"role": "user", "content": msg})

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": chats[chat][-10:]
        }
    )

    res = response.json()

    if "choices" not in res:
        return jsonify({"response": "⚠️ API Error: " + str(res)})

    reply = res["choices"][0]["message"]["content"]

    chats[chat].append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})
