from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import os

app = FastAPI()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Chat(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body>
        <h2>Bloxy-bot</h2>
        <input id="msg" placeholder="Type a message">
        <button onclick="send()">Send</button>
        <pre id="out"></pre>

        <script>
        async function send() {
            const msg = document.getElementById("msg").value;

            const r = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({message: msg})
            });

            const data = await r.json();
            document.getElementById("out").textContent = data.reply;
        }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
def chat(data: Chat):

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "user", "content": data.message}
                ]
            },
            timeout=20
        )

        result = r.json()

        reply = result["choices"][0]["message"]["content"]

        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Error: {e}"}


import uuid

users = {}
sessions = {}

class Auth(BaseModel):
    email: str
    password: str

@app.post("/signup")
def signup(data: Auth):
    if data.email in users:
        return {"error": "Account already exists"}

    users[data.email] = {
        "password": data.password
    }

    return {"ok": True}

@app.post("/login")
def login(data: Auth):
    if data.email not in users:
        return {"error": "Account not found"}

    if users[data.email]["password"] != data.password:
        return {"error": "Wrong password"}

    session_id = str(uuid.uuid4())
    sessions[session_id] = data.email

    return {
        "session_id": session_id,
        "email": data.email
    }
