from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# 💾 DATABASE
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM (THIS FIXES YOUR FORMATTING ISSUE)
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

RULES:
- Always format lists vertically (one item per line)
- Use bullet points or numbering properly
- Never write lists in a single paragraph
- Be clear, clean, and structured
- When giving opinions, separate each point clearly
- Do NOT respond like a dictionary unless explicitly asked
"""
}

# 📖 DICTIONARY (NOW CONTROLLED)
def dictionary_lookup(query):
    triggers = ["define", "meaning", "what does", "definition"]
    if not any(t in query.lower() for t in triggers):
        return None

    try:
        word = query.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if r.status_code == 200:
            return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# 🤖 GROQ
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.5
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 ROUTER (FIXED)
def smart_answer(query, history):

    # ONLY use dictionary when appropriate
    d = dictionary_lookup(query)
    if d:
        return f"📖 Definition:\n{d}"

    # Otherwise use AI normally
    return groq([SYSTEM] + history + [{"role": "user", "content": query}])


# 🎨 UI (INLINE THINKING KEPT)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}
#chat{flex:1;padding:20px;overflow-y:auto}
.msg{max-width:70%;padding:12px;margin:6px;border-radius:10px;white-space:pre-wrap}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;background:#2563eb;color:white;border:none;padding:10px}
</style>
</head>

<body>

<div style="flex:1;display:flex;flex-direction:column">
<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot 🤖...">
<button onclick="send()">Send</button>
</div>
</div>

<script>

const chat=document.getElementById("chat");

/* ADD MESSAGE */
function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
return d;
}

/* STREAM */
function streamTo(el,text){
let i=0;
let t=setInterval(()=>{
el.textContent=text.slice(0,i++);
if(i>text.length) clearInterval(t);
},8);
}

/* SEND */
async function send(){
let input=document.getElementById("msg");
let msg=input.value;
if(!msg) return;

input.value="";

add("user",msg);

/* INLINE THINKING */
let aiMsg = add("ai","Bloxy-bot is thinking... 🤖");

let r=await fetch("/ai",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg})
});

let d=await r.json();

aiMsg.textContent="";
streamTo(aiMsg,d.response);
}

document.getElementById("msg").addEventListener("keypress",e=>{
if(e.key==="Enter"){e.preventDefault();send();}
});

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ai", methods=["POST"])
def ai():
    msg = request.json["message"]
    reply = smart_answer(msg, [])
    return jsonify({"response": reply})

if __name__ == "__main__":
    app.run()
