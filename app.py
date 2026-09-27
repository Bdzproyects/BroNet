import os
import json
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
