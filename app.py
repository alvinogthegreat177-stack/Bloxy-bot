from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# 🔐 API KEY from Render environment
API_KEY = os.environ.get("GROQ_API_KEY")

# 🧠 Chat memory
messages = [
    {"role": "system", "content": "You are Bloxy-bot, a helpful, friendly AI assistant 🙂"}
]

# 🧪 Debug check
print("🔥 GROQ KEY LOADED:", "FOUND" if API_KEY else "MISSING")

# 🌐 UI
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Bloxy-bot</title>
<style>
body { margin:0; font-family:Arial; display:flex; flex-direction:column; height:100vh; }
#chat { flex:1; overflow-y:auto; padding:15px; background:#f5f5f5; }
.msg { padding:10px; margin:6px; border-radius:10px; max-width:60%; }
.user { background:#cfe9ff; margin-left:auto; }
.ai { background:white; }
#input { display:flex; padding:10px; background:white; }
#msg { flex:1; padding:10px; border:1px solid #ccc; border-radius:6px; }
button { padding:10px; margin-left:5px; }
</style>
</head>

<body>

<div id="chat"></div>

<div id="input">
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
    global messages

    if not API_KEY:
        return jsonify({"response": "⚠️ Missing API key in Render environment variables."})

    user_message = request.json["message"]
    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages[-10:]
            }
        )

        data = response.json()

        # 🛡 Safety check
        if "choices" not in data:
            print("❌ GROQ ERROR:", data)
            return jsonify({"response": "⚠️ API ERROR: " + str(data)})

        reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    messages.append({"role": "assistant", "content": reply})

    return jsonify({"response": reply})
