import os, json, subprocess
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-net-ultra-security-2026'
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Usamos eventlet para manejar múltiples conexiones simultáneas [Historial]
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- BASES DE DATOS ---
USER_DB = 'data/users.json'
MSG_DB = 'data/messages.json'
# Diccionario para rastrear quién está en línea realmente
online_users = {} 

def load_data(path, default=[]):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f: json.dump(default, f)
        return default
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def save_data(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

# --- RUTAS ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    u_name, email, pwd = data.get('username'), data.get('email', ""), data.get('password')
    users = load_data(USER_DB)
    user_found = next((u for u in users if u['username'] == u_name or u['email'] == u_name), None)
    
    if user_found:
        if user_found['password'] == pwd: return jsonify({"status": "ok", "user": user_found})
        return jsonify({"status": "error", "msg": "Clave incorrecta"}), 401
    else:
        # Validación de Gmail y Unicidad [775, Historial]
        if not email.lower().endswith("@gmail.com"):
            return jsonify({"status": "error", "msg": "Registro denegado: Usa una cuenta @gmail.com"}), 400
        if any(u['username'] == u_name for u in users):
            return jsonify({"status": "error", "msg": "Arquitecto ya registrado con ese nombre"}), 400
        
        new_user = {"username": u_name, "email": email, "password": pwd, "bio": "Explorando BroNet", "pic": "/static/logo.png"}
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
                u['pic'] = f"/{path}" # Ruta absoluta para que cargue siempre [Historial]
            save_data(USER_DB, users)
            return jsonify({"status": "ok", "user": u})
    return jsonify({"status": "error"}), 404

@app.route('/upload_brol', methods=['POST'])
def upload_brol():
    if 'file' not in request.files: return jsonify({"msg": "Error"}), 400
    file = request.files['file']
    filename = secure_filename(f"brol_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return jsonify({"status": "ok", "msg": "Brol subido al feed!"})

@app.route('/get_brols', methods=['GET'])
def get_brols():
    # Escaneamos la carpeta de subidas para encontrar videos [5]
    videos = [{"title": "Brol Oficial", "url": "/static/uploads/" + f} 
              for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.mov'))]
    return jsonify(videos or [{"title": "Sube el primer Brol!", "url": ""}])

@app.route('/get_users', methods=['GET'])
def get_users():
    users = load_data(USER_DB)
    return jsonify([{"username": u['username'], "online": u['username'] in online_users.values(), "pic": u['pic']} for u in users])

@app.route('/get_history', methods=['POST'])
def get_history():
    data = request.json
    room = f"room_{min(data['user'], data['target'])}_{max(data['user'], data['target'])}"
    return jsonify([m for m in load_data(MSG_DB) if m['room'] == room])

# --- SOCKETS: PRESENCIA Y ESCRITURA ---
@socketio.on('connect')
def handle_connect():
    print("Nuevo túnel de datos abierto.")

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
