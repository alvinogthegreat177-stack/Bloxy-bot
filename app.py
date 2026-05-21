from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import requests
import json
import os
import traceback
import time

app = FastAPI()

# =========================================================
# 17+ API SOURCES
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
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
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
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
# 5 AI MODELS
# =========================================================

AI_MODELS = [

    {
        "provider": "groq",
        "model": "llama-3.1-8b-instant"
    },

    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile"
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
        "provider": "openrouter",
        "model": "mistralai/mistral-small-3.2-24b-instruct:free"
    }

]

# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    email: str
    message: str
    chat_id: str

# =========================================================
# LIVE SOURCES
# =========================================================

def sports_context(query):

    try:

        if THESPORTSDB_API_KEY:

            r = requests.get(
                f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
                params={"t": query},
                timeout=2
            )

            return r.text[:1000]

    except:
        pass

    return ""


def news_context(query):

    try:

        if GNEWS_API_KEY:

            r = requests.get(
                "https://gnews.io/api/v4/search",
                params={
                    "q": query,
                    "token": GNEWS_API_KEY,
                    "lang": "en",
                    "max": 3
                },
                timeout=2
            )

            return r.text[:1000]

    except:
        pass

    return ""


def wiki_context(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=2
        )

        return r.text[:900]

    except:
        return ""


def finance_context(query):

    try:

        if FINNHUB_API_KEY:

            r = requests.get(
                "https://finnhub.io/api/v1/quote",
                params={
                    "symbol": "AAPL",
                    "token": FINNHUB_API_KEY
                },
                timeout=2
            )

            return r.text[:500]

    except:
        pass

    return ""


def build_context(prompt):

    lower = prompt.lower()

    sports_words = [
        "football",
        "soccer",
        "premier league",
        "nba",
        "ufc",
        "boxing",
        "f1",
        "formula 1",
        "cricket",
        "rugby",
        "horse racing",
        "nfl",
        "mlb"
    ]

    finance_words = [
        "stock",
        "bitcoin",
        "crypto",
        "market",
        "shares",
        "finance"
    ]

    news_words = [
        "news",
        "war",
        "government",
        "breaking",
        "politics"
    ]

    parts = []

    if any(x in lower for x in sports_words):
        parts.append(sports_context(prompt))

    if any(x in lower for x in finance_words):
        parts.append(finance_context(prompt))

    if any(x in lower for x in news_words):
        parts.append(news_context(prompt))

    parts.append(wiki_context(prompt))

    return "\n\n".join([x for x in parts if x])

# =========================================================
# AI
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
            "temperature": 0.4,
            "max_tokens": 220
        },
        timeout=10
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]


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
            "temperature": 0.4,
            "max_tokens": 220
        },
        timeout=10
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]


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
# CHAT
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

CORE RULES:

1. Never say knowledge cutoff
2. Never say outdated
3. Never say As an AI
4. Never sound robotic
5. Always sound modern
6. Always sound premium
7. Always prioritize live info
8. Always answer naturally
9. Always answer directly
10. Always avoid dictionary definitions
11. Always avoid repetitive greetings
12. Always answer sports intelligently
13. Always answer finance intelligently
14. Always answer science intelligently
15. Always answer coding intelligently
16. Always answer gaming intelligently
17. Always answer politics intelligently
18. Always support live events
19. Always support recent events
20. Always support breaking news
21. Always support horse racing
22. Always support football
23. Always support NBA
24. Always support UFC
25. Always support Formula 1
26. Always support cricket
27. Always support rugby
28. Always support NFL
29. Always avoid fake scores
30. Always avoid fake statistics
31. Always avoid fake news
32. Always avoid filler
33. Always avoid stale replies
34. Always stay conversational
35. Always stay intelligent
36. Always stay smooth
37. Always adapt to user tone
38. Always prioritize usefulness
39. Always feel responsive
40. Always feel alive
41. Always support Roblox scripting
42. Always support current technology
43. Always support school questions
44. Always support math
45. Always support entertainment
46. Always support world affairs
47. Always support recent sports standings
48. Always support transfer news
49. Always support match analysis
50. Always support tactical analysis
51. Always support betting discussions
52. Always support odds analysis
53. Always support historical topics
54. Always support moments ago events
55. Always support real-time style replies
56. Always avoid repetitive formatting
57. Always remain Bloxy-bot
58. Always feel like a production AI

Live Context:

{context}

"""

    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]

    messages += history[-2:]

    messages.append({

        "role": "user",
        "content": data.message

    })

    reply = ask_ai(messages)

    blocked = [

        "As an AI",
        "language model",
        "training cutoff",
        "knowledge cutoff",
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

    if len(history) > 8:
        history[:] = history[-8:]

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
overflow:auto;
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
background:#1c1c1c;
color:white;
cursor:pointer;
margin-bottom:15px;
}

.chatitem{
padding:14px;
background:#181818;
border-radius:14px;
margin-bottom:10px;
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
background:#111;
display:flex;
justify-content:space-between;
align-items:center;
}

.messages{
flex:1;
overflow:auto;
padding:20px;
}

.msg{
padding:18px;
border-radius:18px;
margin-bottom:18px;
line-height:1.7;
background:#181818;
animation:fade .2s;
}

@keyframes fade{
from{
opacity:0;
transform:translateY(10px);
}
to{
opacity:1;
transform:translateY(0px);
}
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

.dot:nth-child(2){
animation-delay:.2s;
}

.dot:nth-child(3){
animation-delay:.4s;
}

@keyframes bounce{
0%,80%,100%{
transform:scale(0);
}
40%{
transform:scale(1);
}
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

</style>

</head>

<body>

<div class='container'>

<div class='sidebar'>

<div class='logo'>
Bloxy-bot
</div>

<button class='newchat' onclick='newChat()'>
+ New Chat
</button>

<div id='chatlist'></div>

</div>

<div class='main'>

<div class='topbar'>

<div id='account'></div>

<button onclick='guestMode()'>
Continue As Guest
</button>

</div>

<div class='messages' id='messages'></div>

<div class='inputarea'>

<div class='row'>

<input
id='message'
class='input'
placeholder='Message Bloxy-bot...'
onkeydown="if(event.key==='Enter'){send()}"
>

<button class='send' onclick='send()'>
➤
</button>

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

<path
fill='#ff8800'
d='M12 1 L15 4 L19 3 L20 7 L23 12 L20 17 L19 21 L15 20 L12 23 L9 20 L5 21 L4 17 L1 12 L4 7 L5 3 L9 4 Z'
/>

<path
fill='white'
d='M10 15 L7 12 L8.5 10.5 L10 12 L15.5 6.5 L17 8 Z'
/>

</svg>

</div>
`;

}

function updateAccount(){

document.getElementById('account').innerHTML=
currentUser.username+
(currentUser.verified?badge():"");

}

function renderChats(){

let box=document.getElementById('chatlist');

box.innerHTML='';

Object.keys(chats).forEach(name=>{

let d=document.createElement('div');

d.className='chatitem';

d.innerHTML=`

<span onclick="switchChat('${name}')">
${name}
</span>

<div>

<button onclick="renameChat('${name}')">
✏️
</button>

<button onclick="pinChat('${name}')">
📌
</button>

<button onclick="deleteChat('${name}')">
🗑️
</button>

</div>

`;

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

d.innerHTML=`

<div class='typing'>

<div class='dot'></div>
<div class='dot'></div>
<div class='dot'></div>

<span>
Bloxy-bot is typing...
</span>

</div>

`;

}else{

d.innerHTML=`

<div style='display:flex;align-items:center;gap:6px;font-weight:bold;margin-bottom:8px;'>

${m.role==='assistant'
?'Bloxy-bot'
:currentUser.username+(currentUser.verified?badge():'')}

</div>

<div>${m.content}</div>

`;

}

box.appendChild(d);

}

box.scrollTop=box.scrollHeight;

}

function newChat(){

let name='Chat '+(Object.keys(chats).length+1);

chats[name]={
messages:[],
pinned:false
};

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

chats[name].pinned=!chats[name].pinned;

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

chats[currentChat].messages.push({
role:'user',
content:msg
});

chats[currentChat].messages.push({
role:'assistant',
typing:true
});

render();

try{

let r=await fetch('/chat',{

method:'POST',

headers:{
'Content-Type':'application/json'
},

body:JSON.stringify({

email:currentUser.email,
message:msg,
chat_id:currentChat

})

});

let d=await r.json();

chats[currentChat].messages.pop();

chats[currentChat].messages.push({

role:'assistant',
content:d.reply

});

render();

}catch(e){

chats[currentChat].messages.pop();

chats[currentChat].messages.push({

role:'assistant',
content:'Error loading response.'

});

render();

}

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
