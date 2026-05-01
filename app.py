from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# 🔐 API KEY (Render Environment Variable)
API_KEY = os.environ.get("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")

# 🧠 CHAT STORAGE
chats = {
    "🤖 Bloxy-bot Chat 1": [
        {"role": "system", "content": "You are a helpful, friendly AI assistant 🙂"}
    ]
}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

<style>
body { margin:0; font-family: Arial; display:flex; }

/* SIDEBAR */
#sidebar {
    width: 240px;
    background: #202123;
    color: white;
    height: 100vh;
    padding: 10px;
    transition: 0.3s;
}

.hidden {
    width: 0;
    padding: 0;
    overflow: hidden;
}

.chat-item {
    padding: 10px;
    border-radius: 6px;
    cursor: pointer;
}

.chat-item:hover {
    background:#2a2b32;
}

/* MAIN */
#main {
    flex:1;
    display:flex;
    flex-direction:column;
}

#chat {
    flex:1;
    overflow-y:auto;
    padding:20px;
    background:#f7f7f7;
}

.msg {
    max-width:60%;
    padding:10px;
    margin:8px;
    border-radius:10px;
}

.user { background:#d1e7ff; margin-left:auto; }
.ai { background:white; }

#inputArea {
    display:flex;
    padding:10px;
    background:white;
}

#msg {
    flex:1;
    padding:10px;
}

button {
    padding:10px;
    margin-left:5px;
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

<div id="inputArea">
    <input id="msg" placeholder="Type message...">
    <button onclick="send()">Send</button>
</div>

</div>

<script>

let currentChat = "";

async function loadChats() {
    const res = await fetch("/chats");
    const data = await res.json();

    let list = document.getElementById("chatList");
    list.innerHTML = "";

    data.chats.forEach(c => {
        list.innerHTML += `<div class="chat-item" onclick="switchChat('${c}')">${c}</div>`;
    });

    if (!currentChat && data.chats.length > 0) {
        currentChat = data.chats[0];
    }
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

    let chat = document.getElementById("chat");

    chat.innerHTML += `<div class='msg user'>${msg}</div>`;

    const res = await fetch("/ai", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({message: msg, chat: currentChat})
    });

    const data = await res.json();

    chat.innerHTML += `<div class='msg ai'>${data.response}</div>`;

    document.getElementById("msg").value = "";
    chat.scrollTop = chat.scrollHeight;
}

document.addEventListener("keydown", function(e){
    if(e.key === "Enter") send();
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
    name = f"🤖 Bloxy-bot Chat {len(chats)+1}"
    chats[name] = chats[list(chats.keys())[0]][:1]
    return jsonify({"name": name})

@app.route("/ai", methods=["POST"])
def ai():
    data = request.json
    user_message = data["message"]
    chat_name = data["chat"]

    chats[chat_name].append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": chats[chat_name][-10:]
            }
        )

        result = response.json()
        reply = result["choices"][0]["message"]["content"]

    except Exception:
        reply = "⚠️ AI error. Check API key or try again."

    chats[chat_name].append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})
