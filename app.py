# 🧠 IMPROVED SYSTEM CORE

import sqlite3
import time

# 📀 DATABASE (persistent memory)
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
    chat TEXT,
    role TEXT,
    content TEXT
)
""")
conn.commit()


def save_msg(chat, role, content):
    cur.execute("INSERT INTO chats VALUES (?,?,?)", (chat, role, content))
    conn.commit()


def load_msgs(chat):
    cur.execute("SELECT role, content FROM chats WHERE chat=?", (chat,))
    return [{"role": r, "content": c} for r, c in cur.fetchall()]


# ⚡ SIMPLE CACHE (reduces API calls)
CACHE = {}

def cached_search(query):
    if query in CACHE:
        return CACHE[query]

    data = web_search(query)
    if not data:
        data = wikipedia_search(query)

    CACHE[query] = data
    return data


# 🧠 SMART ROUTER (better detection)
def smart_context(msg):
    m = msg.lower()

    if any(x in m for x in ["score", "league", "match", "today"]):
        return cached_search(msg)

    if any(x in m for x in ["what is", "who is", "define"]):
        return wikipedia_search(msg)

    return cached_search(msg)


# 🧠 CLEAN RESPONSE STYLE
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
You are Bloxy-bot.

Rules:
- Be clear and structured
- Avoid long paragraphs
- Use bullet points when useful
- If info is provided, USE it
- Do not say "I don't have access"
"""
}


# 🚀 FINAL AI FLOW
@app.route("/ai", methods=["POST"])
def ai():

    data = request.json
    msg = data["message"]
    chat = data["chat"]

    history = load_msgs(chat)

    # 🌐 Get context
    context = smart_context(msg)

    final_input = f"""
User question:
{msg}

Relevant info:
{context}
"""

    history.append({"role": "user", "content": final_input})

    reply = ask_groq([SYSTEM_PROMPT] + history[-10:])

    # 💾 SAVE MEMORY
    save_msg(chat, "user", msg)
    save_msg(chat, "assistant", reply)

    return jsonify({"response": reply})

