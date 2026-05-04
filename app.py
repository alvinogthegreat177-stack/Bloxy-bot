from flask import Flask, request, jsonify, session, Response, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
import sqlite3, os, json, uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

# ================= AI =================
groq = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# ================= DATABASE =================
db = sqlite3.connect("chatgpt.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
username TEXT PRIMARY KEY,
password TEXT,
verified INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
id TEXT,
user TEXT,
data TEXT
)
""")
db.commit()

# ================= LOCKED OWNER SYSTEM =================
OWNER_USERNAME = "aTg"

def init_owner():
    cur.execute("SELECT * FROM users WHERE username=?", (OWNER_USERNAME,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users VALUES (?,?,?)",
            (OWNER_USERNAME, generate_password_hash("alvintheultimede17.og"), 1)
        )
        db.commit()

init_owner()

# ================= AUTH =================
def register_user(u,p):
    if u == OWNER_USERNAME:
        return False
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)",
                (u, generate_password_hash(p), 0))
    db.commit()
    return True

def login_user(u,p):
    cur.execute("SELECT password FROM users WHERE username=?", (u,))
    row = cur.fetchone()
    if row and check_password_hash(row[0], p):
        session["user"] = u
        return True
    return False

def get_user():
    u = session.get("user")
    if not u:
        return {"name":"Guest","verified":False}

    cur.execute("SELECT verified FROM users WHERE username=?", (u,))
    r = cur.fetchone()
    return {
        "name": u,
        "verified": bool(r[0]) if r else False
    }

# ================= CHAT MEMORY (ChatGPT STYLE) =================
def save_chat(user, cid, msg, reply):
    cur.execute("SELECT data FROM chats WHERE id=? AND user=?", (cid,user))
    row = cur.fetchone()

    data = json.loads(row[0]) if row else []

    data.append({"role":"user","content":msg})
    data.append({"role":"assistant","content":reply})

    if row:
        cur.execute("UPDATE chats SET data=? WHERE id=? AND user=?",
                    (json.dumps(data), cid, user))
    else:
        cur.execute("INSERT INTO chats VALUES (?,?,?)",
                    (cid,user,json.dumps(data)))

    db.commit()

# ================= VECTOR MEMORY (SIMPLIFIED CHATGPT STYLE) =================
def memory_context(user, msg):
    cur.execute("SELECT data FROM chats WHERE user=? ORDER BY rowid DESC LIMIT 5", (user,))
    rows = cur.fetchall()

    context = []
    for r in rows:
        try:
            context.extend(json.loads(r[0])[-4:])
        except:
            pass

    return context

# ================= AI AGENT (NO RULES - CHATGPT STYLE) =================
def ai_agent(user, msg):
    context = memory_context(user, msg)

    messages = [
        {"role":"system","content":
         "You are a ChatGPT-level assistant. Use memory and reasoning."}
    ]

    for c in context:
        messages.append({"role":c["role"],"content":c["content"]})

    messages.append({"role":"user","content":msg})

    res = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=0.7
    )

    return res.choices[0].message.content

# ================= STREAMING (CHATGPT TYPING EFFECT) =================
def stream_ai(user, msg):
    res = groq.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role":"system","content":"You are a streaming AI."},
            {"role":"user","content":msg}
        ],
        stream=True
    )

    full = ""

    for chunk in res:
        if chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            full += token
            yield token

    save_chat(user, str(uuid.uuid4()), msg, full)

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ChatGPT-Level AI</title>
<style>
body{margin:0;font-family:Arial;background:#0b0f1a;color:white;display:flex;height:100vh;}
.chat{flex:1;display:flex;flex-direction:column;}
.box{flex:1;overflow:auto;padding:15px;}
.msg{padding:10px;margin:6px;border-radius:10px;max-width:70%;}
.u{background:#2563eb;margin-left:auto;}
.a{background:#1f2937;}
.input{display:flex;padding:10px;background:#111827;}
input{flex:1;padding:10px;border:none;outline:none;}
button{padding:10px;background:#2563eb;color:white;}
.userpanel{position:fixed;bottom:10px;left:10px;background:#1f2937;padding:10px;border-radius:8px;}
</style>
</head>
<body>

<div class="chat">
<div class="box" id="box"></div>

<div class="input">
<input id="inp">
<button onclick="send()">Send</button>
</div>
</div>

<div class="userpanel" id="userpanel"></div>

<script>

async function send(){
 let m=inp.value;
 box.innerHTML+="<div class='msg u'>"+m+"</div>";

 let res = await fetch("/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({m})});

 let reader = res.body.getReader();
 let decoder = new TextDecoder();

 let ai="";
 let div=document.createElement("div");
 div.className="msg a";
 box.appendChild(div);

 while(true){
  let {done,value}=await reader.read();
  if(done)break;
  ai+=decoder.decode(value);
  div.innerText=ai;
 }
}

async function me(){
 let r=await fetch("/me");
 let d=await r.json();
 userpanel.innerText=d.name + (d.verified ? " ✔ Verified" : "");
}
me();

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

@app.route("/login",methods=["POST"])
def login():
    d=request.json
    if login_user(d["u"],d["p"]):
        return jsonify({"ok":True})
    return jsonify({"ok":False})

@app.route("/signup",methods=["POST"])
def signup():
    d=request.json
    register_user(d["u"],d["p"])
    return jsonify({"ok":True})

@app.route("/stream",methods=["POST"])
def stream():
    user = get_user()["name"]
    msg = request.json["m"]
    return Response(stream_ai(user,msg), mimetype="text/plain")

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
