from flask import Flask, request, jsonify, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
import wikipedia, requests, os, uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change")

# ================= APIs =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

NEWS_KEY = os.getenv("NEWS_API_KEY", "")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")
WOLFRAM_APP = os.getenv("WOLFRAM_APP_ID", "")

# ================= USERS (hashed auth) =================
users = {
    "aTg": {
        "password": generate_password_hash("alvintheultimedev17.og"),
        "verified": True
    }
}

# ================= MEMORY =================
conversations = {}

# ================= USER =================
def get_user():
    u = session.get("user")
    if not u or u not in users:
        return {"name": "Guest", "verified": False}
    return {"name": u, "verified": users[u]["verified"]}

# ================= TOOLS =================
def wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return None

def dictionary(word):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        ).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

def tavily(q):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": q}
        ).json()
        return r.get("results", [{}])[0].get("content")
    except:
        return None

def news():
    try:
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}&country=us"
        ).json()
        return "\n".join([a["title"] for a in r.get("articles", [])[:5]])
    except:
        return None

def wolfram(q):
    try:
        import wolframalpha
        client = wolframalpha.Client(WOLFRAM_APP)
        res = next(client.query(q).results).text
        return res
    except:
        return None

# ================= ROUTER =================
def route(msg):
    t = msg.lower()

    if t.startswith("define"):
        return dictionary(msg.replace("define","").strip())

    if any(x in t for x in ["who is", "what is"]):
        return wiki(msg)

    if any(x in t for x in ["solve", "+", "-", "/", "equation"]):
        return wolfram(msg)

    if "news" in t:
        return news()

    if "search" in t:
        return tavily(msg)

    return None

# ================= AI (FIXED RELIABILITY) =================
def ai(msg):
    try:
        res = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Bloxy-bot, a helpful AI assistant. Always respond clearly."},
                {"role": "user", "content": msg}
            ],
            temperature=0.7
        )
        return res.choices[0].message.content
    except Exception as e:
        print("AI ERROR:", e)
        return "⚠️ AI temporarily unavailable. Please try again."

def get_response(msg):
    tool = route(msg)
    if tool:
        return tool
    return ai(msg)

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot AI</title>

<style>
body{margin:0;font-family:Arial;background:#0b0f1a;color:white;display:flex;height:100vh;}
.sidebar{width:260px;background:#111827;display:flex;flex-direction:column;}
.newchat{margin:10px;padding:10px;background:#2563eb;color:white;border:none;border-radius:6px;cursor:pointer;}
.conv{flex:1;overflow-y:auto;padding:10px;}
.item{padding:8px;margin:5px;background:#1f2937;border-radius:6px;cursor:pointer;}
.chat{flex:1;display:flex;flex-direction:column;}
.box{flex:1;overflow-y:auto;padding:15px;}
.msg{padding:10px;margin:8px;border-radius:10px;max-width:75%;white-space:pre-line;}
.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f2937;}
.input{display:flex;padding:10px;background:#111827;}
input{flex:1;padding:10px;border:none;outline:none;}
button{padding:10px;background:#2563eb;color:white;border:none;}
.footer{text-align:center;font-size:12px;opacity:0.6;padding:5px;}
.badge{width:16px;height:16px;margin-left:6px;vertical-align:middle;}
.userpanel{position:fixed;bottom:10px;left:10px;background:#1f2937;padding:10px;border-radius:8px;display:flex;align-items:center;gap:6px;}
</style>
</head>

<body>

<div class="sidebar">
<button class="newchat" onclick="newChat()">+ New Chat</button>
<div class="conv" id="conv"></div>
</div>

<div class="chat">
<div class="box" id="box"></div>

<div class="input">
<input id="input" placeholder="Type..." onkeypress="if(event.key==='Enter')send()">
<button onclick="send()">Send</button>
</div>

<div class="footer">Bloxy-bot may make mistakes.</div>
</div>

<div class="userpanel" id="userpanel">Guest</div>

<script>

let current="default";
let user={name:"Guest",verified:false};

const badge=`<svg class="badge" viewBox="0 0 24 24" fill="#22c55e">
<path d="M12 2l2.9 6.6L22 9.3l-5 5 1.2 7.2L12 18l-6.2 3.5L7 14.3 2 9.3l7.1-0.7L12 2z"/>
<path d="M10.5 12.5l1.5 1.5 3-3" stroke="white" stroke-width="2" fill="none"/>
</svg>`;

async function getMe(){
 let r=await fetch("/me");
 user=await r.json();
 update();
}

function update(){
 userpanel.innerHTML=user.name+(user.verified?badge:"");
}

async function send(){
 let msg=input.value;
 if(!msg)return;

 add(user.name+": "+msg,"user");
 input.value="";

 let r=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg,id:current})});
 let d=await r.json();
 add("Bloxy-bot: "+d.reply,"ai");
}

function add(t,c){
 let d=document.createElement("div");
 d.className="msg "+c;
 d.innerHTML=t;
 box.appendChild(d);
 box.scrollTop=box.scrollHeight;
}

async function newChat(){
 let r=await fetch("/new");
 let d=await r.json();
 current=d.id;
 box.innerHTML="";
}

getMe();

</script>
</body>
</html>
"""

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/me")
def me():
    return jsonify(get_user())

@app.route("/new")
def new():
    cid=str(uuid.uuid4())
    conversations[cid]={"messages":[]}
    return jsonify({"id":cid})

@app.route("/chat",methods=["POST"])
def chat():
    d=request.json
    msg=d.get("message","")

    reply=get_response(msg)

    return jsonify({"reply":reply})

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
