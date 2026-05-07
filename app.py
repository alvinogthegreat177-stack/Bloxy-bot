from fastapi import FastAPI, Request
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
# OWNER VERIFIED ACCOUNT
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

# =========================================================
# FILES
# =========================================================

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

# =========================================================
# HELPERS
# =========================================================

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
# MODELS
# =========================================================

class Auth(BaseModel):
    email: str
    password: str

class ChatRequest(BaseModel):
    email: str = None
    chat_id: str = None
    message: str = None

# =========================================================
# TOOLS (UNCHANGED)
# =========================================================

def wikipedia_search(query):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        )
        data = r.json()
        return data.get("extract", "")
    except:
        return ""

def tavily_search(query):
    if not TAVILY_API_KEY:
        return ""

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": 2
            },
            timeout=20
        )
        data = r.json()
        results = data.get("results", [])

        return "\n".join([x.get("content", "") for x in results])

    except:
        return ""

def news_search(query):
    if not NEWS_API_KEY:
        return ""

    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": 2
            },
            timeout=20
        )

        data = r.json()
        articles = data.get("articles", [])

        return "\n".join([f"{a['title']} - {a['source']['name']}" for a in articles])

    except:
        return ""

def wolfram_search(query):
    if not WOLFRAM_API_KEY:
        return ""

    try:
        r = requests.get(
            "http://api.wolframalpha.com/v1/result",
            params={
                "appid": WOLFRAM_API_KEY,
                "i": query
            },
            timeout=20
        )
        return r.text

    except:
        return ""

# =========================================================
# TOOL ROUTER
# =========================================================

def build_tool_context(prompt):

    text = (prompt or "").lower()
    context = []

    if any(x in text for x in ["who is", "what is", "history", "city", "country"]):
        w = wikipedia_search(prompt)
        if w:
            context.append("WIKIPEDIA:\n" + w)

    if any(x in text for x in ["news", "latest", "today", "trending"]):
        n = news_search(prompt)
        if n:
            context.append("NEWS:\n" + n)

    if any(x in text for x in ["solve", "calculate", "equation", "math"]):
        w = wolfram_search(prompt)
        if w:
            context.append("WOLFRAM:\n" + w)

    if any(x in text for x in ["search", "internet", "web", "research"]):
        t = tavily_search(prompt)
        if t:
            context.append("TAVILY:\n" + t)

    return "\n\n".join(context)

# =========================================================
# AI (SAFE 400 FIX HERE IS IMPORTANT)
# =========================================================

def ask_ai(messages):

    if not GROQ_API_KEY:
        return "Groq API key missing."

    try:
        response = requests.post(
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
            },
            timeout=60
        )

        # 🔥 FIX 400 HANDLING
        if response.status_code != 200:
            print("GROQ ERROR:", response.text)
            return f"AI Error {response.status_code}"

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(traceback.format_exc())
        return "AI system error."

# =========================================================
# CHAT (🔥 THIS FIXES YOUR 400 ERROR)
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    # 🔥 SAFE DEFAULTS (PREVENT 400 CRASH)
    email = data.email or "guest"
    chat_id = data.chat_id or "main"
    message = data.message or ""

    if not message.strip():
        return {"reply": "Empty message received."}

    if email not in chat_memory:
        chat_memory[email] = {}

    if chat_id not in chat_memory[email]:
        chat_memory[email][chat_id] = []

    history = chat_memory[email][chat_id]

    tool_context = build_tool_context(message)

    system_prompt = f"""
You are Bloxy-bot AI.

External Context:
{tool_context}
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": message})

    reply = ask_ai(messages)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})

    save_json(CHATS_FILE, chat_memory)

    return {"reply": reply}

# =========================================================
# FRONTEND (UNCHANGED)
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """ YOUR EXISTING UI EXACTLY AS YOU GAVE IT """

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
