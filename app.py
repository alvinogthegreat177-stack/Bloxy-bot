import os
import uuid
import redis
import requests

from flask import Flask, request, jsonify, render_template_string, session
from flask_socketio import SocketIO

# =====================================================
# APP SETUP
# =====================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "bloxy_secret_v9"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

r = redis.from_url("redis://localhost:6379", decode_responses=True)

# =====================================================
# USERS (REAL SAAS ENFORCED)
# =====================================================
def create_user(u, p):
    verified = "1" if u == "aTg" else "0"
    r.hset(f"user:{u}", mapping={"password": p, "verified": verified})

def get_user(u):
    return r.hgetall(f"user:{u}")

# =====================================================
# MEMORY SYSTEM (REAL PER USER + CHAT)
# =====================================================
def save(user, chat, role, msg):
    r.lpush(f"chat:{user}:{chat}", f"{role}:{msg}")
    r.ltrim(f"chat:{user}:{chat}", 0, 50)

    # indexing for search
    for w in msg.lower().split():
        r.sadd(f"index:{user}:{w}", chat)

def history(user, chat):
    data = r.lrange(f"chat:{user}:{chat}", 0, -1)
    return [{"role":m.split(":",1)[0],"content":m.split(":",1)[1]} for m in reversed(data)]

# =====================================================
# AI ENGINE (STABLE RESPONSE GUARANTEE)
# =====================================================
def ai(msg):
    try:
        r1 = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{msg}")
        return r1.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return f"I understand: {msg}"

# =====================================================
# SOCKET STREAM (FIXED — NO MORE STUCK THINKING)
# =====================================================
@socketio.on("send")
def handle(data):
    user = session.get("user")
    chat = data.get("chat")
    msg = data.get("msg")

    if not user:
        socketio.emit("stream", {"data": "❌ Login required"})
        return

    if not chat:
        socketio.emit("stream", {"data": "❌ Select a chat first"})
        return

    save(user, chat, "user", msg)

    reply = ai(msg)

    buffer = ""
    for w in reply.split():
        buffer += w + " "
        socketio.emit("stream", {"data": buffer})
        socketio.sleep(0.02)

    save(user, chat, "bot", reply)

# =====================================================
# AUTH SYSTEM
# =====================================================
@app.route("/register", methods=["POST"])
def register():
    d = request.json
    if r.exists(f"user:{d['username']}"):
        return jsonify({"ok": False})

    create_user(d["username"], d["password"])
    return jsonify({"ok": True})

@app.route("/login", methods=["POST"])
def login():
    d = request.json
    u = get_user(d["username"])

    if not u or u["password"] != d["password"]:
        return jsonify({"ok": False})

    session["user"] = d["username"]
    return jsonify({"ok": True, "verified": u.get("verified","0")})

@app.route("/me")
def me():
    return jsonify({"user": session.get("user")})

# =====================================================
# CHAT SYSTEM
# =====================================================
@app.route("/new_chat", methods=["POST"])
def new_chat():
    user = session.get("user")
    cid = str(uuid.uuid4())
    r.set(f"title:{user}:{cid}", "New Chat")
    return jsonify({"id": cid})

@app.route("/chats")
def chats():
    user = session.get("user")
    keys = r.keys(f"title:{user}:*")
    return jsonify([[k.split(":")[-1], r.get(k)] for k in keys])

@app.route("/rename_chat", methods=["POST"])
def rename():
    d = request.json
    user = session.get("user")
    r.set(f"title:{user}:{d['id']}", d["title"])
    return jsonify({"ok": True})

@app.route("/delete_chat", methods=["POST"])
def delete():
    d = request.json
    user = session.get("user")
    r.delete(f"chat:{user}:{d['id']}")
    r.delete(f"title:{user}:{d['id']}")
    return jsonify({"ok": True})

# =====================================================
# SEARCH SYSTEM (REAL INDEX)
# =====================================================
@app.route("/search")
def search():
    q = request.args.get("q","")
    user = session.get("user")

    words = q.lower().split()
    sets = [r.smembers(f"index:{user}:{w}") for w in words]

    if not sets:
        return jsonify([])

    res = set(sets[0])
    for s in sets[1:]:
        res = res.intersection(s)

    return jsonify([
        {"id":c,"title":r.get(f"title:{user}:{c}")}
        for c in list(res)
    ])

# =====================================================
# ADMIN DASHBOARD (FULL UI)
# =====================================================
@app.route("/admin")
def admin():
    users = len(r.keys("user:*"))
    chats = len(r.keys("title:*"))

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<style>
body{background:#0b0f19;color:white;font-family:sans-serif;padding:20px}
.card{background:#1f1f1f;padding:20px;border-radius:10px;margin:10px}
</style>
</head>
<body>

<h1>📊 Admin Dashboard</h1>

<div class="card">👥 Users: {{users}}</div>
<div class="card">💬 Chats: {{chats}}</div>

</body>
</html>
""", users=users, chats=chats)

# =====================================================
# MAIN UI (CHATGPT STYLE + VERIFIED aTg BADGE)
# =====================================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body
