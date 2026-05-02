from flask import Flask, request, jsonify, render_template_string
import os
import requests

# ✅ FIX (this was missing)
app = Flask(__name__)

# 🔐 ENV VARIABLES
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

print("GROQ KEY:", "FOUND" if GROQ_API_KEY else "MISSING")
print("TAVILY KEY:", "FOUND" if TAVILY_API_KEY else "MISSING")

# 🧠 SAFE TAVILY INIT
tavily = None
if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
    except:
        tavily = None

# 🧠 MEMORY
chats = {}

SYSTEM = {
    "role": "system",
    "content": "You are Bloxy-bot. Be clear, helpful, and short."
}

# 🌐 WIKIPEDIA
def wikipedia_search(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        r = requests.get(url, timeout=5)
        return r.json().get("extract", "")
    except:
        return ""

# 🌐 TAVILY
def web_search(query):
    if not tavily:
        return ""
    try:
        res = tavily.search(query=query, search_depth="basic", max_results=3)
        return "\n".join([r.get("content", "") for r in res.get("results", [])])
    except:
        return ""

# 🧠 GROQ
def ask_groq(messages):
    if not GROQ_API_KEY:
        return "⚠️ Missing GROQ_API_KEY"

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages
            },
            timeout=10
        )

        data = res.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

# 🎨 UI
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

function switchChat(c){
 current=c;
 document.getElementById("chat").innerHTML="";
}

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
    chats[name] = [SYSTEM]
    return jsonify({"ok": True})

@app.route("/ai", methods=["POST"])
def ai():
    data = request.json
    msg = data["message"]
    chat = data["chat"]

    if chat not in chats:
        chats[chat] = [SYSTEM]

    # 🌐 SEARCH FLOW
    web_info = web_search(msg)
    if not web_info:
        web_info = wikipedia_search(msg)

    final = f"""
User: {msg}

Info:
{web_info}
"""

    chats[chat].append({"role": "user", "content": final})

    reply = ask_groq(chats[chat][-10:])

    chats[chat].append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run()
