


API_KEY = "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"

app = Flask(__name__)

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

/* CHAT ITEM */
.chat-item {
    padding: 10px;
    border-radius: 6px;
    display:flex;
    justify-content: space-between;
    align-items:center;
}

.chat-item:hover {
    background:#2a2b32;
}

.menu {
    display:none;
    cursor:pointer;
}

.chat-item:hover .menu {
    display:block;
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

/* INPUT */
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

/* TOP BAR */
#topbar {
    background:#eee;
    padding:10px;
}

</style>
</head>

<body>

<div id="sidebar">
    <button onclick="newChat()">+ New Chat</button>
    <div id="chatList"></div>
</div>

<div id="main">

<div id="topbar">
    <button onclick="toggleSidebar()">☰</button>
</div>

<div id="chat"></div>

<div id="inputArea">
    <input id="msg" placeholder="Type message...">
    <button onclick="send()">Send</button>
</div>

</div>

<script>

let currentChat = Object.keys({})[0];

async function loadChats() {
    const res = await fetch("/chats");
    const data = await res.json();

    let list = document.getElementById("chatList");
    list.innerHTML = "";

    data.chats.forEach(c => {
        list.innerHTML += `
        <div class="chat-item">
            <span onclick="switchChat('${c}')">${c}</span>
            <span class="menu" onclick="openMenu('${c}')">⋮</span>
        </div>`;
    });

    if (!currentChat && data.chats.length > 0) {
        currentChat = data.chats[0];
    }
}

function openMenu(name) {
    let action = prompt("Type: rename or delete");

    if (action === "rename") {
        let newName = prompt("New name:");
        fetch("/rename", {
            method:"POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({old:name,new:newName})
        }).then(loadChats);
    }

    if (action === "delete") {
        fetch("/delete", {
            method:"POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({name:name})
        }).then(loadChats);
    }
}

function switchChat(name) {
    currentChat = name;
    document.getElementById("chat").innerHTML = "";
}

async function newChat() {
    await fetch("/new_chat",{method:"POST"});
    loadChats();
}

function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("hidden");
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
    if(e.key==="Enter") send();
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

@app.route("/rename", methods=["POST"])
def rename():
    data = request.json
    chats[data["new"]] = chats.pop(data["old"])
    return jsonify({"ok": True})

@app.route("/delete", methods=["POST"])
def delete():
    name = request.json["name"]
    if len(chats) > 1:
        chats.pop(name)
    return jsonify({"ok": True})

@app.route("/ai", methods=["POST"])
def ai():
    data_req = request.json
    user_message = data_req["message"]
    chat_name = data_req["chat"]

    chats[chat_name].append({"role":"user","content":user_message})

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model":"llama-3.3-70b-versatile",
            "messages": chats[chat_name][-10:]
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]

    chats[chat_name].append({"role":"assistant","content":reply})

    return jsonify({"response": reply})


