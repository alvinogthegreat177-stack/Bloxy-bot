# =========================================================
# BLOXY-BOT 2026 ULTIMATE AI
# NOW USING GROQ + LIVE APIs
# =========================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import traceback
import json
import os

app = FastAPI()

# =========================================================
# ENV VARIABLES
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY")

EXA_API_KEY = os.getenv("EXA_API_KEY")

# =========================================================
# OWNER VERIFIED ACCOUNT
# =========================================================

OWNER_EMAIL = "alvinogthegreat177@gmail.com"

OWNER_PASSWORD = "alvindev17.og"

OWNER_USERNAME = "aTg"

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

        with open(path, "r", encoding="utf-8") as f:

            return json.load(f)

    except:

        return default


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=2)


users = load_json(USERS_FILE, {})

chat_memory = load_json(CHATS_FILE, {})

# =========================================================
# MODELS
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
    chat_id: str
    message: str


class EditProfile(BaseModel):

    email: str
    username: str
    password: str


class DeleteAccount(BaseModel):

    email: str

# =========================================================
# LIVE APIs
# =========================================================

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
            timeout=15
        )

        data = r.json()

        text = []

        for x in data.get("results", []):

            text.append(
                x.get("content", "")
            )

        return "\n".join(text)

    except:

        return ""


def gnews_search(query):

    if not GNEWS_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "token": GNEWS_API_KEY,
                "lang": "en",
                "max": 2
            },
            timeout=15
        )

        data = r.json()

        text = []

        for x in data.get("articles", []):

            text.append(
                x.get("title", "")
            )

        return "\n".join(text)

    except:

        return ""


def wikipedia_search(query):

    try:

        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query,
            timeout=15
        )

        data = r.json()

        return data.get("extract", "")

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
            timeout=15
        )

        return r.text

    except:

        return ""


def sports_search(query):

    if not THESPORTSDB_API_KEY:

        return ""

    try:

        r = requests.get(
            f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_API_KEY}/searchteams.php",
            params={
                "t": query
            },
            timeout=15
        )

        return r.text[:2500]

    except:

        return ""


def finance_search():

    if not FINNHUB_API_KEY:

        return ""

    try:

        r = requests.get(
            "https://finnhub.io/api/v1/news",
            params={
                "category": "general",
                "token": FINNHUB_API_KEY
            },
            timeout=15
        )

        data = r.json()

        text = []

        for x in data[:3]:

            text.append(
                x.get("headline", "")
            )

        return "\n".join(text)

    except:

        return ""


def exa_search(query):

    if not EXA_API_KEY:

        return ""

    try:

        r = requests.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": EXA_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "numResults": 2
            },
            timeout=15
        )

        return r.text[:2500]

    except:

        return ""

# =========================================================
# CONTEXT BUILDER
# =========================================================

def build_context(prompt):

    text = prompt.lower()

    context = []

    tavily = tavily_search(prompt)

    if tavily:

        context.append("LIVE WEB:\n" + tavily)

    gnews = gnews_search(prompt)

    if gnews:

        context.append("NEWS:\n" + gnews)

    wiki = wikipedia_search(prompt)

    if wiki:

        context.append("WIKIPEDIA:\n" + wiki)

    exa = exa_search(prompt)

    if exa:

        context.append("EXA:\n" + exa)

    if any(x in text for x in [
        "football",
        "sports",
        "nba",
        "f1",
        "premier league",
        "cricket",
        "ufc",
        "boxing"
    ]):

        sports = sports_search(prompt)

        if sports:

            context.append("SPORTS:\n" + sports)

    if any(x in text for x in [
        "stock",
        "bitcoin",
        "crypto",
        "economy"
    ]):

        finance = finance_search()

        if finance:

            context.append("FINANCE:\n" + finance)

    if any(x in text for x in [
        "math",
        "solve",
        "equation",
        "calculate",
        "physics"
    ]):

        wolf = wolfram_search(prompt)

        if wolf:

            context.append("WOLFRAM:\n" + wolf)

    return "\n\n".join(context)

# =========================================================
# GROQ AI
# =========================================================

def ask_ai(messages):

    try:

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization":
                f"Bearer {GROQ_API_KEY}",

                "Content-Type":
                "application/json"
            },
            json={
                "model":
                "llama-3.3-70b-versatile",

                "messages":
                messages,

                "temperature":
                0.7,

                "max_tokens":
                2000
            },
            timeout=60
        )

        data = r.json()

        if "choices" in data:

            return data["choices"][0]["message"]["content"]

        return str(data)

    except Exception:

        print(traceback.format_exc())

        return "Bloxy-bot AI error."

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
                "ok": False
            }

        return {
            "ok": True,
            "username": OWNER_USERNAME,
            "verified": True,
            "email": OWNER_EMAIL
        }

    if data.email not in users:

        return {
            "ok": False
        }

    if users[data.email]["password"] != data.password:

        return {
            "ok": False
        }

    return {
        "ok": True,
        "username": users[data.email]["username"],
        "verified": False,
        "email": data.email
    }

# =========================================================
# EDIT PROFILE
# =========================================================

@app.post("/edit_profile")
def edit_profile(data: EditProfile):

    if data.email not in users:

        return {
            "ok": False
        }

    users[data.email]["username"] = data.username

    users[data.email]["password"] = data.password

    save_json(USERS_FILE, users)

    return {
        "ok": True
    }

# =========================================================
# DELETE ACCOUNT
# =========================================================

@app.post("/delete_account")
def delete_account(data: DeleteAccount):

    if data.email in users:

        del users[data.email]

    if data.email in chat_memory:

        del chat_memory[data.email]

    save_json(USERS_FILE, users)

    save_json(CHATS_FILE, chat_memory)

    return {
        "ok": True
    }

# =========================================================
# CHAT
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

- Use live 2026 information
- Be modern
- Be intelligent
- Use live web context
- Use bullet points
- Avoid giant paragraphs
- Keep responses readable
- Sports tables must be current
- Breaking news must be recent
- Know all about any sport
- Use easily understandable words
- Use occasional emojis where necessary

Context:

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

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<style>

body{
margin:0;
background:#0f0f0f;
font-family:Arial;
color:white;
overflow:hidden;
}

.container{
display:flex;
height:100vh;
}

.sidebar{
width:270px;
background:#111;
display:flex;
flex-direction:column;
border-right:1px solid #222;
}

.logo{
padding:22px;
font-size:30px;
font-weight:bold;
color:#00ff88;
text-shadow:0 0 18px #00ff88;
}

.newchat{
margin:15px;
padding:16px;
border:none;
border-radius:16px;
background:#1d1d1d;
color:white;
cursor:pointer;
}

.chatlist{
flex:1;
overflow:auto;
padding:10px;
}

.chatitem{
padding:15px;
background:#1b1b1b;
border-radius:16px;
margin-bottom:10px;
cursor:pointer;
}

.userbox{
padding:16px;
border-top:1px solid #222;
display:flex;
justify-content:space-between;
align-items:center;
background:#101010;
}

.main{
flex:1;
display:flex;
flex-direction:column;
}

.messages{
flex:1;
overflow:auto;
padding:25px;
}

.msg{
padding:18px;
background:#1a1a1a;
border-radius:18px;
margin-bottom:18px;
line-height:1.7;
white-space:pre-wrap;
}

.user{
border-left:4px solid orange;
}

.assistant{
border-left:4px solid #00ff88;
}

.inputarea{
padding:18px;
background:#111;
border-top:1px solid #222;
}

.inputbox{
width:100%;
padding:18px;
border:none;
outline:none;
border-radius:18px;
background:#1d1d1d;
color:white;
}

.helper{
margin-top:10px;
text-align:center;
opacity:0.4;
font-size:12px;
}

.auth{
position:fixed;
top:0;
left:0;
right:0;
bottom:0;
background:#000000dd;
display:flex;
justify-content:center;
align-items:center;
z-index:999;
backdrop-filter:blur(10px);
}

.authbox{
width:360px;
background:#171717;
padding:30px;
border-radius:24px;
}

.authinput{
width:100%;
padding:16px;
border:none;
outline:none;
border-radius:16px;
background:#222;
color:white;
margin-top:12px;
}

.authbtn{
width:100%;
padding:16px;
border:none;
border-radius:16px;
background:#00ff88;
font-weight:bold;
cursor:pointer;
margin-top:12px;
}

.guestbtn{
width:100%;
padding:15px;
border:none;
border-radius:16px;
background:#222;
color:white;
cursor:pointer;
margin-top:12px;
}

.accountmenu{
position:fixed;
bottom:80px;
left:20px;
background:#1d1d1d;
padding:10px;
border-radius:16px;
display:none;
flex-direction:column;
gap:10px;
z-index:999;
}

.accountbtn{
padding:12px;
background:#252525;
border-radius:12px;
cursor:pointer;
}

.typing{
padding:10px 25px;
opacity:0.7;
}

.verified{
display:inline-flex;
margin-left:6px;
vertical-align:middle;
}

.verified svg{
width:20px;
height:20px;
filter:drop-shadow(0 0 8px orange);
}

@media(max-width:700px){

.sidebar{
width:85px;
}

.logo{
font-size:18px;
}

}

</style>

</head>

<body>

<div class="auth"
id="auth">

<div class="authbox">

<h2>Bloxy-bot</h2>

<input id="username"
class="authinput"
placeholder="Username">

<input id="email"
class="authinput"
placeholder="Email">

<input id="password"
type="password"
class="authinput"
placeholder="Password">

<button class="authbtn"
onclick="signup()">
Signup
</button>

<button class="authbtn"
onclick="login()">
Login
</button>

<button class="guestbtn"
onclick="guestMode()">
Stay Signed Out
</button>

</div>

</div>

<div class="accountmenu"
id="accountmenu">

<div class="accountbtn"
onclick="editProfile()">
Edit Profile
</div>

<div class="accountbtn"
onclick="deleteAccount()">
Delete Account
</div>

<div class="accountbtn"
onclick="logout()">
Logout
</div>

</div>

<div class="container">

<div class="sidebar">

<div class="logo">
Bloxy-bot
</div>

<button class="newchat"
onclick="newChat()">
+ New Chat
</button>

<div class="chatlist"
id="chatlist">
</div>

<div class="userbox">

<div id="userbox">
Guest
</div>

<div
style="cursor:pointer;"
onclick="toggleMenu()">
⋮
</div>

</div>

</div>

<div class="main">

<div class="messages"
id="messages">
</div>

<div class="typing"
id="typing">
</div>

<div class="inputarea">

<input
id="message"
class="inputbox"
placeholder="Message Bloxy-bot..."
onkeydown="if(event.key==='Enter'){send()}">

<div class="helper">
Bloxy-bot can make mistakes. Verify important information.
</div>

</div>

</div>

</div>

<script>

let currentUser = {
email:"guest",
username:"Guest",
verified:false
};

let currentChat = "Main";

let chats = {
"Main":[]
};

function verifiedBadge(){

if(currentUser.verified){

return `
<span class="verified">

<svg viewBox="0 0 24 24">

<path
fill="#f6a000"

d="
M12 1
L14.5 4
L18.5 3
L19.5 7
L23 9
L21 13
L23 17
L19.5 19
L18.5 23
L14.5 22
L12 25
L9.5 22
L5.5 23
L4.5 19
L1 17
L3 13
L1 9
L4.5 7
L5.5 3
L9.5 4
Z"/>

<path
fill="white"

d="
M10 16
L6.5 12.5
L8 11
L10 13
L16.5 6.5
L18 8
Z"/>

</svg>

</span>
`;

}

return "";

}

function updateUser(){

document.getElementById(
"userbox"
).innerHTML = `
${currentUser.username}
${verifiedBadge()}
`;

}

function toggleMenu(){

let menu =
document.getElementById(
"accountmenu"
);

menu.style.display =
menu.style.display==="flex"
? "none"
: "flex";

}

function saveLocal(){

localStorage.setItem(
"bloxy_user",
JSON.stringify(currentUser)
);

localStorage.setItem(
"bloxy_chats",
JSON.stringify(chats)
);

}

function loadLocal(){

let u =
localStorage.getItem(
"bloxy_user"
);

if(u){

currentUser = JSON.parse(u);

document.getElementById(
"auth"
).style.display = "none";

}

let c =
localStorage.getItem(
"bloxy_chats"
);

if(c){

chats = JSON.parse(c);

}

}

function renderChats(){

let box =
document.getElementById(
"chatlist"
);

box.innerHTML = "";

for(let c in chats){

let d =
document.createElement("div");

d.className = "chatitem";

d.innerHTML = c;

d.onclick = ()=>{

currentChat = c;

render();

};

box.appendChild(d);

}

saveLocal();

}

function render(){

let box =
document.getElementById(
"messages"
);

box.innerHTML = "";

for(let m of chats[currentChat]){

let d =
document.createElement("div");

d.className =
"msg " +
(m.role==="assistant"
? "assistant"
: "user");

let name =
m.role==="assistant"
? "Bloxy-bot"
: currentUser.username;

let badge =
m.role==="user"
? verifiedBadge()
: "";

d.innerHTML = `
<b>
${name}
${badge}
</b>

<div style="margin-top:10px;">
${m.content.replace(/\\n/g,"<br>")}
</div>
`;

box.appendChild(d);

}

box.scrollTop =
box.scrollHeight;

saveLocal();

}

function newChat(){

let id =
"Chat " +
(Object.keys(chats).length+1);

chats[id] = [];

currentChat = id;

renderChats();
render();

}

function signup(){

fetch("/signup",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
username:username.value,
email:email.value,
password:password.value
})
})
.then(r=>r.json())
.then(d=>{

if(!d.ok){

alert(d.error);

return;

}

alert("Signup successful");

});

}

function login(){

fetch("/login",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
email:email.value,
password:password.value
})
})
.then(r=>r.json())
.then(d=>{

if(!d.ok){

alert("Login failed");

return;

}

currentUser = {
email:d.email,
username:d.username,
verified:d.verified
};

document.getElementById(
"auth"
).style.display = "none";

updateUser();

saveLocal();

});

}

function guestMode(){

document.getElementById(
"auth"
).style.display = "none";

updateUser();

}

function editProfile(){

let newName =
prompt(
"New Username",
currentUser.username
);

if(!newName) return;

let newPass =
prompt(
"New Password"
);

if(!newPass) return;

fetch("/edit_profile",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
email:currentUser.email,
username:newName,
password:newPass
})
})
.then(r=>r.json())
.then(d=>{

currentUser.username =
newName;

updateUser();

saveLocal();

});

}

function deleteAccount(){

let sure =
confirm(
"All the conversations and chats you have had with Bloxy-bot will be erased permanently."
);

if(!sure) return;

fetch("/delete_account",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
email:currentUser.email
})
})
.then(r=>r.json())
.then(d=>{

localStorage.clear();

location.reload();

});

}

function logout(){

localStorage.clear();

location.reload();

}

function send(){

let input =
document.getElementById(
"message"
);

let msg =
input.value.trim();

if(!msg){

return;

}

input.value = "";

chats[currentChat].push({
role:"user",
content:msg
});

render();

document.getElementById(
"typing"
).innerHTML =
"Bloxy-bot is typing...";

fetch("/chat",{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
email:currentUser.email,
chat_id:currentChat,
message:msg
})
})
.then(r=>r.json())
.then(d=>{

document.getElementById(
"typing"
).innerHTML = "";

let box =
document.getElementById(
"messages"
);

let wrapper =
document.createElement("div");

wrapper.className =
"msg assistant";

wrapper.innerHTML = `
<b>Bloxy-bot</b>

<div
id="streamingText"
style="margin-top:10px;">
</div>
`;

box.appendChild(wrapper);

let stream =
document.getElementById(
"streamingText"
);

let reply = "";

let i = 0;

let interval =
setInterval(()=>{

if(i < d.reply.length){

reply += d.reply[i];

stream.innerHTML =
reply.replace(/\\n/g,"<br>");

box.scrollTop =
box.scrollHeight;

i++;

}else{

clearInterval(interval);

chats[currentChat].push({
role:"assistant",
content:reply
});

saveLocal();

}

},6);

})
.catch(()=>{

document.getElementById(
"typing"
).innerHTML = "";

});

}

loadLocal();

updateUser();

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

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
