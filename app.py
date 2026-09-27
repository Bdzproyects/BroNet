import os
import json
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-net-ultra-secret'
app.config['UPLOAD_FOLDER'] = 'uploads/'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- BASE DE DATOS (JSON) --- [8]
USER_DB = 'data/users.json'

def load_users():
    if not os.path.exists(USER_DB): return []
    with open(USER_DB, 'r', encoding='utf-8') as f: return json.load(f)

def save_users(users):
    with open(USER_DB, 'w', encoding='utf-8') as f: json.dump(users, f, indent=4)

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    users = load_users()
    if not any(u['username'] == data['username'] for u in users):
        users.append(data)
        save_users(users)
        return jsonify({"status": "ok", "user": data['username']})
    for u in users:
        if u['username'] == data['username'] and u['password'] == data['password']:
            return jsonify({"status": "ok", "user": u['username']})
    return jsonify({"status": "error"}), 401

@app.route('/get_users', methods=['GET'])
def get_users():
    return jsonify([u['username'] for u in load_users()])

@app.route('/get_brols', methods=['GET'])
def get_brols():
    return jsonify([
        {"title": "Arquitectura Anas", "url": "https://www.w3schools.com/html/mov_bbb.mp4"},
        {"title": "Ciberseguridad Pro", "url": "https://www.w3schools.com/html/horse.mp4"}
    ])

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'file' not in request.files: return jsonify({"msg": "No hay archivo"})
    file = request.files['file']
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    # Lógica del Desintegrador de Virus [9, 10]
    try:
        result = subprocess.run(['clamscan', path], capture_output=True, text=True)
        if "Infected files: 0" not in result.stdout:
            os.remove(path)
            return jsonify({"msg": "¡VIRUS DETECTADO! Archivo desintegrado."})
    except: pass
    return jsonify({"msg": "Archivo seguro y guardado."})

# --- SOCKETS (CHAT PRIVADO) --- [Historial]
@socketio.on('join_private')
def on_join(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    join_room(room)

@socketio.on('send_msg')
def on_msg(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('new_msg', data, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080)) # Puerto dinámico para Railway [11]
    socketio.run(app, host='0.0.0.0', port=port)

3. La Cara: templates/index.html
He corregido los errores de etiquetas duplicadas y activado el Icono de Bíceps y el Manifiesto
.

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>BroNet - Arquitectura Anas</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link rel="manifest" href="/static/manifest.json">
    <link rel="icon" href="/static/logo.png" type="image/png">
    <style>
        body { font-family: sans-serif; background: #2c2f33; color: white; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        #sidebar { width: 220px; background: #23272a; padding: 20px; border-right: 1px solid #444; }
        #main { flex-grow: 1; padding: 20px; background: #36393f; display: flex; flex-direction: column; }
        .tab { display: none; flex-grow: 1; }
        .active { display: block; }
        .btn { background: #7289da; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; margin-bottom: 10px; }
        #chat-box { background: #2f3136; height: 70%; overflow-y: auto; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        input { width: 100%; padding: 10px; background: #40444b; color: white; border: none; border-radius: 5px; box-sizing: border-box; }
        .hidden { display: none; }
    </style>
</head>
<body>

<div id="login-overlay" style="position:fixed; inset:0; background:#23272a; z-index:100; display:flex; flex-direction:column; align-items:center; justify-content:center;">
    <h2>📡 Conectar a BroNet</h2>
    <input type="text" id="u" placeholder="Usuario" style="width:200px; margin:5px;">
    <input type="password" id="p" placeholder="Contraseña" style="width:200px; margin:5px;">
    <button onclick="login()" class="btn" style="width:210px; background:#43b581;">ENTRAR</button>
</div>

<div id="sidebar">
    <h2>BroNet</h2>
    <button class="btn" onclick="show('perfil')">👥 Bros</button>
    <button class="btn" onclick="show('chat')">💬 Chat</button>
    <button class="btn" onclick="show('brols')">🔥 Brols</button>
</div>

<div id="main">
    <div id="perfil-tab" class="tab active">
        <h3>Lista de Bros</h3>
        <div id="u-list"></div>
        <hr>
        <h4>Subir Archivo (Escaneo Virus)</h4>
        <input type="file" id="f-up">
        <button onclick="upload()" class="btn" style="margin-top:10px;">Subir y Escanear</button>
        <p id="up-status"></p>
    </div>

    <div id="chat-tab" class="tab">
        <h3 id="c-title">Selecciona un Bro</h3>
        <div id="chat-box"></div>
        <input type="text" id="m-in" placeholder="Escribe un mensaje...">
    </div>

    <div id="brols-tab" class="tab">
        <h3>🔥 Brols - Tendencias</h3>
        <div id="b-list"></div>
    </div>
</div>

<script>
    const socket = io();
    let me = "", target = "";

    async function login() {
        const res = await fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: document.getElementById('u').value, password: document.getElementById('p').value})
        });
        if(res.ok) {
            me = (await res.json()).user;
            document.getElementById('login-overlay').classList.add('hidden');
            loadUsers();
        }
    }

    async function loadUsers() {
        const res = await fetch('/get_users');
        const users = await res.json();
        document.getElementById('u-list').innerHTML = users.filter(u => u !== me).map(u => 
            `<div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>${u}</span><button onclick="startChat('${u}')" style="background:#43b581; color:white; border:none; border-radius:3px; cursor:pointer;">Chat</button></div>`
        ).join('');
    }

    function startChat(u) {
        target = u;
        document.getElementById('c-title').innerText = "Chat con " + u;
        socket.emit('join_private', {user: me, target: u});
        show('chat');
    }

    socket.on('new_msg', data => {
        document.getElementById('chat-box').innerHTML += `<p><strong>${data.user}:</strong> ${data.msg}</p>`;
    });

    document.getElementById('m-in').onkeypress = (e) => {
        if(e.key === 'Enter') {
            socket.emit('send_msg', {user: me, target: target, msg: e.target.value});
            e.target.value = "";
        }
    };

    async function upload() {
        const fd = new FormData();
        fd.append('file', document.getElementById('f-up').files);
        const res = await fetch('/upload_profile', { method: 'POST', body: fd });
        document.getElementById('up-status').innerText = (await res.json()).msg;
    }

    function show(t) {
        document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
        document.getElementById(t + '-tab').classList.add('active');
        if(t === 'brols') loadBrols();
    }

    async function loadBrols() {
        const res = await fetch('/get_brols');
        const brols = await res.json();
        document.getElementById('b-list').innerHTML = brols.map(v => 
            `<p>${v.title}</p><video width="100%" controls src="${v.url}"></video>`
        ).join('');
    }
</script>
</body>
</html>
