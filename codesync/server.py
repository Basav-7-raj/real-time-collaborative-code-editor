"""
CodeSync — Real-Time Collaborative Code Editor
Backend: Flask + Flask-SocketIO (threading mode — no eventlet/gevent needed)

Run:
    pip install -r requirements.txt
    python server.py
Then open http://localhost:5000
"""
from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid, time, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
# threading mode works out of the box on any Python version (no eventlet/gevent)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# ─── In-memory state ────────────────────────────────────────────────────────
rooms = {}       # room_id → {code, language, users, name, created_at, history}
users = {}       # sid → {name, color, room, cursor}

COLORS = ['#60a5fa','#34d399','#f472b6','#fb923c','#a78bfa','#38bdf8','#facc15','#fb7185','#4ade80','#e879f9']
STARTER = {
    'python':    '# Python\nprint("Hello, World!")\n\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Collaborator"))\n',
    'javascript':'// JavaScript\nconsole.log("Hello, World!");\n\nconst greet = (name) => {\n  return `Hello, ${name}!`;\n};\n\nconsole.log(greet("Collaborator"));\n',
    'typescript':'// TypeScript\nconst greet = (name: string): string => {\n  return `Hello, ${name}!`;\n};\n\nconsole.log(greet("Collaborator"));\n',
    'html':      '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <title>Hello</title>\n</head>\n<body>\n  <h1>Hello, World!</h1>\n  <p>Welcome to the collaborative editor!</p>\n</body>\n</html>\n',
    'css':       '/* CSS */\nbody {\n  font-family: system-ui, sans-serif;\n  background: #0f172a;\n  color: #e2e8f0;\n  margin: 0;\n  padding: 2rem;\n}\n\nh1 {\n  color: #60a5fa;\n  font-size: 2rem;\n}\n',
    'sql':       '-- SQL\nCREATE TABLE users (\n  id INT PRIMARY KEY AUTO_INCREMENT,\n  name VARCHAR(100) NOT NULL,\n  email VARCHAR(255) UNIQUE NOT NULL,\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);\n\nSELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY;\n',
    'json':      '{\n  "project": "Collaborative Editor",\n  "version": "1.0.0",\n  "contributors": [],\n  "features": [\n    "real-time sync",\n    "multi-cursor",\n    "syntax highlighting"\n  ]\n}\n',
    'markdown':  '# Collaborative Document\n\n## Introduction\nThis is a **real-time** collaborative editor.\n\n## Features\n- Live cursor tracking\n- Syntax highlighting\n- Room-based sessions\n\n> Start typing to collaborate!\n',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, 'templates', 'index.html')


def get_color(room_id):
    used = {u['color'] for u in users.values() if u.get('room') == room_id}
    for c in COLORS:
        if c not in used:
            return c
    return COLORS[len(used) % len(COLORS)]


def room_user_list(room_id):
    return [{'sid': sid, 'name': u['name'], 'color': u['color']}
            for sid, u in users.items() if u.get('room') == room_id]


def serve_html_file():
    """Read index.html directly from disk (avoids Jinja parsing of template braces)."""
    try:
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"<h1>Internal Server Error</h1><p>Could not read index.html: {e}</p>", 500


# ─── HTTP Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return Response(serve_html_file(), mimetype='text/html')


@app.route('/room/<room_id>')
def room(room_id):
    return Response(serve_html_file(), mimetype='text/html')


@app.route('/api/rooms', methods=['GET'])
def list_rooms():
    result = []
    for rid, r in rooms.items():
        result.append({
            'id': rid,
            'name': r['name'],
            'language': r['language'],
            'user_count': len(room_user_list(rid)),
            'created_at': r['created_at'],
        })
    return jsonify(result)


@app.route('/api/create-room', methods=['POST'])
def create_room():
    data = request.get_json(silent=True) or {}
    room_id = str(uuid.uuid4())[:8].upper()
    lang = data.get('language', 'javascript')
    rooms[room_id] = {
        'name': data.get('name', f'Room {room_id}'),
        'language': lang,
        'code': STARTER.get(lang, '// Start coding...\n'),
        'users': [],
        'created_at': int(time.time()),
        'history': [],
    }
    return jsonify({'room_id': room_id})


# ─── Socket Events ───────────────────────────────────────────────────────────
@socketio.on('join')
def on_join(data):
    sid = request.sid
    room_id = data.get('room_id')
    name = (data.get('name') or 'Anonymous')[:20]
    if room_id not in rooms:
        emit('error', {'msg': 'Room not found'})
        return
    color = get_color(room_id)
    users[sid] = {'name': name, 'color': color, 'room': room_id, 'cursor': {'line': 0, 'ch': 0}}
    join_room(room_id)
    r = rooms[room_id]
    emit('room_state', {
        'code': r['code'],
        'language': r['language'],
        'name': r['name'],
        'users': room_user_list(room_id),
        'my_sid': sid,
        'my_color': color,
    })
    emit('user_joined',
         {'sid': sid, 'name': name, 'color': color, 'users': room_user_list(room_id)},
         to=room_id, include_self=False)


@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in users:
        room_id = users[sid].get('room')
        name = users[sid]['name']
        del users[sid]
        if room_id:
            leave_room(room_id)
            emit('user_left',
                 {'sid': sid, 'name': name, 'users': room_user_list(room_id)},
                 to=room_id)


@socketio.on('code_change')
def on_code_change(data):
    sid = request.sid
    if sid not in users: return
    room_id = users[sid]['room']
    if room_id not in rooms: return
    code = data.get('code', '')
    rooms[room_id]['code'] = code
    emit('code_update', {'code': code, 'from': sid}, to=room_id, include_self=False)


@socketio.on('cursor_move')
def on_cursor(data):
    sid = request.sid
    if sid not in users: return
    room_id = users[sid]['room']
    users[sid]['cursor'] = data.get('cursor', {})
    emit('cursor_update', {
        'sid': sid,
        'name': users[sid]['name'],
        'color': users[sid]['color'],
        'cursor': data.get('cursor', {}),
        'selection': data.get('selection'),
    }, to=room_id, include_self=False)


@socketio.on('language_change')
def on_language_change(data):
    sid = request.sid
    if sid not in users: return
    room_id = users[sid]['room']
    if room_id not in rooms: return
    lang = data.get('language', 'javascript')
    rooms[room_id]['language'] = lang
    emit('language_update', {'language': lang, 'from': users[sid]['name']}, to=room_id)


@socketio.on('chat_message')
def on_chat(data):
    sid = request.sid
    if sid not in users: return
    room_id = users[sid]['room']
    emit('chat_message', {
        'from': users[sid]['name'],
        'color': users[sid]['color'],
        'msg': str(data.get('msg', ''))[:500],
        'ts': int(time.time()),
    }, to=room_id)


@socketio.on('request_run')
def on_run(data):
    sid = request.sid
    if sid not in users: return
    room_id = users[sid]['room']
    emit('run_notification', {'from': users[sid]['name']}, to=room_id)


if __name__ == '__main__':
    print('\n🚀 CodeSync running at  http://localhost:5000  (Ctrl+C to stop)\n')
    # debug=False + use_reloader=False -> stable single-process run for demos
    socketio.run(app, host='0.0.0.0', port=5000, debug=False,
                 allow_unsafe_werkzeug=True)
