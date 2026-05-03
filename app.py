from flask import Flask, request, jsonify, render_template_string, session, Response, stream_with_context
from groq import Groq
import sqlite3
import os
import uuid
import hashlib
import requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
DB = "app.db"

# ================= DB =================

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        verified INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def current_user():
    uid = session.get("uid")
    if not uid:
        return None

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, email, verified FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    conn.close()
    return user

# ================= AUTH =================

@app.route("/signup", methods=["POST"])
def signup():
    d = request.json
    uid = str(uuid.uuid4())

    verified = 1 if d["email"] == OWNER_EMAIL else 0

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO users VALUES (?,?,?,?,?)
    """, (uid, d["username"], d["email"], hash_pw(d["password"]), verified))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/login", methods=["POST"])
def login():
    d = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=? AND password=?",
              (d["username"], hash_pw(d["password"])))

    u = c.fetchone()
    conn.close()

    if u:
        session["uid"] = u[0]
        return jsonify({"ok": True})

    return jsonify({"error": "Invalid login"})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

# ================= TOOLS =================

def wiki(q):
    try:
        import wikipedia
        return wikipedia.summary(q, sentences=2)
    except:
        return "Wikipedia error"

def math_tool(q):
    try:
        import wolframalpha
        client = wolframalpha.Client(os.getenv("WOLFRAM_APP_ID"))
        return next(client.query(q).results).text
    except:
        return "Math error"

def news():
    try:
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?apiKey={os.getenv('NEWS_API_KEY')}"
        ).json()
        return "\n".join([a["title"] for a in r["articles"][:5]])
    except:
        return "News error"

def dictionary(q):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{q}"
        ).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "Dict error"

def tavily(q):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": os.getenv("TAVILY_API_KEY"),
                "query": q
            }
        ).json()
        return r.get("answer", "No result")
    except:
        return "Tavily error"

# ================= ROUTER =================

def route(msg):
    t = msg.lower()

    if "define" in t:
        return "dict"
    if any(x in t for x in ["solve", "+", "-", "/", "="]):
        return "math"
    if "who is" in t or "what is" in t:
        return "wiki"
    if "news" in t:
        return "news"
    if "search" in t:
        return "tavily"
    return None

# ================= CHAT =================

@app.route("/chat", methods=["POST"])
def chat():
    user = current_user()
    if not user:
        return "NOT LOGGED IN"

    msg = request.json["message"]
    tool = route(msg)

    if tool == "wiki":
        return wiki(msg)
    if tool == "math":
        return math_tool(msg)
    if tool == "news":
        return news()
    if tool == "dict":
        return dictionary(msg)
    if tool == "tavily":
        return tavily(msg)

    def generate():
        completion = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": msg}],
            stream=True
        )

        for chunk in completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    return Response(stream_with_stream(generate()), mimetype="text/plain")

# ================= UI (RESTORED FULL) =================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy AI</title>
<style>
body{margin:0;font-family:Arial;background:#0b0f1a;color:white;display:flex;height:100vh;}
.sidebar{width:260px;background:#111827;padding:10px;}
.chat{flex:1;display:flex;flex-direction:column;}
.box{flex:1;overflow-y:auto;padding:10px;}
.msg{padding:10px;margin:5px;border-radius:10px;max-width:70%;}
.user{background:#2563eb;margin-left:auto;}
.ai{background:#1f2937;}
.input{display:flex;padding:10px;background:#111827;}
input{flex:1;padding:10px;}
button{padding:10px;background:#2563eb;color:white;border:none;}

.verified{color:#f97316;font-weight:bold;}
</style>
</head>

<body>

<div class="sidebar">
<div id="profile"></div>
</div>

<div class="chat" id="main">

<div class="box" id="box"></div>

<div class="input">
<input id="input">
<button onclick="send()">Send</button>
</div>

</div>

<script>

async function profile(){
let r=await fetch("/me");
let d=await r.json();

if(!d.logged_in){
document.getElementById("main").innerHTML=`
<h2>Login</h2>
<input id="u"><br>
<input id="p" type="password"><br>
<button onclick="login()">Login</button>

<h3>Signup</h3>
<input id="su"><br>
<input id="se"><br>
<input id="sp" type="password"><br>
<button onclick="signup()">Signup</button>
`;
return;
}

document.getElementById("profile").innerHTML =
d.username + (d.verified ? " ✔ VERIFIED" : "");
}

async function login(){
await fetch("/login",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({username:u.value,password:p.value})
});
location.reload();
}

async function signup(){
await fetch("/signup",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({username:su.value,email:se.value,password:sp.value})
});
alert("created");
}

async function send(){
let msg=input.value;
if(!msg)return;

let box=document.getElementById("box");

let user=document.createElement("div");
user.className="msg user";
user.innerText=msg;
box.appendChild(user);

let ai=document.createElement("div");
ai.className="msg ai";
box.appendChild(ai);

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg})
});

const reader=r.body.getReader();
const decoder=new TextDecoder();

ai.innerText="";

while(true){
const {value,done}=await reader.read();
if(done)break;
ai.innerText+=decoder.decode(value);
}
}

profile();

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

# ================= RUN =================
if __name__ == "__main__":
    app.run()
