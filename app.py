from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import wikipedia
import wolframalpha
import requests
import os
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

# ================= SAFE API SETUP =================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID")
NEWS_KEY = os.getenv("NEWS_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
wolfram = wolframalpha.Client(WOLFRAM_APP_ID) if WOLFRAM_APP_ID else None

# ================= MEMORY =================
conversations = {}

# ================= TOOLS =================

def wiki(q):
    try:
        return wikipedia.summary(q, sentences=2)
    except:
        return "Wikipedia result not found."

def math(q):
    if not wolfram:
        return "Wolfram API not configured."

    try:
        return next(wolfram.query(q).results).text
    except:
        return "Math error."

def news():
    if not NEWS_KEY:
        return "News API not configured."

    try:
        url = f"https://newsapi.org/v2/top-headlines?apiKey={NEWS_KEY}"
        r = requests.get(url).json()
        return "\n".join([a["title"] for a in r["articles"][:5]])
    except:
        return "News unavailable."

def web(q):
    if not TAVILY_KEY:
        return "Tavily API not configured."

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": q}
        ).json()
        return r.get("answer", "No result.")
    except:
        return "Web search failed."

def dictionary(word):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        ).json()
        return r[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return "No definition found."

# ================= ROUTER =================

def route(msg):
    t = msg.lower()

    if "define" in t or "meaning" in t:
        return dictionary(msg)

    if any(x in t for x in ["solve", "+", "-", "/", "equation"]):
        return math(msg)

    if "who is" in t or "what is" in t:
        return wiki(msg)

    if "news" in t or "latest" in t:
        return news()

    if "search" in t or "find" in t:
        return web(msg)

    return None

# ================= AI =================

def ai(msg):
    if not groq:
        return "⚠️ GROQ_API_KEY is missing on Render."

    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "Respond in a formal, structured, diplomatic tone."
                },
                {"role": "user", "content": msg}
            ]
        )
        return r.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
        return "⚠️ AI temporarily unavailable (API error)."

# ================= MEMORY SUMMARY =================

def make_summary(conv):
    try:
        text = "\n".join([m["text"] for m in conv["messages"][-8:]])

        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role": "user",
                "content": "Summarize this conversation in 1 short memory paragraph:\n" + text
            }]
        )

        conv["summary"] = r.choices[0].message.content

    except:
        conv["summary"] = "No memory available."

# ================= RESPONSE =================

def get_response(msg):
    tool = route(msg)
    if tool:
        return tool
    return ai(msg)

# ================= TITLE =================

def make_title(text):
    if not groq:
        return "New Chat"

    try:
        r = groq.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role": "user",
                "content": f"Summarize in 3-5 words: {text}"
            }]
        )
        return r.choices[0].message.content
    except:
        return "New Chat"

# ================= UI =================

HTML = """ (KEEP YOUR HTML EXACTLY SAME HERE — NOT CHANGED) """

# ================= ROUTES =================

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/new")
def new():
    cid = str(uuid.uuid4())

    conversations[cid] = {
        "title": "New Chat",
        "messages": [],
        "summary": ""
    }

    return jsonify({"id": cid})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data["message"]
    cid = data["id"]

    if cid not in conversations:
        conversations[cid] = {
            "title": "New Chat",
            "messages": [],
            "summary": ""
        }

    conv = conversations[cid]

    if len(conv["messages"]) == 0:
        conv["title"] = make_title(msg)

    reply = get_response(msg)

    conv["messages"].append({"role": "user", "text": msg})
    conv["messages"].append({"role": "ai", "text": reply})

    make_summary(conv)

    return jsonify({"reply": reply})

@app.route("/conversations")
def convs():
    return jsonify([
        {"id": k, "title": v["title"]}
        for k, v in conversations.items()
    ])

@app.route("/load")
def load():
    cid = request.args.get("id")
    return jsonify(conversations.get(cid, {"messages": []})["messages"])

@app.route("/rename", methods=["POST"])
def rename():
    d = request.json
    if d["id"] in conversations:
        conversations[d["id"]]["title"] = d["name"]
    return jsonify({"ok": True})

@app.route("/delete", methods=["POST"])
def delete():
    cid = request.json["id"]
    conversations.pop(cid, None)
    return jsonify({"ok": True})

# ================= RUN =================
if __name__ == "__main__":
    app.run()
