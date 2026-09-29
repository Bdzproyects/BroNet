import os
import json
import time
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-net-ultra-security-2026'

# Carpetas de almacenamiento
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/', exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Bases de datos JSON
USER_DB = 'data/users.json'
MSG_DB = 'data/messages.json'

# Mapeo de presencia en tiempo real (sid -> username)
online_users = {}

def load_data(path, default=[]):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- RUTAS HTTP ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u_name = data.get('username')
    email = data.get('email', "")
    pwd = data.get('password')
    
    users = load_data(USER_DB)
    user_found = next((u for u in users if u['username'] == u_name or u['email'] == u_name), None)
    
    if user_found:
        if user_found['password'] == pwd:
            return jsonify({"status": "ok", "user": user_found})
        return jsonify({"status": "error", "msg": "Contraseña incorrecta"}), 401
    else:
        if not email.lower().endswith("@gmail.com"):
            return jsonify({"status": "error", "msg": "Se requiere un correo @gmail.com para el registro"}), 400
        if any(u['username'] == u_name for u in users):
            return jsonify({"status": "error", "msg": "Ese nombre de usuario ya está en uso"}), 400
        
        new_user = {
            "username": u_name,
            "email": email,
            "password": pwd,
            "bio": "BroNet User",
            "pic": "/static/logo.png"
        }
        users.append(new_user)
        save_data(USER_DB, users)
        return jsonify({"status": "ok", "user": new_user})

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
                filename = secure_filename(f"profile_{u_name}_{file.filename}")
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                
                # Desintegrador de Virus (ClamAV)
                try:
                    result = subprocess.run(['clamscan', path], capture_output=True, text=True)
                    if "Infected files: 0" not in result.stdout:
                        os.remove(path)
                        return jsonify({"status": "error", "msg": "¡PELIGRO! Archivo borrado por detectar virus."}), 400
                except FileNotFoundError:
                    pass
                
                u['pic'] = f"/static/uploads/{filename}" 
            save_data(USER_DB, users)
            return jsonify({"status": "ok", "user": u})
    return jsonify({"status": "error"}), 404

# RUTA SOLUCIONADA: Nombre de archivo único por milisegundos para evitar repeticiones de audio
@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files: 
        return jsonify({"status": "error", "msg": "Sin archivo"}), 400
    file = request.files['audio']
    user = request.form.get('user', 'anonimo')
    timestamp = int(time.time() * 1000)
    filename = secure_filename(f"audio_{user}_{timestamp}.webm")
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return jsonify({"status": "ok", "url": f"/static/uploads/{filename}"})

@app.route('/upload_brol', methods=['POST'])
def upload_brol():
    if 'file' not in request.files: 
        return jsonify({"msg": "Error"}), 400
    file = request.files['file']
    filename = secure_filename(f"brol_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({"status": "ok", "msg": "¡Brol publicado!"})

@app.route('/get_brols', methods=['GET'])
def get_brols():
    videos = [{"title": f.split('_')[-1], "url": "/static/uploads/" + f} 
              for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.mov', '.webm'))]
    return jsonify(videos)

@app.route('/get_users', methods=['GET'])
def get_users():
    users = load_data(USER_DB)
    active_names = list(online_users.values())
    return jsonify([
        {
            "username": u['username'], 
            "online": u['username'] in active_names, 
            "pic": u['pic'],
            "bio": u.get('bio', '')
        } for u in users
    ])

@app.route('/get_history', methods=['POST'])
def get_history():
    data = request.json
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    return jsonify([m for m in load_data(MSG_DB) if m['room'] == room])

# --- SOCKETS: CHAT, PRESENCIA Y SEÑALIZACIÓN WEBRTC DE LLAMADAS ---

@socketio.on('set_identity')
def set_identity(data):
    online_users[request.sid] = data['user']
    emit('status_update', list(online_users.values()), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in online_users:
        del online_users[request.sid]
        emit('status_update', list(online_users.values()), broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('is_typing', {"user": data['user']}, room=room, include_self=False)

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
    save_data(MSG_DB, msgs)
    emit('new_msg', new_m, room=room)

# MÓDULO DE SEÑALIZACIÓN DE LLAMADAS
@socketio.on('call_user')
def handle_call_user(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('call_received', {"offer": data['offer'], "from": data['user']}, room=room, include_self=False)

@socketio.on('answer_call')
def handle_answer_call(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('call_answered', {"answer": data['answer']}, room=room, include_self=False)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('ice_candidate_received', {"candidate": data['candidate']}, room=room, include_self=False)

@socketio.on('end_call')
def handle_end_call(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('call_ended', {"from": data['user']}, room=room, include_self=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)

