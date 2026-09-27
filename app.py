import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' # Clave de seguridad para la sesión
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

# El "cableado": Cuando alguien manda un mensaje, el servidor lo recibe y lo reenvía a todos
@socketio.on('message')
def handle_message(data):
    print(f"Mensaje de {data['user']}: {data['msg']}")
    # Aquí es donde más adelante meteremos el "Filtro de Toxicidad" [3, 4]
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
