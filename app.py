import os

from flask import Flask, render_template_string
from flask_socketio import SocketIO

# =====================================================
# SAFE INIT (NO CRASH ZONE)
# =====================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "bloxy_base"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# =====================================================
# BASIC ROUTE (ENSURES SERVER ALWAYS STARTS)
# =====================================================
@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{
margin:0;
background:#0b0f19;
color:white;
font-family:sans-serif;
display:flex;
height:100vh;
}

#sidebar{
width:240px;
background:#111;
padding:10px;
}

#main{
flex:1;
display:flex;
flex-direction:column;
}

#chat{
flex:1;
padding:10px;
overflow:auto;
}

.msg{
margin:6px;
padding:10px;
border-radius:8px;
max-width:70%;
}

.user{background:#2563eb;margin-left:auto}
.bot{background:#1f1f1f}

#input{
display:flex;
padding:10px;
background:#111;
}

input{
flex:1;
padding:10px;
background:#222;
border:none;
color:white;
}

button{
padding:10px;
background:#2563eb;
border:none;
color:white;
}
</style>
</head>

<body>

<div id="sidebar">
<h3>Bloxy-bot</h3>
<p style="color:#777;font-size:12px">
Stable Base v1
</p>
</div>

<div id="main">

<div id="chat"></div>

<div id="input">
<input id="msg" placeholder="Type...">
<button onclick="send()">Send</button>
</div>

</div>

<script>
const socket = io();

function add(type,text){
let d=document.createElement("div");
d.className="msg "+type;
d.textContent=text;
chat.appendChild(d);
chat.scrollTop=chat.scrollHeight;
}

socket.on("reply",data=>{
add("bot",data.text);
});

function send(){
let m=msg.value;
if(!m)return;

msg.value="";
add("user",m);

socket.emit("msg",{text:m});
}
</script>

</body>
</html>
""")

# =====================================================
# SOCKET (SAFE + MINIMAL)
# =====================================================
@socketio.on("msg")
def handle(data):
    text = data.get("text","")

    # SAFE RESPONSE (NO AI YET)
    reply = f"You said: {text}"

    socketio.emit("reply", {"text": reply})

# =====================================================
# RUN (CRASH SAFE)
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
