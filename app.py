from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os, wikipedia, wolframalpha, requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY","dev")

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
wolfram = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID"))

NEWS = os.getenv("NEWS_API_KEY")
TAVILY = os.getenv("TAVILY_API_KEY")

# ================= EMOJI ENGINE =================

def emoji_context(text, mode):
    t = text.lower()

    if mode == "math":
        return ""  # no emojis in math

    if "error" in t:
        return "⚠️ "

    if "success" in t or "correct" in t:
        return "✅ "

    if "warning" in t:
        return "⚠️ "

    if mode == "wiki":
        return "📚 "

    if mode == "news":
        return "📰 "

    if mode == "ai":
        return "🤖 "

    return ""

# ================= FORMATTING =================

def format_response(text):
    lines = text.split("\n")
    out = []

    for l in lines:
        l = l.strip()

        # enforce vertical numbering style
        if len(l) > 2 and l[0].isdigit() and "." in l[:3]:
            num = l.split(".")[0]
            content = l.split(".",1)[1].strip()
            out.append(f"{num}\n{content}\n")
        else:
            out.append(l)

    return "\n".join(out)

# ================= AI =================

def ai(msg):
    r = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role":"system",
                "content":"""
You are Bloxy-bot.
Rules:
- Always respond in formal diplomatic tone.
- Use vertical formatting for numbered points.
- Be structured and clear.
- Do not use emojis unless system allows.
"""
            },
            {"role":"user","content":msg}
        ]
    )
    return r.choices[0].message.content

# ================= TOOLS =================

def wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "Wikipedia result not found."

def math(q):
    try:
        return next(wolfram.query(q).results).text
    except:
        return "Math error."

def news(q):
    try:
        url=f"https://newsapi.org/v2/top-headlines?category=general&apiKey={NEWS}"
        r=requests.get(url).json()
        return "\n".join([a["title"] for a in r.get("articles",[])[:3]])
    except:
        return "News error."

# ================= ROUTER =================

def router(msg, mode):

    base = ""

    # tool routing
    if mode == "math":
        base = math(msg)

    elif mode == "wiki":
        base = wiki(msg)

    elif mode == "news":
        base = news(msg)

    else:
        base = ai(msg)

    # emoji layer
    em = emoji_context(base, mode)

    return em + format_response(base)

# ================= UI =================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot Pro</title>

<style>
body{
margin:0;
font-family:Arial;
background:#0b0f1a;
color:white;
display:flex;
height:100vh;
}

.sidebar{
width:280px;
background:#111827;
padding:10px;
display:flex;
flex-direction:column;
justify-content:space-between;
}

.account{
background:#0f172a;
padding:10px;
border-radius:8px;
}

.badge{
background:linear-gradient(90deg,#3b82f6,#f97316);
padding:4px 8px;
border-radius:6px;
font-size:11px;
}

.chat{
flex:1;
display:flex;
flex-direction:column;
}

.box{
flex:1;
overflow-y:auto;
padding:15px;
}

.msg{
padding:10px;
margin:8px;
border-radius:10px;
max-width:75%;
white-space:pre-line;
}

.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f2937;}

.input{
display:flex;
padding:10px;
background:#111827;
}

input{
flex:1;
padding:10px;
border:none;
outline:none;
}

button{
padding:10px;
background:#2563eb;
color:white;
border:none;
}

.footer{
text-align:center;
font-size:12px;
opacity:0.6;
padding:5px;
}
</style>
</head>

<body>

<div class="sidebar">
<div>
<button onclick="newChat()">+ New Chat</button>
</div>

<div class="account">
<div>✔ aTg</div>
<div class="badge">✔ VERIFIED</div>
</div>
</div>

<div class="chat">

<div class="box" id="box"></div>

<div class="input">
<input id="input" onkeypress="key(event)">
<button onclick="send()">Send</button>
</div>

<div class="footer">
Bloxy-bot can make mistakes. Double check important information.
</div>

</div>

<script>
let mode="ai";

function key(e){
if(e.key==="Enter") send();
}

async function send(){

let input=document.getElementById("input");
let msg=input.value;
if(!msg)return;

add(msg,"user");
input.value="";

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,mode:mode})
});

let d=await r.json();
add(d.reply,"ai");
}

function add(t,c){
let d=document.createElement("div");
d.className="msg "+c;
d.innerText=t;
document.getElementById("box").appendChild(d);
}
</script>

</body>
</html>
"""

# ================= ROUTE =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat",methods=["POST"])
def chat():

    data=request.json
    msg=data["message"]
    mode=data.get("mode","ai")

    reply=router(msg,mode)

    return jsonify({"reply":reply})

# ================= RUN =================
if __name__=="__main__":
    app.run()
