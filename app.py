import os
import json
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bro-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

USER_DB = 'data/users.json'

# Función para cargar usuarios [3, 4]
def load_users():
    if not os.path.exists(USER_DB): return []
    with open(USER_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

# Ruta de Login/Registro
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    users = load_users()
    # Verificamos si el usuario ya existe [5]
    for u in users:
        if u['username'] == data['username'] and u['password'] == data['password']:
            return {"status": "ok", "user": u['username']}
    
    # Si no existe, lo registramos (Sistema Simple) [2]
    users.append(data)
    with open(USER_DB, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)
    return {"status": "registered", "user": data['username']}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)

