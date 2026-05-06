from flask import Flask, request, jsonify, render_template_string
import requests, os

app = Flask(__name__)

# KEYS
GROQ = os.getenv("GROQ_API_KEY")
TAVILY = os.getenv("TAVILY_API_KEY")
NEWS = os.getenv("NEWS_API_KEY")
WOLFRAM = os.getenv("WOLFRAM_APP_ID")

ACCOUNT_NAME = "aTg"

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>aTg AI</title>
<style>
body {margin:0;display:flex;font-family:Arial;background:#0f0f0f;color:white;}
.sidebar {width:250px;background:#181818;padding:20px;}
.main {flex:1;display:flex;flex-direction:column;align-items:center;}
#chat {width:60%;margin-top:50px;}
.message {background:#222;padding:10px;margin:10px 0;border-radius:10px;animation:slide .3s;}
input {width:60%;padding:15px;margin:20px;border-radius:10px;border:none;}
@keyframes slide {from{opacity:0;transform:translateY(-10px);}to{opacity:1;}}
.badge svg {width:14px;height:14px;fill:orange;margin-left:5px;}
.name {color:#aaa;font-size:12px;}
</style>
</head>
<body>

<div class="sidebar">
  <h2>aTg AI</h2>
  <div>
    aTg
    <span class="badge">
      <svg viewBox="0 0 24 24">
        <path d="M12 2l3 7h7l-5.5 4.2L18 21l-6-4-6 4 1.5-7.8L2 9h7z"/>
      </svg>
    </span>
  </div>

  <p>Sources:</p>
  <ul>
    <li>Groq</li>
    <li>Tavily</li>
    <li>Wikipedia</li>
    <li>NewsAPI</li>
    <li>Wolfram</li>
  </ul>
</div>

<div class="main">
  <div id="chat"></div>
  <input id="input" placeholder="Ask anything..." />
</div>

<script>
const chat = document.getElementById("chat");
const input = document.getElementById("input");

input.addEventListener("keypress", async (e) => {
 if(e.key==="Enter"){
   const msg = input.value;
   input.value="";
   addMessage("aTg", msg, true);

   const res = await fetch("/chat", {
     method:"POST",
     headers:{"Content-Type":"application/json"},
     body:JSON.stringify({message:msg})
   });

   const data = await res.json();
   addMessage("AI", data.reply, false);
 }
});

function addMessage(name, text, isUser){
 const div = document.createElement("div");
 div.className="message";

 const badge = isUser ? `
 <span class="badge">
   <svg viewBox="0 0 24 24">
     <path d="M12 2l3 7h7l-5.5 4.2L18 21l-6-4-6 4 1.5-7.8L2 9h7z"/>
   </svg>
 </span>` : "";

 div.innerHTML = `<div class="name">${name}${badge}</div>${text}`;
 chat.appendChild(div);
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

# TOOL FUNCTIONS
def tavily_search(q):
    try:
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": TAVILY,
            "query": q
        })
        return r.json().get("results", [])[:2]
    except:
        return []

def wiki_summary(q):
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}")
        return r.json().get("extract", "")
    except:
        return ""

def news(q):
    try:
        r = requests.get(f"https://newsapi.org/v2/everything?q={q}&apiKey={NEWS}")
        articles = r.json().get("articles", [])[:2]
        return [a["title"] for a in articles]
    except:
        return []

def wolfram(q):
    try:
        r = requests.get(f"http://api.wolframalpha.com/v1/result?i={q}&appid={WOLFRAM}")
        return r.text
    except:
        return ""

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message")

    # TOOL AGGREGATION
    context = ""

    context += "\\nWikipedia: " + wiki_summary(msg)
    context += "\\nNews: " + str(news(msg))
    context += "\\nSearch: " + str(tavily_search(msg))
    context += "\\nMath: " + wolfram(msg)

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role":"system","content":"Use provided tools context when helpful."},
                    {"role":"user","content": msg + "\\n\\n" + context}
                ]
            }
        )

        reply = r.json()["choices"][0]["message"]["content"]

    except:
        reply = "Error."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run()
