from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback

app = FastAPI()

# =========================================================
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

# =========================================================
# OWNER ACCOUNT
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

# =========================================================
# FILE STORAGE
# =========================================================

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

users = load_json(USERS_FILE, {})
chat_memory = load_json(CHATS_FILE, {})

# =========================================================
# MODELS (SAFE - FIXES 400 ERROR)
# =========================================================

class Auth(BaseModel):
    email: str = None
    password: str = None

class ChatRequest(BaseModel):
    email: str = None
    chat_id: str = None
    message: str = None

# =========================================================
# TOOLS
# =========================================================

def wikipedia_search(query):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        )
        return r.json().get("extract", "")
    except:
        return ""

def tavily_search(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 3
            },
            timeout=20
        )
        data = r.json()
        return "\n".join([x.get("content", "") for x in data.get("results", [])])
    except:
        return ""

def news_search(query):
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": 3
            }
        )
        data = r.json()
        return "\n".join([a["title"] for a in data.get("articles", [])])
    except:
        return ""

def wolfram_search(query):
    try:
        r = requests.get(
            "http://api.wolframalpha.com/v1/result",
            params={
                "appid": WOLFRAM_API_KEY,
                "i": query
            }
        )
        return r.text
    except:
        return ""

# =========================================================
# TOOL ROUTER
# =========================================================

def build_context(prompt):
    t = (prompt or "").lower()
    out = []

    if any(x in t for x in ["who is", "what is", "history", "country"]):
        w = wikipedia_search(prompt)
        if w: out.append("WIKIPEDIA:\n" + w)

    if any(x in t for x in ["search", "internet", "web"]):
        tw = tavily_search(prompt)
        if tw: out.append("TAVILY:\n" + tw)

    if any(x in t for x in ["news", "latest", "trending"]):
        nw = news_search(prompt)
        if nw: out.append("NEWS:\n" + nw)

    if any(x in t for x in ["solve", "math", "equation"]):
        wo = wolfram_search(prompt)
        if wo: out.append("WOLFRAM:\n" + wo)

    return "\n\n".join(out)

# =========================================================
# GROQ AI
# =========================================================

def ask_ai(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1200
            }
        )

        if r.status_code != 200:
            return f"AI ERROR {r.status_code}"

        return r.json()["choices"][0]["message"]["content"]

    except:
        return "AI system error."

# =========================================================
# CHAT (🔥 FIXED 400 ERROR HERE)
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    email = data.email or "guest"
    chat_id = data.chat_id or "main"
    message = data.message or ""

    if not message.strip():
        return {"reply": "Empty message."}

    if email not in chat_memory:
        chat_memory[email] = {}

    if chat_id not in chat_memory[email]:
        chat_memory[email][chat_id] = []

    history = chat_memory[email][chat_id]

    context = build_context(message)

    system = f"""
You are Bloxy-bot AI.

External context:
{context}
"""

    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": message})

    reply = ask_ai(messages)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})

    save_json(CHATS_FILE, chat_memory)

    return {"reply": reply}

# =========================================================
# AUTH (SIMPLE)
# =========================================================

@app.post("/signup")
def signup(data: Auth):
    if data.email in users:
        return {"ok": False, "error": "Exists"}

    users[data.email] = {
        "password": data.password,
        "verified": data.email == OWNER_EMAIL
    }

    save_json(USERS_FILE, users)

    return {"ok": True}

@app.post("/login")
def login(data: Auth):

    if data.email == OWNER_EMAIL and data.password == OWNER_PASSWORD:
        return {
            "ok": True,
            "verified": True,
            "username": "aTg"
        }

    if data.email not in users:
        return {"ok": False}

    if users[data.email]["password"] != data.password:
        return {"ok": False}

    return {
        "ok": True,
        "verified": users[data.email]["verified"],
        "username": data.email.split("@")[0]
    }

# =========================================================
# UI (YOUR FULL FRONTEND WOULD GO HERE)
# =========================================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body{margin:0;background:#0f0f0f;color:white;font-family:Arial;}
.chat{padding:20px;}
</style>
</head>
<body>

<div class="chat">
<h2>Bloxy-bot Running</h2>
<p>Frontend would be pasted here exactly as your original UI.</p>
</div>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
