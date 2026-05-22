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
# API KEYS
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
APISPORTS_API_KEY = os.getenv("APISPORTS_API_KEY", "")
SPORTMONK_API_KEY = os.getenv("SPORTMONK_API_KEY", "")
SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")
ALLSPORTS_API_KEY = os.getenv("ALLSPORTS_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
EXA_API_KEY = os.getenv("EXA_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY", "")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "")

# =========================================================
# STORAGE
# =========================================================

CHATS = {}

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
# LIVE SPORTS CONTEXT
# =========================================================

def get_sports_context(query):

    try:

        if THESPORTSDB_API_KEY:

            r = requests.get(
                f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
                params={"t": query},
                timeout=3
            )

            return r.text[:1000]

    except:
        pass

    return ""

# =========================================================
# NEWS CONTEXT
# =========================================================

def get_news_context(query):

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
                timeout=3
            )

            return r.text[:1200]

    except:
        pass

    return ""

# =========================================================
# WIKIPEDIA CONTEXT
# =========================================================

def get_wiki_context(query):

    try:

        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=3
        )

        return r.text[:1000]

    except:
        pass

    return ""

# =========================================================
# BUILD CONTEXT
# =========================================================

def build_context(prompt):

    lower = prompt.lower()

    sports_words = [
        "football",
        "soccer",
        "arsenal",
        "chelsea",
        "man city",
        "premier league",
        "laliga",
        "nba",
        "ufc",
        "cricket",
        "f1",
        "formula 1",
        "horse racing",
        "nfl",
        "rugby"
    ]

    news_words = [
        "news",
        "war",
        "government",
        "politics",
        "breaking"
    ]

    context = []

    if any(x in lower for x in sports_words):
        context.append(get_sports_context(prompt))

    if any(x in lower for x in news_words):
        context.append(get_news_context(prompt))

    context.append(get_wiki_context(prompt))

    return "\n\n".join(context)

# =========================================================
# GROQ
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
            "max_tokens": 250
        },
        timeout=12
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]

# =========================================================
# OPENROUTER
# =========================================================

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
            "max_tokens": 250
        },
        timeout=12
    )

    data = r.json()

    return data["choices"][0]["message"]["content"]

# =========================================================
# ASK AI
# =========================================================

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
# CHAT ENDPOINT
# =========================================================

@app.post("/chat")
def chat(data: ChatRequest):

    if data.email not in CHATS:
        CHATS[data.email] = {}

    if data.chat_id not in CHATS[data.email]:
        CHATS[data.email][data.chat_id] = []

    history = CHATS[data.email][data.chat_id]

    context = build_context(data.message)

    system_prompt = f"""

You are Bloxy-bot AI Ultimate.

RULES:

1. Never say knowledge cutoff
2. Never say outdated
3. Never say As an AI
4. Never sound robotic
5. Never define words like a dictionary
6. Always sound modern
7. Always sound premium
8. Always sound natural
9. Always answer directly
10. Always answer beautifully
11. Always answer cleanly
12. Always support live information
13. Always support sports
14. Always support football
15. Always support NBA
16. Always support UFC
17. Always support F1
18. Always support cricket
19. Always support rugby
20. Always support NFL
21. Always support horse racing
22. Always support world news
23. Always support science
24. Always support coding
25. Always support gaming
26. Always support Roblox scripting
27. Always support current events
28. Always support moments ago events
29. Always avoid ugly formatting
30. Always avoid robotic numbering
31. Always avoid repeating yourself
32. Always avoid fake scores
33. Always avoid fake statistics
34. Always avoid fake information
35. Always prioritize live context
36. Always stay conversational
37. Always stay useful
38. Always stay fast
39. Always stay intelligent
40. Always stay smooth
41. Always avoid stale replies
42. Always answer like ChatGPT premium
43. Always avoid giant paragraphs
44. Always answer in readable style
45. Always support entertainment
46. Always support education
47. Always support finance
48. Always support technology
49. Always support tactical analysis
50. Always support transfer news
51. Always support standings
52. Always support predictions carefully
53. Always support recent updates
54. Always support modern information
55. Always support human-like replies
56. Always remain Bloxy-bot
57. Always feel production ready
58. Always feel like a real modern AI

LIVE CONTEXT:

{context}

"""

    messages = [

        {
            "role": "system",
            "content": system_prompt
        }

    ]

    messages += history[-4:]

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

    if len(history) > 12:
        history[:] = history[-12:]

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

*{
box-sizing:border-box;
}

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
width:280px;
background:#111;
border-right:1px solid #222;
display:flex;
flex-direction:column;
}

.sidebarTop{
padding:20px;
}

.logo{
font-size:32px;
font-weight:bold;
color:#00ff88;
margin-bottom:20px;
}

.newchat{
width:100%;
padding:14px;
border:none;
border-radius:14px;
background:#1d1d1d;
color:white;
cursor:pointer;
font-size:15px;
}

.chatlist{
flex:1;
overflow:auto;
padding:20px;
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

.chatBtns{
display:flex;
gap:6px;
}

.chatBtns button{
background:#222;
border:none;
color:white;
padding:6px 8px;
border-radius:8px;
cursor:pointer;
}

.accountBar{
padding:16px;
border-top:1px solid #222;
background:#151515;
display:flex;
justify-content:space-between;
align-items:center;
}

.accountLeft{
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
}

.accountBtns{
display:flex;
gap:8px;
}

.accountBtn{
background:#222;
border:none;
color:white;
padding:8px 12px;
border-radius:10px;
cursor:pointer;
}

.main{
flex:1;
display:flex;
flex-direction:column;
}

.topbar{
padding:18px;
background:#111;
border-bottom:1px solid #222;
font-weight:bold;
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
background:#181818;
line-height:1.7;
animation:fade .2s;
max-width:900px;
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
margin-left:auto;
border-left:4px solid orange;
}

.assistant{
border-left:4px solid #00ff88;
}

.topName{
display:flex;
align-items:center;
gap:6px;
font-weight:bold;
margin-bottom:8px;
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
background:#1c1c1c;
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
bottom:35px;
left:-50px;
width:260px;
background:#1b1b1b;
padding:12px;
border-radius:14px;
font-size:11px;
opacity:0;
pointer-events:none;
transition:.2s;
border:1px solid #333;
z-index:999;
}

.badgeWrap:hover .badgeTooltip{
opacity:1;
}

</style>

</head>

<body>

<div class='container'>

<div class='sidebar'>

<div class='sidebarTop'>

<div class='logo'>
Bloxy-bot
</div>

<button class='newchat' onclick='newChat()'>
+ New Chat
</button>

</div>

<div class='chatlist' id='chatlist'></div>

<div class='accountBar'>

<div class='accountLeft' id='account'></div>

<div class='accountBtns' id='accountButtons'></div>

</div>

</div>

<div class='main'>

<div class='topbar'>
Bloxy-bot AI Ultimate
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
verified:false,
guest:true
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

currentUser.username +

(currentUser.verified ? badge() : '');

if(currentUser.guest){

document.getElementById('accountButtons').innerHTML=`

<button class='accountBtn' onclick='login()'>
Sign In
</button>

`;

}else{

document.getElementById('accountButtons').innerHTML=`

<button class='accountBtn' onclick='logout()'>
Logout
</button>

`;

}

}

function login(){

let name=prompt("Enter username");

if(!name)return;

currentUser={

email:name+"@bloxy.ai",
username:name,
verified:name.toLowerCase()==='atg',
guest:false

};

updateAccount();

}

function logout(){

currentUser={

email:'guest',
username:'Guest',
verified:false,
guest:true

};

updateAccount();

}

function renderChats(){

let box=document.getElementById('chatlist');

box.innerHTML='';

Object.keys(chats).forEach(name=>{

let d=document.createElement('div');

d.className='chatitem';

d.innerHTML=`

<span onclick="switchChat('${name}')">

${chats[name].pinned ? '📌 ' : ''}${name}

</span>

<div class='chatBtns'>

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

<div class='topName'>

${m.role==='assistant'
?'Bloxy-bot'
:currentUser.username}

${m.role==='user' && currentUser.verified ? badge() : ''}

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

renderChats();

}

function deleteChat(name){

if(Object.keys(chats).length===1)return;

delete chats[name];

currentChat=Object.keys(chats)[0];

renderChats();

render();

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
content:'Failed to load response.'

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
