from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests, re

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

# 🤖 SYSTEM (FORCE STRUCTURE)
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Rules:
- Always respond in clean structured format
- Use vertical lists for steps or options
- Never dump raw web pages
- Keep answers readable and concise
- Think like a helpful assistant, not a dictionary
"""
}

# 🧠 CLEAN TEXT (removes web junk)
def clean_text(text):
    text = re.sub(r"#+.*", "", text)
    text = re.sub(r"http\\S+", "", text)
    return text.strip()

# 🌐 WIKIPEDIA (SAFE SUMMARY)
def wikipedia(query):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("extract", None)
    except:
        return None

# 🌍 TAVILY (SEARCH)
def tavily(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        results = r.json().get("results", [])
        if results:
            return " ".join([r["content"] for r in results[:3]])
    except:
        return None

# 🤖 GROQ BRAIN
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.4
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 INTELLIGENCE ROUTER (FIXED CORE PROBLEM)

def smart_answer(query, history):
    q = query.lower().strip()

    # 🟢 GREETINGS
    if q in ["hi", "hello", "hey"]:
        return "Hello 👋\n\nI am Bloxy-bot. How can I help you today?"

    # 🟢 SIMPLE COMMAND DETECTION
    is_definition = any(x in q for x in ["define", "meaning", "what is"])
    is_search = any(x in q for x in ["news", "latest", "who won", "table", "standings"])

    # 📖 DICTIONARY STYLE (ONLY WHEN NEEDED)
    if is_definition:
        wiki = wikipedia(q.replace("what is", "").strip())
        if wiki:
            return f"📖 Explanation:\n\n{clean_text(wiki)[:500]}"
    
    # 🌐 SEARCH MODE
    if is_search:
        web = tavily(q)
        if web:
            summary = groq([
                SYSTEM,
                {"role":"user","content":f"Summarize clearly in bullet points:\n\n{web}"}
            ])
            return summary

    # 🤖 DEFAULT AI MODE
    return groq([SYSTEM] + history + [{"role":"user","content":query}])


# 🎨 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}

/* SIDEBAR */
#sidebar{width:260px;background:#111;display:flex;flex-direction:column}
#top{padding:15px;font-weight:bold}
.chat{padding:10px;cursor:pointer}
.chat:hover{background:#222}

/* MAIN */
#main{flex:1;display:flex;flex-direction:column}
#header{padding:15px;border-bottom:1px solid #222;font-weight:bold}
#chat{flex:1;overflow-y:auto;padding:20px}

/* MSG */
.msg{max-width:70%;padding:12px;margin:6px;border-radius:10px;white-space:pre-wrap}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}

/* INPUT */
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
button{margin-left:10px;padding:10px;background:#2563eb;color:white;border:none}

/* FOOTER */
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

async function send(){
let input=document.getElementById("msg");
let msg=input.value;
if(!msg) return;

input.value="";

add("user",msg);

// 🤖 inline thinking (NO FLICKER)
let ai=add("ai","Bloxy-bot is thinking... 🤖");

let r=await fetch("/ai",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,chat:current})
});

let d=await r.json();

ai.textContent="";
stream(ai,d.response);
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
    data=request.json
    msg=data["message"]

    cur.execute("SELECT role,content FROM messages")
    history=[{"role":r,"content":c} for r,c in cur.fetchall()]

    reply=smart_answer(msg, history[-10:])

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
