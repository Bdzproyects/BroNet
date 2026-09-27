import os
import json
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-net-ultra-security-2026'
# Carpeta para fotos de perfil y videos (Brols)
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")

# --- RUTAS DE BASES DE DATOS ---
USER_DB = 'data/users.json'
MSG_DB = 'data/messages.json'

def load_data(path, default=[]):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: json.dump(default, f)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- RUTAS WEB ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u_name = data.get('username') # Identidad (usuario o email)
    email_reg = data.get('email', "")
    pwd = data.get('password')
    
    users = load_data(USER_DB)
    
    # 1. Intentar Login (Búsqueda por usuario o email) [775, Historial]
    user_found = next((u for u in users if u['username'] == u_name or u['email'] == u_name), None)
    
    if user_found:
        if user_found['password'] == pwd:
            return jsonify({"status": "ok", "user": user_found})
        return jsonify({"status": "error", "msg": "Clave incorrecta"}), 401
    else:
        # 2. Registro de Nuevo Bro [Historial]
        if not email_reg.lower().endswith("@gmail.com"):
            return jsonify({"status": "error", "msg": "Solo se permiten correos @gmail.com"}), 400
        
        if any(u['username'] == u_name for u in users):
            return jsonify({"status": "error", "msg": "Ese nombre de usuario ya está pillado"}), 400
        
        new_user = {
            "username": u_name,
            "email": email_reg,
            "password": pwd,
            "bio": "¡Soy un nuevo Arquitecto en BroNet!",
            "pic": "/static/logo.png"
        }
        users.append(new_user)
        save_data(USER_DB, users)
        return jsonify({"status": "ok", "user": new_user, "msg": "Registro completado"})

@app.route('/update_profile', methods=['POST'])
def update_profile():
    u_name = request.form.get('username')
    bio = request.form.get('bio')
    users = load_data(USER_DB)
    
    for u in users:
        if u['username'] == u_name:
            u['bio'] = bio
            if 'file' in request.files:
                file = request.files['file']
                # Guardamos el archivo con nombre seguro [434, Historial]
                filename = secure_filename(f"{u_name}_{file.filename}")
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                
                # --- DESINTEGRADOR DE VIRUS (Opcional: ClamAV) ---
                try:
                    result = subprocess.run(['clamscan', path], capture_output=True, text=True)
                    if "Infected files: 0" not in result.stdout:
                        os.remove(path) # Borrado físico inmediato
                        return jsonify({"status": "error", "msg": "¡VIRUS DETECTADO! Archivo desintegrado."}), 400
                except: pass
                
                u['pic'] = f"/{path}"
            
            save_data(USER_DB, users)
            return jsonify({"status": "ok", "user": u})
    return jsonify({"status": "error"}), 404

@app.route('/get_users', methods=['GET'])
def get_users():
    return jsonify([u['username'] for u in load_data(USER_DB)])

@app.route('/get_brols', methods=['GET'])
def get_brols():
    # Mezclamos videos externos con subidas locales de static/uploads/ [832, Historial]
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    community_videos = [f"/static/uploads/{f}" for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.mov'))]
    
    feed = [{"title": "Arquitectura Digital", "url": "https://www.w3schools.com/html/mov_bbb.mp4"}]
    for v in community_videos:
        feed.append({"title": "Bro Post", "url": v})
    return jsonify(feed)

@app.route('/get_history', methods=['POST'])
def get_history():
    data = request.json
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    msgs = load_data(MSG_DB)
    # Devolvemos solo los mensajes de esa habitación privada [661, Historial]
    return jsonify([m for m in msgs if m['room'] == room])

# --- SOCKETS: CHATS PRIVADOS Y MEMORIA ---
@socketio.on('join_private')
def on_join(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    join_room(room)

@socketio.on('send_msg')
def on_msg(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    msgs = load_data(MSG_DB)
    new_m = {"room": room, "user": data['user'], "msg": data['msg']}
    msgs.append(new_m)
    save_data(MSG_DB, msgs) # Guardado persistente
    emit('new_msg', new_m, room=room)

if __name__ == '__main__':
    # Puerto dinámico vital para Railway y evitar Error 502 [Historial]
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
