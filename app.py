from flask import Flask, request, jsonify, render_template_string, session, Response, stream_with_context
from groq import Groq
import sqlite3
import os
import uuid
import hashlib

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# ================= AI =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ================= OWNER EMAIL =================
OWNER_EMAIL = "alvinogthegreat177@gmail.com"

# ================= DB =================
DB = "app.db"

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT,
        user_id TEXT,
        role TEXT,
        text TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= SECURITY =================

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ================= SESSION =================

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

# ================= SIGNUP =================

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    uid = str(uuid.uuid4())

    verified = 1 if data["email"] == OWNER_EMAIL else 0

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO users VALUES (?,?,?,?,?)
        """, (
            uid,
            data["username"],
            data["email"],
            hash_pw(data["password"]),
            verified
        ))
        conn.commit()
    except:
        return jsonify({"error": "User exists"})

    conn.close()
    return jsonify({"ok": True})

# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT id FROM users WHERE username=? AND password=?
    """, (data["username"], hash_pw(data["password"])))

    user = c.fetchone()
    conn.close()

    if user:
        session["uid"] = user[0]
        return jsonify({"ok": True})

    return jsonify({"error": "Invalid login"})

# ================= AI STREAM =================

def ai_stream(msg):
    completion = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": msg}],
        stream=True
    )

    for chunk in completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ================= CHAT =================

@app.route("/chat", methods=["POST"])
def chat():
    user = current_user()

    if not user:
        return jsonify({"error": "Not logged in"})

    uid = user[0]
    msg = request.json["message"]

    def generate():
        full = ""

        for chunk in ai_stream(msg):
            full += chunk
            yield chunk

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("INSERT INTO messages VALUES (?,?,?,?)",
                  (str(uuid.uuid4()), uid, "user", msg))

        c.execute("INSERT INTO messages VALUES (?,?,?,?)",
                  (str(uuid.uuid4()), uid, "ai", full))

        conn.commit()
        conn.close()

    return Response(stream_with_context(generate()), mimetype="text/plain")

# ================= PROFILE =================

@app.route("/me")
def me():
    user = current_user()

    if not user:
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "username": user[1],
        "email": user[2],
        "verified": bool(user[3])
    })

# ================= UI =================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI System</title>
<style>
body{background:#0b0f1a;color:white;font-family:Arial;}
.box{padding:20px;}
.verified{color:#f97316;font-weight:bold;}
</style>
</head>

<body>

<div class="box">
<h2>AI Platform</h2>

<div id="profile"></div>

<input id="msg">
<button onclick="send()">Send</button>

<pre id="out"></pre>
</div>

<script>

async function profile(){
let r=await fetch("/me");
let d=await r.json();

if(d.logged_in){
document.getElementById("profile").innerHTML =
"User: "+d.username +
(d.verified ? " ✔ VERIFIED OWNER" : "");
}
}

async function send(){
let msg=document.getElementById("msg").value;

let r=await fetch("/chat",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:msg})
});

const reader=r.body.getReader();
const decoder=new TextDecoder();

document.getElementById("out").innerText="";

while(true){
const {value,done}=await reader.read();
if(done)break;
document.getElementById("out").innerText += decoder.decode(value);
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
