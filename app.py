# Clean Bloxy-bot Script

Save ONLY the Python section below into `app.py`.


from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

OWNER_EMAIL = "alvinogthegreat177@gmail.com"
OWNER_PASSWORD = "alvindev17.og"

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


class Auth(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    email: str
    chat_id: str
    message: str


SPORTS_KEYWORDS = [
    "football", "soccer", "premier league", "nba",
    "nfl", "ufc", "boxing", "cricket",
    "f1", "tennis", "wimbledon", "ipl",
    "standings", "table", "fixtures"
]


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

        text = []

        for x in data.get("results", []):
            text.append(x.get("content", ""))

        return "
".join(text)

    except:

        return ""


def build_tool_context(prompt):

    text = prompt.lower()

    context = []

    if any(x in text for x in SPORTS_KEYWORDS):

        sports = tavily_search(prompt)

        if sports:
            context.append(f"SPORTS DATA:
{sports}")

    return "

".join(context)


def ask_ai(messages):

    if not OPENROUTER_API_KEY:
        return "OpenRouter API key missing."

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/auto",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 1
            },
            timeout=120
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]

        return f"AI Error: {data}"

    except Exception as e:

        return str(e)


@app.post("/signup")
def signup(data: Auth):

    if data.email in users:
        return {"ok": False, "error": "Account already exists"}

    users[data.email] = {
        "password": data.password,
        "username": data.email.split("@")[0],
        "created": str(datetime.now())
    }

    save_json(USERS_FILE, users)

    return {"ok": True}


@app.post("/login")
def login(data: Auth):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:
            return {"ok": False, "error": "Wrong password"}

        return {
            "ok": True,
            "username": "aTg",
            "verified": True,
            "email": OWNER_EMAIL
        }

    if data.email not in users:
        return {"ok": False, "error": "Account not found"}

    if users[data.email]["password"] != data.password:
        return {"ok": False, "error": "Wrong password"}

    return {
        "ok": True,
        "username": users[data.email]["username"],
        "verified": False,
        "email": data.email
    }


@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in chat_memory:
        chat_memory[data.email] = {}

    if data.chat_id not in chat_memory[data.email]:
        chat_memory[data.email][data.chat_id] = []

    history = chat_memory[data.email][data.chat_id]

    context = build_tool_context(data.message)

    system_prompt = f"""
You are Bloxy-bot.

Rules:
- Speak naturally like ChatGPT
- Be intelligent and conversational
- Use emojis naturally
- Format cleanly
- Be modern and helpful

External Context:
{context}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history[-10:]

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
color:white;
font-family:Arial;
}
.messages{
height:80vh;
overflow:auto;
padding:20px;
}
.msg{
background:#1a1a1a;
padding:16px;
border-radius:16px;
margin-bottom:14px;
white-space:pre-wrap;
}
.input-area{
padding:20px;
background:#111;
}
.inputbox{
width:100%;
padding:16px;
border:none;
border-radius:14px;
background:#1d1d1d;
color:white;
}
</style>
</head>
<body>
<div class='messages' id='messages'></div>
<div class='input-area'>
<input class='inputbox' id='message' placeholder='Message Bloxy-bot...' onkeydown="if(event.key==='Enter'){send()}">
</div>
<script>
let chats = [];
function send(){
let msg = message.value.trim();
if(!msg)return;
message.value='';
chats.push({role:'user',content:msg});
render();
fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:'guest@bloxy.ai',
chat_id:'main',
message:msg
})
})
.then(r=>r.json())
.then(d=>{
chats.push({role:'assistant',content:d.reply});
render();
});
}
function render(){
messages.innerHTML='';
for(let m of chats){
let div=document.createElement('div');
div.className='msg';
div.innerHTML=`<b>${m.role==='user'?'You':'Bloxy-bot'}</b><br><br>${m.content}`;
messages.appendChild(div);
}
messages.scrollTop=messages.scrollHeight;
}
</script>
</body>
</html>
"""


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
```



```txt
fastapi
uvicorn
requests
python-dotenv
```



```txt
python-3.11.9
```

# users.json

```json
{}
```

# chats.json

```json
{}
```
