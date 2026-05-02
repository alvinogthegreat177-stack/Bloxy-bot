from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 💾 DB
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Rules:
- Always respond in structured format
- Use vertical lists
- Never dump raw web pages
- Be clean and readable
"""
}

# 📖 DICTIONARY (SAFE)
def dictionary_lookup(query):
    if not any(x in query.lower() for x in ["define","meaning","what is"]):
        return None
    try:
        word = query.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if r.status_code == 200:
            return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# 📚 WIKIPEDIA
def wikipedia(query):
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}")
        if r.status_code == 200:
            return r.json().get("extract")
    except:
        return None

# 🌐 TAVILY
def tavily(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        results = r.json().get("results", [])
        return " ".join([r["content"] for r in results[:3]]) if results else None
    except:
        return None

# 🤖 GROQ
def groq(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.4
            }
        )

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ AI error: {str(e)}"

# 🧠 ROUTER (FIXED LOGIC)
def smart_answer(query, history):

    q = query.lower().strip()

    if q in ["hi","hello","hey"]:
        return "Hello 👋\n\nHow can I help you today?"

    d = dictionary_lookup(query)
    if d:
        return f"📖 Definition:\n{d}"

    w = wikipedia(query.replace(" ","_"))
    if w:
        return f"📚 {w[:500]}..."

    t = tavily(query)
    if t:
        return groq([
            SYSTEM,
            {"role":"user","content":f"Summarize clearly in bullet points:\n\n{t}"}
        ])

    return groq([SYSTEM] + history + [{"role":"user","content":query}])


# 🎨 UI (UNCHANGED STRUCTURE)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}

#sidebar{width:260px;background:#111;display:flex;flex-direction:column}
#top{padding:15px;font-weight:bold}
.chat{padding:10px;cursor:pointer}
.chat:hover{background:#222}

#main{flex:1;display:flex;flex-direction:column}
#header{padding:15px;border-bottom:1px solid #222;font-weight:bold}
#chat{flex:1;padding:20px;overflow-y:auto}

.msg{max-width:70%;padding:12px;margin:6px;border-radius:10px;white-space:pre-wrap}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;padding:10px;background:#2563eb;color:white;border:none}

#footer{text-align:center;font-size:12px;color:#777;padding:5px}
</style>
</head>

<body>

<div id="sidebar">
<div id="top">Bloxy-bot 🤖</div>
<div id="list"></div>
</div>

<div id="main">

<div id="header">Bloxy-bot 🤖</div>
<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot...">
<button onclick="send()">Send</button>
</div>

<div id="footer">
Bloxy-bot can make mistakes. Double-check just in case.
</div>

</div>

<script>

let current=null;
const chat=document.getElementById("chat");

function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
return d;
}

function stream(el,text){
let i=0;
let t=setInterval(()=>{
el.textContent=text.slice(0,i++);
if(i>text.length) clearInterval(t);
},8);
}

/* 🔥 FIXED SEND FUNCTION */
async function send(){
let input=document.getElementById("msg");
let msg=input.value;
if(!msg) return;

input.value="";

add("user",msg);

// loading bubble
let ai=add("ai","Thinking... 🤖");

try{
let r=await fetch("/ai",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,chat:current})
});

let d=await r.json();

/* 🔥 SAFETY FIX */
if(!d.response){
ai.textContent="⚠️ No response received.";
return;
}

ai.textContent="";
stream(ai,d.response);

}catch(e){
ai.textContent="❌ Connection error.";
}
}

document.getElementById("msg").addEventListener("keypress",e=>{
if(e.key==="Enter"){e.preventDefault();send();}
});

</script>

</body>
</html>
"""

# 🌐 ROUTES
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ai", methods=["POST"])
def ai():
    try:
        data=request.json
        msg=data["message"]

        cur.execute("SELECT role,content FROM messages")
        history=[{"role":r,"content":c} for r,c in cur.fetchall()]

        reply=smart_answer(msg, history[-10:])

        if not reply:
            reply="⚠️ Empty response."

        return jsonify({"response":str(reply)})

    except Exception as e:
        return jsonify({"response":f"❌ Server error: {str(e)}"})

if __name__ == "__main__":
    app.run()
