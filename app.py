from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
WORDS_API_KEY = os.environ.get("WORDS_API_KEY")  # optional

# 💾 DB
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Give clean, structured answers.
If listing, use vertical bullet format.
Be clear and helpful.
"""
}

# 📖 DICTIONARY LAYER

def dict_free(word):
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

def dict_datamuse(word):
    try:
        r = requests.get(f"https://api.datamuse.com/words?ml={word}").json()
        return ", ".join([w["word"] for w in r[:5]])
    except:
        return None

def dict_urban(word):
    try:
        r = requests.get(f"https://api.urbandictionary.com/v0/define?term={word}").json()
        return r["list"][0]["definition"]
    except:
        return None

def dict_wordsapi(word):
    if not WORDS_API_KEY:
        return None
    try:
        r = requests.get(
            f"https://wordsapiv1.p.rapidapi.com/words/{word}/definitions",
            headers={"X-RapidAPI-Key": WORDS_API_KEY}
        ).json()
        return r["definitions"][0]["definition"]
    except:
        return None

def dictionary_lookup(query):
    word = query.lower().split()[-1]

    sources = [
        dict_free(word),
        dict_wordsapi(word),
        dict_datamuse(word),
        dict_urban(word)
    ]

    results = [s for s in sources if s]

    if not results:
        return None

    return "📖 Definition:\n\n" + "\n\n".join(results[:3])

# 🌐 TAVILY
def tavily_search(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        data = r.json()
        results = data.get("results", [])
        return "\n".join([r["content"] for r in results[:5]])
    except:
        return None

# 📚 WIKIPEDIA
def wikipedia(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url).json()
        return r.get("extract")
    except:
        return None

# 🤖 GROQ
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 SMART ROUTER
def smart_answer(query, messages):

    # 1️⃣ Dictionary first
    dictionary = dictionary_lookup(query)
    if dictionary:
        return dictionary

    # 2️⃣ Wikipedia
    wiki = wikipedia(query.replace(" ", "_"))
    if wiki:
        return f"📚 {wiki}"

    # 3️⃣ Web
    web = tavily_search(query)
    if web:
        return f"🌐 {web}"

    # 4️⃣ AI
    return groq(messages)

# 🎨 UI (LOADING + SMOOTH)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}
#chat{flex:1;padding:20px;overflow-y:auto}
.msg{max-width:75%;padding:12px;margin:6px;border-radius:10px}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
#loading{position:fixed;top:0;left:0;width:100%;height:100%;background:black;display:none;align-items:center;justify-content:center}
</style>
</head>

<body>

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot 🤖..."/>
<button onclick="send()">Send</button>
</div>

<div id="loading">Processing your request... 🤖</div>

<script>

function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
}

function stream(text){
let d=document.createElement("div");
d.className="msg ai";
chat.appendChild(d);
let i=0;
let t=setInterval(()=>{
d.textContent=text.slice(0,i++);
if(i>text.length) clearInterval(t);
},5);
}

async function send(){
let input=document.getElementById("msg");
let m=input.value;
if(!m)return;

input.value="";
add("user",m);

loading.style.display="flex";

let r=await fetch("/ai",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:m})});

let d=await r.json();

loading.style.display="none";
stream(d.response);
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ai", methods=["POST"])
def ai():
    msg = request.json["message"]

    reply = smart_answer(msg, [SYSTEM, {"role":"user","content":msg}])

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
WORDS_API_KEY = os.environ.get("WORDS_API_KEY")  # optional

# 💾 DB
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT, title TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM
SYSTEM = {
    "role": "system",
    "content": """
You are Bloxy-bot 🤖.

Give clean, structured answers.
If listing, use vertical bullet format.
Be clear and helpful.
"""
}

# 📖 DICTIONARY LAYER

def dict_free(word):
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

def dict_datamuse(word):
    try:
        r = requests.get(f"https://api.datamuse.com/words?ml={word}").json()
        return ", ".join([w["word"] for w in r[:5]])
    except:
        return None

def dict_urban(word):
    try:
        r = requests.get(f"https://api.urbandictionary.com/v0/define?term={word}").json()
        return r["list"][0]["definition"]
    except:
        return None

def dict_wordsapi(word):
    if not WORDS_API_KEY:
        return None
    try:
        r = requests.get(
            f"https://wordsapiv1.p.rapidapi.com/words/{word}/definitions",
            headers={"X-RapidAPI-Key": WORDS_API_KEY}
        ).json()
        return r["definitions"][0]["definition"]
    except:
        return None

def dictionary_lookup(query):
    word = query.lower().split()[-1]

    sources = [
        dict_free(word),
        dict_wordsapi(word),
        dict_datamuse(word),
        dict_urban(word)
    ]

    results = [s for s in sources if s]

    if not results:
        return None

    return "📖 Definition:\n\n" + "\n\n".join(results[:3])

# 🌐 TAVILY
def tavily_search(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        data = r.json()
        results = data.get("results", [])
        return "\n".join([r["content"] for r in results[:5]])
    except:
        return None

# 📚 WIKIPEDIA
def wikipedia(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url).json()
        return r.get("extract")
    except:
        return None

# 🤖 GROQ
def groq(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# 🧠 SMART ROUTER
def smart_answer(query, messages):

    # 1️⃣ Dictionary first
    dictionary = dictionary_lookup(query)
    if dictionary:
        return dictionary

    # 2️⃣ Wikipedia
    wiki = wikipedia(query.replace(" ", "_"))
    if wiki:
        return f"📚 {wiki}"

    # 3️⃣ Web
    web = tavily_search(query)
    if web:
        return f"🌐 {web}"

    # 4️⃣ AI
    return groq(messages)

# 🎨 UI (LOADING + SMOOTH)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot 🤖</title>
<style>
body{margin:0;display:flex;height:100vh;background:#0d0d0d;color:white;font-family:Arial}
#chat{flex:1;padding:20px;overflow-y:auto}
.msg{max-width:75%;padding:12px;margin:6px;border-radius:10px}
.user{background:#2563eb;margin-left:auto}
.ai{background:#1f1f1f}
#input{display:flex;padding:10px;background:#111}
input{flex:1;padding:10px;background:#222;color:white;border:none}
#loading{position:fixed;top:0;left:0;width:100%;height:100%;background:black;display:none;align-items:center;justify-content:center}
</style>
</head>

<body>

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Ask Bloxy-bot 🤖..."/>
<button onclick="send()">Send</button>
</div>

<div id="loading">Processing your request... 🤖</div>

<script>

function add(role,text){
let d=document.createElement("div");
d.className="msg "+role;
d.textContent=text;
chat.appendChild(d);
}

function stream(text){
let d=document.createElement("div");
d.className="msg ai";
chat.appendChild(d);
let i=0;
let t=setInterval(()=>{
d.textContent=text.slice(0,i++);
if(i>text.length) clearInterval(t);
},5);
}

async function send(){
let input=document.getElementById("msg");
let m=input.value;
if(!m)return;

input.value="";
add("user",m);

loading.style.display="flex";

let r=await fetch("/ai",{method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({message:m})});

let d=await r.json();

loading.style.display="none";
stream(d.response);
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ai", methods=["POST"])
def ai():
    msg = request.json["message"]

    reply = smart_answer(msg, [SYSTEM, {"role":"user","content":msg}])

    return jsonify({"response":reply})

if __name__ == "__main__":
    app.run()
