# app.py

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import requests
import json
import os
import traceback

app = FastAPI()

# =========================================================
# ENV VARIABLES
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")
SECRET_API_KEY = os.getenv("SECRET_API_KEY")

# =========================================================
# STORAGE
# =========================================================

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
chats = load_json(CHATS_FILE, {})

# =========================================================
# OWNER
# =========================================================

OWNER_EMAIL = "admin@bloxy.ai"
OWNER_PASSWORD = "bloxyadmin"
OWNER_USERNAME = "aTg"

# =========================================================
# AI MODELS
# =========================================================

AI_MODELS = [
    {
        "provider": "groq",
        "model": "llama-3.1-8b-instant"
    },
    {
        "provider": "openrouter",
        "model": "deepseek/deepseek-chat-v3-0324:free"
    },
    {
        "provider": "openrouter",
        "model": "qwen/qwen3-32b"
    },
    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile"
    }
]

# =========================================================
# REQUEST MODELS
# =========================================================

class Signup(BaseModel):
    username: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    email: str
    message: str
    chat_id: str

# =========================================================
# LIVE CONTEXT
# =========================================================


def wiki_context(query):
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=2
        )

        return r.json().get("extract", "")[:700]

    except:
        return ""



def gnews_context(query):
    try:
        r = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "token": GNEWS_API_KEY,
                "lang": "en",
                "max": 2
            },
            timeout=2
        )

        return r.text[:1000]

    except:
        return ""



def sports_context(query):
    try:
        r = requests.get(
            f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
            params={"t": query},
            timeout=2
        )

        return r.text[:1000]

    except:
        return ""



def build_context(prompt):

    lower = prompt.lower()

    sports_words = [
        "football", "soccer", "premier league", "nba",
        "nfl", "ufc", "f1", "formula 1", "boxing",
        "cricket", "rugby", "horse racing"
    ]

    news_words = [
        "news", "politics", "war", "government",
        "president", "breaking"
    ]

    parts = []

    if any(x in lower for x in sports_words):
        parts.append(sports_context(prompt))

    if any(x in lower for x in news_words):
        parts.append(gnews_context(prompt))

    if len(prompt.split()) > 3:
        parts.append(wiki_context(prompt))

    return "\n\n".join([x for x in parts if x])

# =========================================================
# AI ROUTING
# =========================================================


def groq_chat(model, messages):

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 890
        },
        timeout=5
    )

    return r.json()["choices"][0]["message"]["content"]



def openrouter_chat(model, messages):

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 120
        },
        timeout=5
    )

    return r.json()["choices"][0]["message"]["content"]



def ask_ai(messages):

    for model in AI_MODELS:

        try:

            if model["provider"] == "groq":
                return groq_chat(model["model"], messages)

            if model["provider"] == "openrouter":
                return openrouter_chat(model["model"], messages)

        except Exception:
            print(traceback.format_exc())
            continue

    return "Bloxy-bot is overloaded right now."

# =========================================================
# AUTH ROUTES
# =========================================================

@app.post("/signup")
def signup(data: Signup):

    if data.email in users:
        return {"ok": False}

    users[data.email] = {
        "username": data.username,
        "password": data.password
    }

    save_json(USERS_FILE, users)

    return {"ok": True}


@app.post("/login")
def login(data: Login):

    if data.email == OWNER_EMAIL:

        if data.password != OWNER_PASSWORD:
            return {"ok": False}

        return {
            "ok": True,
            "email": OWNER_EMAIL,
            "username": OWNER_USERNAME,
            "verified": True
        }

    if data.email not in users:
        return {"ok": False}

    if users[data.email]["password"] != data.password:
        return {"ok": False}

    return {
        "ok": True,
        "email": data.email,
        "username": users[data.email]["username"],
        "verified": False
    }

# =========================================================
# CHAT ROUTE
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in chats:
        chats[data.email] = {}

    if data.chat_id not in chats[data.email]:
        chats[data.email][data.chat_id] = []

    history = chats[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI Ultimate.

RULES:

1. NEVER say your knowledge is outdated
2. NEVER mention training cutoffs
3. NEVER say As an AI
4. NEVER say language model
5. ALWAYS sound modern
6. ALWAYS answer naturally
7. ALWAYS prioritize live information
8. ALWAYS prioritize usefulness
9. ALWAYS sound premium
10. ALWAYS avoid robotic replies
11. ALWAYS avoid repetitive greetings
12. ALWAYS avoid dictionary definitions
13. ALWAYS answer sports intelligently
14. ALWAYS answer politics intelligently
15. ALWAYS answer science intelligently
16. ALWAYS answer finance intelligently
17. ALWAYS answer coding intelligently
18. ALWAYS answer gaming intelligently
19. ALWAYS answer current events
20. ALWAYS feel fast and alive
21. ALWAYS avoid stale information
22. ALWAYS avoid fake scores
23. ALWAYS avoid fake statistics
24. ALWAYS avoid fake news
25. ALWAYS avoid fake citations
26. ALWAYS use recent context naturally
27. ALWAYS keep responses smooth
28. ALWAYS avoid filler
29. ALWAYS adapt to user tone
30. ALWAYS remain conversational
31. ALWAYS remain premium
32. ALWAYS answer directly
33. ALWAYS avoid unnecessary explanations
34. ALWAYS support live sports
35. ALWAYS support breaking news
36. ALWAYS support live events
37. ALWAYS support recent events
38. ALWAYS support modern AI topics
39. ALWAYS support Roblox scripting
40. ALWAYS support historical questions
41. ALWAYS support school questions
42. ALWAYS support mathematics
43. ALWAYS support entertainment
44. ALWAYS support world affairs
45. ALWAYS support football leagues
46. ALWAYS support horse racing
47. ALWAYS support UFC
48. ALWAYS support F1
49. ALWAYS support NBA
50. ALWAYS support NFL
51. ALWAYS support cricket
52. ALWAYS support rugby
53. ALWAYS avoid repetitive formatting
54. ALWAYS avoid robotic structure
55. ALWAYS sound and be responsive
56. ALWAYS sound intelligent
57. ALWAYS feel like a production AI
58. ALWAYS remain Bloxy-bot AI Ultimate
59. ALWAYS use emojis

Context:

{context}

"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    messages += history[-1:]

    messages.append({
        "role": "user",
        "content": data.message
    })

    reply = ask_ai(messages)

    blocked = [
        "As an AI",
        "language model",
        "training cutoff",
        "My knowledge"
    ]

    for b in blocked:
        reply = reply.replace(b, "")

    history.append({
        "role": "user",
        "content": data.message
    })

    history.append({
        "role": "assistant",
        "content": reply
    })

    if len(history) > 6:
        history[:] = history[-6:]

    save_json(CHATS_FILE, chats)

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
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Bloxy-bot</title>
<style>
body{
margin:0;
background:#0d0d0d;
font-family:Arial;
color:white;
overflow:hidden;
}
.container{
display:flex;
height:100vh;
}
.sidebar{
width:260px;
background:#111;
border-right:1px solid #222;
padding:20px;
box-sizing:border-box;
}
.logo{
font-size:30px;
font-weight:bold;
margin-bottom:20px;
color:#00ff88;
}
.newchat{
width:100%;
padding:14px;
border:none;
border-radius:14px;
background:#1d1d1d;
color:white;
cursor:pointer;
margin-bottom:15px;
}
.chatitem{
padding:14px;
background:#181818;
border-radius:14px;
margin-bottom:10px;
cursor:pointer;
display:flex;
justify-content:space-between;
align-items:center;
}
.main{
flex:1;
display:flex;
flex-direction:column;
}
.topbar{
padding:18px;
border-bottom:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
background:#111;
}
.messages{
flex:1;
overflow:auto;
padding:20px;
}
.msg{
background:#181818;
padding:18px;
border-radius:18px;
margin-bottom:18px;
line-height:1.7;
}
.user{
border-left:4px solid orange;
}
.assistant{
border-left:4px solid #00ff88;
}
.inputarea{
padding:18px;
border-top:1px solid #222;
background:#111;
}
.row{
display:flex;
gap:10px;
}
.input{
flex:1;
padding:18px;
border:none;
outline:none;
background:#1d1d1d;
border-radius:18px;
color:white;
font-size:15px;
}
.send{
width:70px;
border:none;
background:orange;
color:white;
font-size:22px;
border-radius:18px;
cursor:pointer;
}
.helper{
text-align:center;
opacity:.45;
font-size:12px;
margin-top:10px;
}
.badgeWrap{
display:flex;
align-items:center;
position:relative;
}
.badgeTooltip{
position:absolute;
bottom:30px;
left:-40px;
width:250px;
background:#1b1b1b;
padding:12px;
border-radius:14px;
font-size:11px;
opacity:0;
pointer-events:none;
transition:.2s;
border:1px solid #333;
}
.badgeWrap:hover .badgeTooltip{
opacity:1;
}
.typing{
display:flex;
align-items:center;
gap:5px;
}
.dot{
width:8px;
height:8px;
background:#00ff88;
border-radius:50%;
animation:bounce 1s infinite;
}
@keyframes bounce{
0%,80%,100%{transform:scale(0)}
40%{transform:scale(1)}
}
</style>
</head>
<body>
<div class='container'>
<div class='sidebar'>
<div class='logo'>Bloxy-bot</div>
<button class='newchat' onclick='newChat()'>+ New Chat</button>
<div id='chatlist'></div>
</div>
<div class='main'>
<div class='topbar'>
<div id='account'>Guest</div>
<button onclick='guestMode()'>Continue As Guest</button>
</div>
<div class='messages' id='messages'></div>
<div class='inputarea'>
<div class='row'>
<input id='message' class='input' placeholder='Message Bloxy-bot...' onkeydown="if(event.key==='Enter'){send()}">
<button class='send' onclick='send()'>➤</button>
</div>
<div class='helper'>
Bloxy-bot can make mistakes.Verify highly important information
</div>
</div>
</div>
</div>
<script>
let currentUser={
email:'guest',
username:'Guest',
verified:false
};
let chats={
'Main':{
messages:[],
pinned:false
}
};
let currentChat='Main';
function badge(){
return `
<div class='badgeWrap'>
<div class='badgeTooltip'>
This badge symbolizes the rightful owner of the platform or an admin contributor towards the platform.
</div>
<svg viewBox='0 0 24 24' width='18' height='18'>
<path fill='#ff8800' d='M12 1 L15 4 L19 3 L20 7 L23 12 L20 17 L19 21 L15 20 L12 23 L9 20 L5 21 L4 17 L1 12 L4 7 L5 3 L9 4 Z'/>
<path fill='white' d='M10 15 L7 12 L8.5 10.5 L10 12 L15.5 6.5 L17 8 Z'/>
</svg>
</div>`;
}
function updateAccount(){
document.getElementById('account').innerHTML=
currentUser.username+
(currentUser.verified?badge():'');
}
function renderChats(){
let box=document.getElementById('chatlist');
box.innerHTML='';
Object.keys(chats).forEach(name=>{
let d=document.createElement('div');
d.className='chatitem';
d.innerHTML=`
<span onclick="switchChat('${name}')">${name}</span>
<div>
<button onclick="renameChat('${name}')">✏️</button>
<button onclick="pinChat('${name}')">📌</button>
<button onclick="deleteChat('${name}')">🗑️</button>
</div>`;
box.appendChild(d);
});
}
function render(){
let box=document.getElementById('messages');
box.replaceChildren();
for(let m of chats[currentChat].messages){
let d=document.createElement('div');
d.className='msg '+m.role;
if(m.typing){
d.innerHTML=`<div class='typing'><div class='dot'></div><div class='dot'></div><div class='dot'></div><span>Bloxy-bot is typing...</span></div>`;
}else{
d.innerHTML=`
<div style='display:flex;align-items:center;gap:6px;font-weight:bold;margin-bottom:8px;'>
${m.role==='assistant'?'Bloxy-bot':currentUser.username+(currentUser.verified?badge():'')}
</div>
<div>${m.content}</div>`;
}
box.appendChild(d);
}
box.scrollTop=box.scrollHeight;
}
function newChat(){
let name='Chat '+(Object.keys(chats).length+1);
chats[name]={messages:[],pinned:false};
currentChat=name;
renderChats();
render();
}
function switchChat(name){
currentChat=name;
render();
}
function renameChat(name){
let n=prompt('Rename conversation',name);
if(!n)return;
chats[n]=chats[name];
delete chats[name];
currentChat=n;
renderChats();
}
function pinChat(name){
alert(name+' pinned');
}
function deleteChat(name){
if(Object.keys(chats).length===1)return;
delete chats[name];
currentChat=Object.keys(chats)[0];
renderChats();
render();
}
function guestMode(){
currentUser={
email:'guest',
username:'Guest',
verified:false
};
updateAccount();
}
async function send(){
let input=document.getElementById('message');
let msg=input.value.trim();
if(!msg)return;
input.value='';
chats[currentChat].messages.push({role:'user',content:msg});
chats[currentChat].messages.push({role:'assistant',typing:true});
render();
let r=await fetch('/chat',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({
email:currentUser.email,
message:msg,
chat_id:currentChat
})
});
let d=await r.json();
chats[currentChat].messages.pop();
chats[currentChat].messages.push({role:'assistant',content:d.reply});
render();
}
updateAccount();
renderChats();
render();
</script>
</body>
</html>
"""

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
