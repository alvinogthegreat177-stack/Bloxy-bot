from flask import Flask, request, jsonify, render_template_string, session
from groq import Groq
import wikipedia, wolframalpha, requests, os, uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# ================= API KEYS =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
wolfram = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID", ""))

NEWS_KEY = os.getenv("NEWS_API_KEY", "")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

# ================= USERS =================
users = {
    "aTg": {"password": "admin123", "verified": True}
}

# ================= MEMORY =================
conversations = {}

# ================= USER =================
def get_user():
    u = session.get("user")
    if not u:
        return {"name": "Guest", "verified": False}
    return {"name": u, "verified": users[u]["verified"]}

# ================= TOOLS =================

def wiki(q):
    try: return wikipedia.summary(q, sentences=2)
    except: return None

def math(q):
    try: return next(wolfram.query(q).results).text
    except: return None

def news():
    try:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}").json()
        return "\n".join([a["title"] for a in r.get("articles", [])[:5]])
    except: return None

def web(q):
    try:
        r = requests.post("https://api.tavily.com/search",
        json={"api_key":TAVILY_KEY,"query":q}).json()
        return r.get("answer")
    except: return None

def dictionary(word):
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except: return None

# ================= ROUTER =================
def route(msg):
    t = msg.lower()

    if "define" in t or "meaning" in t:
        return dictionary(msg)

    if any(x in t for x in ["solve","+","-","/","equation"]):
        return math(msg)

    if "news" in t or "latest" in t:
        return news()

    if "who is" in t or "what is" in t:
        return wiki(msg)

    if "search" in t or "find" in t:
        return web(msg)

    return None

# ================= AI =================
def ai(msg):
    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role":"system","content":"Respond formally and clearly."},
                {"role":"user","content":msg}
            ]
        )
        return r.choices[0].message.content
    except Exception as e:
        print("AI ERROR:", e)
        return "⚠️ AI temporarily unavailable."

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
<title>Bloxy-bot</title>
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
.verify{
display:inline-flex;align-items:center;justify-content:center;
width:22px;height:22px;background:#f97316;color:white;
margin-left:6px;
clip-path: polygon(
50% 0%,60% 10%,75% 5%,85% 18%,100% 25%,92% 40%,100% 50%,92% 60%,
100% 75%,85% 82%,75% 95%,60% 90%,50% 100%,40% 90%,25% 95%,15% 82%,
0% 75%,8% 60%,0% 50%,8% 40%,0% 25%,15% 18%,25% 5%,40% 10%
);
}
.auth{padding:10px;}
</style>
</head>

<body>

<div class="sidebar">
<button class="newchat" onclick="newChat()">+ New Chat</button>

<div class="auth">
<input id="user" placeholder="username"><br>
<input id="pass" placeholder="password" type="password"><br>
<button onclick="signup()">Sign Up</button>
<button onclick="login()">Login</button>
<button onclick="logout()">Logout</button>
</div>

<div class="conv" id="conv"></div>
</div>

<div class="chat">
<div class="box" id="box"></div>

<div class="input">
<input id="input" placeholder="Type..." onkeypress="if(event.key==='Enter')send()">
<button onclick="send()">Send</button>
</div>

<div class="footer">Bloxy-bot can make mistakes. Double check just incase.</div>
</div>

<script>

let current="default";
let currentUser = {name:"Guest", verified:false};

async function getMe(){
let r=await fetch("/me");
currentUser=await r.json();
}

async function signup(){
await fetch("/signup",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({username:user.value,password:pass.value})});
alert("Signed up");
}

async function login(){
await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},
body:JSON.stringify({username:user.value,password:pass.value})});
getMe();
}

async function logout(){
await fetch("/logout");
currentUser={name:"Guest",verified:false};
}

function badge(){
return currentUser.verified ? "<span class='verify'>✔</span>" : "";
}

async function send(){

let msg=input.value;
if(!msg)return;

add(currentUser.name+" "+badge()+": "+msg,"user");
input.value="";

let r=await fetch("/chat",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg,id:current})});

let d=await r.json();
add("Bloxy-bot: "+d.reply,"ai");
load();
}

function add(t,c){
let d=document.createElement("div");
d.className="msg "+c;
d.innerHTML=t;
box.appendChild(d);
}

async function newChat(){
let r=await fetch("/new");
let d=await r.json();
current=d.id;
box.innerHTML="";
load();
}

async function load(){
let r=await fetch("/conversations");
let d=await r.json();
conv.innerHTML=d.map(c=>`<div class="item">${c.title}</div>`).join("");
}

getMe();
load();

</script>
</body>
</html>
"""

# ================= ROUTES =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/signup",methods=["POST"])
def signup():
    d=request.json
    if d["username"] in users:
        return jsonify({"error":"exists"})
    users[d["username"]]={"password":d["password"],"verified":False}
    return jsonify({"ok":True})

@app.route("/login",methods=["POST"])
def login():
    d=request.json
    if d["username"] in users and users[d["username"]]["password"]==d["password"]:
        session["user"]=d["username"]
        return jsonify({"ok":True})
    return jsonify({"error":"invalid"})

@app.route("/logout")
def logout():
    session.pop("user",None)
    return jsonify({"ok":True})

@app.route("/me")
def me():
    return jsonify(get_user())

@app.route("/new")
def new():
    cid=str(uuid.uuid4())
    conversations[cid]={"title":"New Chat","messages":[]}
    return jsonify({"id":cid})

@app.route("/chat",methods=["POST"])
def chat():
    d=request.json
    msg=d["message"]
    cid=d["id"]

    if cid not in conversations:
        conversations[cid]={"title":"New Chat","messages":[]}

    conv=conversations[cid]

    if len(conv["messages"])==0:
        conv["title"]=msg[:20]

    reply=get_response(msg)

    conv["messages"].append({"role":"user","text":msg})
    conv["messages"].append({"role":"ai","text":reply})

    return jsonify({"reply":reply})

@app.route("/conversations")
def convs():
    return jsonify([{"id":k,"title":v["title"]} for k,v in conversations.items()])

# ================= RUN =================
if __name__=="__main__":
    app.run()
