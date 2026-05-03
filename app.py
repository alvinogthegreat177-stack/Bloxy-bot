import os
import requests

from flask_socketio import SocketIO

# (keep your existing app + socketio setup from v1)
# ONLY ADD AI LAYER BELOW

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# =====================================================
# AI SOURCES
# =====================================================

def groq_ai(msg):
    if not GROQ_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are Bloxy-bot. Be helpful and structured."},
                    {"role": "user", "content": msg}
                ]
            }
        )
        return r.json()["choices"][0]["message"]["content"]
    except:
        return None


def tavily_search(msg):
    if not TAVILY_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": msg,
                "max_results": 3
            }
        )
        results = r.json().get("results", [])
        return " ".join([i["content"] for i in results])
    except:
        return None


def wikipedia(msg):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{msg}"
        )
        return r.json().get("extract")
    except:
        return None


def dictionary(msg):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{msg}"
        )
        return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# =====================================================
# SMART ENGINE (NEW BRAIN SYSTEM)
# =====================================================

def ai_engine(msg):

    # 1. Web first
    web = tavily_search(msg)
    if web:
        return "🌐 Web Result:\n" + web

    # 2. Groq AI
    ai = groq_ai(msg)
    if ai:
        return ai

    # 3. Wikipedia
    wiki = wikipedia(msg)
    if wiki:
        return "📚 Wikipedia:\n" + wiki

    # 4. Dictionary (only short inputs)
    if len(msg.split()) == 1:
        d = dictionary(msg)
        if d:
            return "📖 Definition:\n" + d

    return "I couldn't find a result."

# =====================================================
# SOCKET UPDATE (REPLACE YOUR v1 HANDLER ONLY)
# =====================================================

@socketio.on("msg")
def handle(data):
    text = data.get("text","")

    reply = ai_engine(text)

    buffer = ""

    for w in reply.split():
        buffer += w + " "
        socketio.emit("reply", {"text": buffer})
        socketio.sleep(0.02)
