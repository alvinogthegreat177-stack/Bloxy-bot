from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# 🔐 Groq API key (set in Render environment variables)
API_KEY = os.environ.get("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")

# 🧠 Simple memory
chat_history = [
    {"role": "system", "content": "You are a helpful, friendly AI assistant 🙂"}
]

# 🌐 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body { font-family: Arial; margin:0; display:flex; flex-direction:column; height:100vh; }
#chat { flex:1; padding:10px; overflow-y:auto; background:#f5f5f5; }
.msg { padding:10px; margin:6px; border-radius:8px; max-width:60%; }
.user { background:#cfe9ff; margin-left:auto; }
.ai { background:white; }
#inputArea { display:flex; padding:10px; }
#msg { flex:1; padding:10px; }
button { padding:10px; margin-left:5px; }
</style>
</head>

<body>

<div id="chat"></div>

<div id="inputArea">
<input id="msg" placeholder="Type message..." />
<button onclick="send()">Send</button>
</div>

<script>

async function send() {
    let msg = document.getElementById("msg").value;
    if (!msg) return;

    document.getElementById("chat").innerHTML +=
        "<div class='msg user'>" + msg + "</div>";

    const res = await fetch("/ai", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    });

    const data = await res.json();

    document.getElementById("chat").innerHTML +=
        "<div class='msg ai'>" + data.response + "</div>";

    document.getElementById("msg").value = "";
    document.getElementById("chat").scrollTop =
        document.getElementById("chat").scrollHeight;
}

document.addEventListener("keydown", e => {
    if (e.key === "Enter") send();
});

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ai", methods=["POST"])
def ai():
    global chat_history

    user_message = request.json["message"]
    chat_history.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": chat_history[-10:]
            }
        )

        data = response.json()

        # 🧠 SAFE CHECK (fixes 'choices' error)
        if "choices" not in data:
            print("GROQ ERROR:", data)
            return jsonify({"response": "⚠️ API Error: " + str(data)})

        reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"⚠️ Request error: {str(e)}"

    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})
