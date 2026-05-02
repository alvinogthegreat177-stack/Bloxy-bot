from flask import Flask, request, jsonify, render_template_string
import sqlite3, os, requests

app = Flask(__name__)

# 🔐 KEYS
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# 💾 DATABASE
conn = sqlite3.connect("bloxy.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS messages (chat_id TEXT, role TEXT, content TEXT)")
conn.commit()

# 🤖 SYSTEM PROMPT
SYSTEM = {
"role": "system",
"content": """
You are Bloxy-bot 🤖.

RULES:
- Use clear structured answers
- Use vertical formatting for lists
- Never hallucinate facts when using web tools
- Be concise and accurate
"""
}

# 📖 DICTIONARY
def dictionary_lookup(query):
    try:
        if not any(x in query.lower() for x in ["define","meaning","what is"]):
            return None
        word = query.split()[-1]
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        return r.json()[0]["meanings"][0]["definitions"][0]["definition"]
    except:
        return None

# 📚 WIKIPEDIA
def wikipedia(query):
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}")
        if r.status_code == 200:
            return r.json().get("extract")
    except:
        return None

# 🌐 TAVILY
def tavily(query):
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": query}
        )
        results = r.json().get("results", [])
        return " ".join([x["content"] for x in results[:3]]) if results else None
    except:
        return None

# 🤖 GROQ
def groq(messages):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.4
            }
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ AI error: {str(e)}"

# 🧠 MEMORY SYSTEM

def save_message(chat_id, role, content):
    cur.execute("INSERT INTO messages VALUES (?,?,?)", (chat_id, role, content))
    conn.commit()

def get_recent(chat_id):
    cur.execute(
        "SELECT role,content FROM messages WHERE chat_id=? ORDER BY rowid DESC LIMIT 12",
        (chat_id,)
    )
    return [{"role":r,"content":c} for r,c in reversed(cur.fetchall())]

def get_summary(chat_id):
    cur.execute("SELECT content FROM messages WHERE chat_id=?", (chat_id,))
    msgs = cur.fetchall()

    if len(msgs) < 20:
        return None

    text = " ".join([m[0] for m in msgs[-40:]])
    return f"Memory summary of chat: {text[:800]}"

# 🧠 SMART ROUTER
def smart_answer(query, chat_id):

    q = query.lower().strip()

    # 📖 Dictionary
    d = dictionary_lookup(query)
    if d:
        return f"📖 Definition:\n{d}"

    # 📚 Wikipedia
    w = wikipedia(query.replace(" ","_"))
    if w:
        return f"📚 {w[:500]}..."

    # 🌐 Tavily
    t = tavily(query)
    if t:
        return groq([
            SYSTEM,
            {"role":"user","content":f"Summarize clearly:\n\n{t}"}
        ])

    # 🧠 MEMORY BUILD
    recent = get_recent(chat_id)
    summary = get_summary(chat_id)

    messages = [SYSTEM]

    if summary:
        messages.append({"role":"system","content":summary})

    messages += recent
    messages.append({"role":"user","content":query})

    return groq(messages)

# 🌐 AI ENDPOINT
@app.route("/ai", methods=["POST"])
def ai():
    try:
        data = request.json
        msg = data["message"]
        chat_id = data["chat"]

        reply = smart_answer(msg, chat_id)

        if not reply:
            reply = "⚠️ No response generated."

        save_message(chat_id, "user", msg)
        save_message(chat_id, "assistant", reply)

        return jsonify({"response": str(reply)})

    except Exception as e:
        return jsonify({"response": f"❌ Error: {str(e)}"})

# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)
