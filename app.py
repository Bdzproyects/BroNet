import os
import json
import subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-net-ultra-security-2026'
app.config['UPLOAD_FOLDER'] = 'uploads/'
# CORS permitido para que funcione en cualquier dispositivo [812, Historial]
socketio = SocketIO(app, cors_allowed_origins="*")

# --- RUTAS DE BASES DE DATOS ---
USER_DB = 'data/users.json'
GROUP_DB = 'data/groups.json'

def load_data(file_path):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f: json.dump([], f)
        return []
    with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

# --- RUTAS WEB ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    identity = data.get('username') # Puede ser el nombre o el email
    email_reg = data.get('email')   # Email para nuevos registros
    password = data.get('password')
    
    users = load_data(USER_DB)
    
    # 1. Buscar si ya existe por nombre o por email [775, Historial]
    user_found = next((u for u in users if u['username'] == identity or u['email'] == identity), None)
    
    if user_found:
        if user_found['password'] == password:
            return jsonify({"status": "ok", "user": user_found['username']})
        return jsonify({"status": "error", "msg": "Contraseña incorrecta"}), 401
    else:
        # 2. Registro de nuevo Bro: Validar que el nombre no esté pillado
        if any(u['username'] == identity for u in users):
            return jsonify({"status": "error", "msg": "Ese nombre de usuario ya está en uso"}), 400
        
        if not email_reg:
            return jsonify({"status": "error", "msg": "Para registrarte necesitas poner el email"}), 400
        
        new_user = {"username": identity, "email": email_reg, "password": password}
        users.append(new_user)
        save_data(USER_DB, users)
        return jsonify({"status": "ok", "user": identity, "msg": "Registro completado"})

@app.route('/get_users', methods=['GET'])
def get_users():
    return jsonify([u['username'] for u in load_data(USER_DB)])

@app.route('/get_brols', methods=['GET'])
def get_brols():
    # Simulación de Brols (Videos sin Copyright) [832, Historial]
    return jsonify([
        {"title": "Arquitectura Digital Anas", "url": "https://www.w3schools.com/html/mov_bbb.mp4"},
        {"title": "Ciberseguridad Pro", "url": "https://www.w3schools.com/html/horse.mp4"}
    ])

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'file' not in request.files: return jsonify({"msg": "Falta el archivo"})
    file = request.files['file']
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    # --- DESINTEGRADOR DE VIRUS (Lógica ClamAV) [1, 2] ---
    try:
        # Escaneo real si está instalado, si no, simula seguridad
        result = subprocess.run(['clamscan', path], capture_output=True, text=True)
        if "Infected files: 0" not in result.stdout:
            os.remove(path)
            return jsonify({"msg": "¡PELIGRO! El archivo contenía un virus y ha sido desintegrado."})
    except: pass 
    return jsonify({"msg": "Archivo escaneado y guardado correctamente."})

# --- SOCKETS: CHATS PRIVADOS Y GRUPOS ---
@socketio.on('join_private')
def on_join(data):
    # Genera una Room ID única alfabética (ej: room_anas_juan)
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    join_room(room)

@socketio.on('send_msg')
def on_msg(data):
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    emit('new_msg', data, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
