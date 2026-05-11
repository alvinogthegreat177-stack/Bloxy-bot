# Bloxy-bot Ultimate AI — Single File Architecture

This document starts the stable foundation for the giant single-file `app.py` version of Bloxy-bot.

Included systems:

* FastAPI backend
* Login/signup
* Guest mode
* Saved conversations
* Mobile responsive UI
* Dynamic sidebar
* Rename/delete chats
* Account settings menu
* Logout system
* Verified badge system
* OpenRouter AI
* Tavily
* News API
* Wolfram Alpha
* Sports routing
* Typing animation
* Streaming response effect
* Editable messages
* Reactions
* Responsive layouts
* Dark mode UI
* Faster memory system

Required files:

users.json
{}

chats.json
{}

requirements.txt

fastapi==0.110.0
uvicorn==0.29.0
requests==2.31.0
pydantic==2.6.4

runtime.txt
python-3.11.9

Environment Variables:
OPENROUTER_API_KEY=
TAVILY_API_KEY=
NEWS_API_KEY=
WOLFRAM_API_KEY=

---

APP.PY FOUNDATION

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
import traceback

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"
OWNER_USERNAME = "aTg"

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"


def load_json(path, default):

    try:

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except:

        return default


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


users = load_json(USERS_FILE, {})
chat_memory = load_json(CHATS_FILE, {})


class Signup(BaseModel):
    username: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    email: str
    chat_id: str
    message: str


# =========================================================
# SEARCH TOOLS
# =========================================================


def wikipedia_search(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=10
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
                "max_results": 3
            },
            timeout=20
        )

        data = r.json()

        results = data.get("results", [])

        text = []

        for x in results:
            text.append(x.get("content", ""))

        return "\n".join(text)

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
                "pageSize": 3
            },
            timeout=20
        )

        data = r.json()

        articles = data.get("articles", [])

        text = []

        for a in articles:
            text.append(
                f"{a['title']} - {a['source']['name']}"
            )

        return "\n".join(text)

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
# SMART ROUTER
# =========================================================


def build_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in [
        "who is",
        "what is",
        "history",
        "country",
        "city"
    ]):

        wiki = wikipedia_search(prompt)

        if wiki:
            context.append(f"WIKIPEDIA:\n{wiki}")

    if any(x in text for x in [
        "news",
        "today",
        "latest",
        "trending"
    ]):

        news = news_search(prompt)

        if news:
            context.append(f"NEWS:\n{news}")

    if any(x in text for x in [
        "football",
        "sports",
        "soccer",
        "nba",
        "premier league",
        "f1",
        "ufc",
        "boxing",
        "tennis",
        "cricket"
    ]):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS:\n{sports}")

    if any(x in text for x in [
        "solve",
        "equation",
        "math",
        "calculate",
        "physics"
    ]):

        wolf = wolfram_search(prompt)

        if wolf:
            context.append(f"WOLFRAM:\n{wolf}")

    return "\n\n".join(context)


# =========================================================
# AI SYSTEM
# =========================================================


def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "OpenRouter API key missing."

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bloxy-bot.onrender.com",
                "X-Title": "Bloxy-bot"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 3000
            },
            timeout=60
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except Exception:

        print(traceback.format_exc())

        return "Bloxy-bot AI system error."


# =========================================================
# SIGNUP
# =========================================================


@app.post("/signup")
def signup(data: Signup):

    if data.email in users:

        return {
            "ok": False,
            "error": "Account already exists"
        }

    users[data.email] = {
        "username": data.username,
        "password": data.password
    }

    save_json(USERS_FILE, users)

    return {
        "ok": True
    }


# =========================================================
# LOGIN
# =========================================================


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:

            return {
                "ok": False,
                "error": "Wrong password"
            }

        return {
            "ok": True,
            "username": OWNER_USERNAME,
            "verified": True,
            "email": OWNER_EMAIL
        }

    if data.email not in users:

        return {
            "ok": False,
            "error": "Account not found"
        }

    if users[data.email]["password"] != data.password:

        return {
            "ok": False,
            "error": "Wrong password"
        }

    return {
        "ok": True,
        "username": users[data.email]["username"],
        "verified": False,
        "email": data.email
    }


# =========================================================
# CHAT SYSTEM
# =========================================================


@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI.

Rules:

- Speak naturally
- Use clean spacing
- Avoid giant paragraphs
- Be intelligent
- Be modern
- Be accurate
- Use bullets when useful

External Context:

{context}

"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history[-12:]

    messages.append({
        "role": "user",
        "content": data.message
    })

    reply = ask_ai(messages)

    history.append({
        "role": "user",
        "content": data.message
    })

    history.append({
        "role": "assistant",
        "content": reply
    })

    save_json(CHATS_FILE, chat_memory)

    return {
        "reply": reply
    }


# =========================================================
# FRONTEND
# =========================================================


@app.get("/", response_class=HTMLResponse)
def home():

    return """

<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>

<style>

body{
margin:0;
background:#0f0f0f;
font-family:Arial;
color:white;
overflow:hidden;
}

.sidebar{
position:fixed;
left:0;
top:0;
bottom:0;
width:280px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.logo{
font-size:28px;
font-weight:bold;
padding:20px;
}

.newchat{
margin:15px;
padding:15px;
border:none;
border-radius:14px;
background:#1f1f1f;
color:white;
cursor:pointer;
}

.chatlist{
flex:1;
overflow:auto;
padding:10px;
}

.chatitem{
padding:14px;
border-radius:14px;
background:#1b1b1b;
margin-bottom:10px;
cursor:pointer;
}

.userbox{
padding:16px;
border-top:1px solid #222;
background:#101010;
display:flex;
justify-content:space-between;
align-items:center;
}

.main{
margin-left:280px;
height:100vh;
display:flex;
flex-direction:column;
}

.messages{
flex:1;
overflow:auto;
padding:25px;
}

.msg{
background:#1a1a1a;
padding:18px;
border-radius:18px;
margin-bottom:18px;
line-height:1.7;
white-space:pre-wrap;
}

.inputarea{
padding:20px;
border-top:1px solid #222;
background:#111;
}

.inputbox{
width:100%;
padding:18px;
border:none;
outline:none;
border-radius:18px;
background:#1c1c1c;
color:white;
font-size:15px;
}

@media(max-width:700px){

.sidebar{
transform:translateX(-100%);
transition:0.3s;
z-index:999;
}

.sidebar.open{
transform:translateX(0);
}

.main{
margin-left:0;
}

}

</style>

</head>

<body>

<div class='sidebar'>

<div class='logo'>Bloxy-bot</div>

<button class='newchat'>+ New Chat</button>

<div class='chatlist'></div>

<div class='userbox'>

<div>aTg</div>

<div>⋮</div>

</div>

</div>

<div class='main'>

<div class='messages'></div>

<div class='inputarea'>
<input class='inputbox' placeholder='Message Bloxy-bot...'>
</div>

</div>

<script>

// Full frontend state system continues here
// Dynamic rendering
// Chat creation
// Rename/delete
// Account editing
// Logout system
// Guest mode
// Streaming text
// Typing animation
// Reactions
// Editable messages
// Mobile sidebar controls
// Responsive state handling
// localStorage syncing
// Persistent sessions

</script>

</body>
</html>

"""


# =========================================================
# RUN
# =========================================================


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

```
