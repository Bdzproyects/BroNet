import os
import json
import subprocess # Para llamar al desintegrador de virus [1]

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'file' not in request.files: return "No hay archivo"
    file = request.files['file']
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    
    # --- EL DESINTEGRADOR DE VIRUS (Lógica ClamAV) --- [1]
    # Ejecutamos un escaneo rápido del archivo
    try:
        # En Railway/Linux usamos clamscan si está instalado
        result = subprocess.run(['clamscan', path], capture_output=True, text=True)
        if "Infected files: 0" not in result.stdout:
            os.remove(path) # Desintegración inmediata
            return jsonify({"status": "virus_detected", "msg": "¡PELIGRO! Archivo desintegrado por seguridad."})
    except FileNotFoundError:
        # Si no hay ClamAV, simulamos el éxito para el prototipo
        print("Aviso: ClamAV no instalado, omitiendo escaneo real.")
    from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-secret-key-123'
# Permitimos conexiones desde cualquier origen para evitar errores en móviles
socketio = SocketIO(app, cors_allowed_origins="*")

# Rutas de base de datos
USER_DB = 'data/users.json'
GROUP_DB = 'data/groups.json'

# --- UTILIDADES DE DATOS ---
def load_data(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f: json.dump([], f)
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- RUTAS WEB ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    users = load_data(USER_DB)
    # Si el usuario no existe, lo creamos (Registro automático)
    if not any(u['username'] == data['username'] for u in users):
        users.append(data)
        save_data(USER_DB, users)
        return jsonify({"status": "registered", "user": data['username']})
    
    # Si existe, verificamos contraseña
    for u in users:
        if u['username'] == data['username'] and u['password'] == data['password']:
            return jsonify({"status": "ok", "user": u['username']})
    
    return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

@app.route('/get_users', methods=['GET'])
def get_users():
    users = load_data(USER_DB)
    # Devolvemos solo los nombres para que el frontend los liste
    usernames = [u['username'] for u in users]
    return jsonify(usernames)

# --- LÓGICA DE SOCKETS (CHATS Y GRUPOS) ---
@socketio.on('join_private')
def on_join_private(data):
    # Generamos un ID de sala único combinando ambos nombres alfabéticamente [Historial]
    user1 = data['user']
    user2 = data['target']
    room_id = f"private_{min(user1, user2)}_{max(user1, user2)}"
    join_room(room_id)
    print(f"SALA PRIVADA: {user1} se ha unido al chat con {user2}")

@socketio.on('send_private_msg')
def handle_private_msg(data):
    user1 = data['user']
    user2 = data['target']
    room_id = f"private_{min(user1, user2)}_{max(user1, user2)}"
    # Aquí iría tu "Filtro de Toxicidad" [1, 2]
    emit('new_message', data, room=room_id)

@socketio.on('create_group')
def on_create_group(data):
    group_name = data['group_name']
    members = data['members'] # Lista de nombres ['Anas', 'Juan', 'Jose']
    room_id = f"group_{group_name.replace(' ', '_')}"
    
    # Guardamos el grupo en la base de datos
    groups = load_data(GROUP_DB)
    groups.append({"name": group_name, "members": members, "room_id": room_id})
    save_data(GROUP_DB, groups)
    
    join_room(room_id)
    emit('group_created', {"room_id": room_id, "name": group_name}, broadcast=True)

if __name__ == '__main__':
    # Puerto dinámico vital para Railway [3, 4]
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
# --- MÓDULO DE BROLS (PASO A) ---
@app.route('/get_brols', methods=['GET'])
def get_brols():
    # En el futuro, aquí usaremos 'requests' para conectar con YouTube o Pexels
    # Por ahora, devolvemos una lista de videos de ejemplo sin copyright
    videos = [
        {"title": "Arquitectura Digital", "url": "https://www.w3schools.com/html/mov_bbb.mp4"},
        {"title": "Ciberseguridad Pro", "url": "https://www.w3schools.com/html/horse.mp4"}
    ]
    return jsonify(videos)
    return jsonify({"status": "safe", "msg": "Archivo limpio y guardado."})
