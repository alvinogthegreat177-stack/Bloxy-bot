from flask import Flask, request, jsonify, session, render_template_string
from groq import Groq
import wikipedia
import wolframalpha
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ================= AI ENGINES =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
wolfram = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID"))

NEWS = os.getenv("NEWS_API_KEY")
TAVILY = os.getenv("TAVILY_API_KEY")

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>

<style>
body{margin:0;font-family:Arial;background:#0b0f1a;color:white;display:flex;height:100vh}

/* SIDEBAR */
.sidebar{
width:260px;background:#111827;padding:15px
}
.sidebar button{
width:100%;padding:10px;margin:5px;background:#1f2937;color:white;border:none;border-radius:6px
}

/* CHAT */
.chat{flex:1;display:flex;flex-direction:column}

/* TOP */
.top{padding:10px;background:#111827;display:flex;justify-content:space-between}

/* MESSAGES */
.box{flex:1;overflow-y:auto;padding:15px}
.msg{padding:10px;margin:8px;border-radius:10px;max-width:70%}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f2937}

/* INPUT */
.input{
display:flex;padding:10px;background:#111827
}
input{flex:1;padding:10px;border:none;outline:none}
button.send{padding:10px;background:#2563eb;color:white;border:none}

/* FOOTER */
.footer{
text-align:center;font-size:12px;opacity:0.6;padding:5px
}

/* typing */
.typing{opacity:0.6;font-style:italic}
</style>
</head>

<body>

<div class="sidebar">
<h3>Bloxy-bot</h3>

<button onclick="mode='ai'">AI Chat</button>
<button onclick="mode='wiki'">Wikipedia</button>
<button onclick="mode='news'">News</button>
<button onclick="mode='math'">Math</button>
<button onclick="mode='web'">Web Search</button>
<button onclick="mode='dict'">Dictionary</button>
</div>

<div class="chat">

<div class="top">
<span>✔ aTg (Owner Verified)</span>
</div>

<div class="box" id="box"></div>

<div class="input">
<input id="input" placeholder="Message Bloxy-bot..." onkeypress="key(event)">
<button class="send" onclick="send()">Send</button>
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
if(!msg) return;

add(msg,"user");
input.value="";

add("Thinking...","ai typing");

let res=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,mode:mode})
});

let data=await res.json();

removeTyping();
add(data.reply,"ai");
}

function add(text,type){
let d=document.createElement("div");
d.className="msg "+type;
d.innerText=text;
document.getElementById("box").appendChild(d);
scroll();
}

function removeTyping(){
document.querySelectorAll(".typing").forEach(e=>e.remove());
}

function scroll(){
let box=document.getElementById("box");
box.scrollTop=box.scrollHeight;
}
</script>

</body>
</html>
"""

# ================= TOOL FUNCTIONS =================

def wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "No wiki result."

def math(q):
    try:
        res = wolfram.query(q)
        return next(res.results).text
    except:
        return "Math error."

def news(q):
    try:
        url=f"https://newsapi.org/v2/top-headlines?category=general&apiKey={NEWS}"
        r=requests.get(url).json()
        return "\n".join([a["title"] for a in r.get("articles",[])[:3]])
    except:
        return "News error."

def dictionary(q):
    try:
        r=requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{q}").json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "No definition."

def web(q):
    try:
        r=requests.post("https://api.tavily.com/search",
        json={"api_key":TAVILY,"query":q}).json()
        return r.get("answer","No result.")
    except:
        return "Web error."

# ================= ROUTER =================

def router(msg,mode):

    text=msg.lower()

    # STRICT RULE (your requirement)
    if mode=="dict" or "define" in text or "meaning" in text:
        return dictionary(msg)

    if mode=="math":
        return math(msg)

    if mode=="wiki":
        return wiki(msg)

    if mode=="news":
        return news(msg)

    if mode=="web":
        return web(msg)

    # MAIN BRAIN (Groq)
    try:
        r=groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role":"user","content":msg}]
        )
        return r.choices[0].message.content
    except:
        return "AI error."

# ================= CHAT =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat",methods=["POST"])
def chat():
    data=request.json
    msg=data["message"]
    mode=data["mode"]

    user=session.get("user","guest")

    prefix="✔ aTg (OWNER VERIFIED)" if user=="aTg" else user

    reply=router(msg,mode)

    return jsonify({"reply":f"{prefix}: {reply}"})

# ================= RUN =================
if __name__=="__main__":
    app.run()
