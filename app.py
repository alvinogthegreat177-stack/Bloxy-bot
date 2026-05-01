from flask import Flask, request, jsonify, render_template_string
import os
import requests
from tavily import TavilyClient

app = Flask(__name__)

# 🔐 KEYS (Render environment variables)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 🧠 AI + Search clients
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# 🧠 CHAT MEMORY
chats = {}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are Bloxy-bot. Be clear, helpful, and use provided web data when available."
}

# 🌐 WIKIPEDIA FALLBACK
def wikipedia_search(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        r = requests.get(url)
        data = r.json()
        return data.get("extract", "")
    except:
        return ""

# 🌐 TAVILY SEARCH (LIVE WEB)
def web_search(query):
    try:
        res = tavily.search(query=query, search_depth="basic", max_results=3)
        results = [r.get("content", "") for r in res.get("results", [])]
        return "\n".join(results)
    except:
        return ""

# 🧠 GROQ CALL
def ask_groq(messages):
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return res.json()

# 🎨 UI (ChatGPT-style)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body{margin:0;font-family:Arial;display:flex;height:100vh}
#sidebar{width:250px;background:#111;color:white;padding:10px}
.chat-item{padding:10px;cursor:pointer}
.chat-item:hover{background:#333}
#main{flex:1;display:flex;flex-direction:column}
#chat{flex:1;overflow-y:auto;padding:10px;background:#f4f4f4}
.msg{padding:10px;margin:5px;border-radius:8px;max-width:70%}
.user{background:#4a90e2;color:white;margin-left:auto}
.ai{background:white}
#input{display:flex;padding:10px}
input{flex:1;padding:10px}
button{margin-left:10px}
</style>
</head>
<body>

<div id="sidebar">
<button onclick="newChat()">+ New Chat</button>
<div id="list"></div>
</div>

<div id="main">
<div id="chat"></div>
<div id="input">
<input id="msg" placeholder="Type..." />
<button onclick="send()">Send</button>
</div>
</div>

<script>
let current="Chat 1";

async function load(){
 let r=await fetch("/chats");
 let d=await r.json();
 let list=document.getElementById("list");
 list.innerHTML="";
 d.chats.forEach(c=>{
   list.innerHTML+=`<div class='chat-item' onclick="switchChat('${c}')">${c}</div>`;
 });
}

function switchChat(c){current=c;document.getElementById("chat").innerHTML=""}

async function newChat(){
 await fetch("/new_chat",{method:"POST"});
 load();
}

async function send(){
 let m=document.getElementById("msg").value;
 if(!m)return;

 document.getElementById("chat").innerHTML+=`<div class='msg user'>${m}</div>`;

 let r=await fetch("/ai",{
 method:"POST",
 headers:{"Content-Type":"application/json"},
 body:JSON.stringify({message:m,chat:current})
 });

 let d=await r.json();
 document.getElementById("chat").innerHTML+=`<div class='msg ai'>${d.response}</div>`;
 document.getElementById("msg").value="";
}

load();
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
    name = f"Chat {len(chats)+1}"
    chats[name] = [SYSTEM_PROMPT]
    return jsonify({"ok": True})

@app.route("/ai", methods=["POST"])
def ai():
    data = request.json
    msg = data["message"]
    chat = data["chat"]

    if chat not in chats:
        chats[chat] = [SYSTEM_PROMPT]

    # 🌐 STEP 1: TRY LIVE WEB (TAVILY)
    web_info = web_search(msg)

    # 🌐 STEP 2: IF EMPTY → USE WIKIPEDIA
    if not web_info:
        web_info = wikipedia_search(msg)

    # 🧠 STEP 3: BUILD PROMPT
    final_msg = f"""
User question: {msg}

Web data:
{web_info}
"""

    chats[chat].append({"role": "user", "content": final_msg})

    # 🧠 STEP 4: CALL GROQ
    response = ask_groq(chats[chat][-10:])

    try:
        reply = response["choices"][0]["message"]["content"]
    except:
        reply = str(response)

    chats[chat].append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run()

   
