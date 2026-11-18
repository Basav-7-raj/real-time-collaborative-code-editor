# CodeSync — Real-Time Collaborative Code Editor

A self-hosted collaborative code editor with real-time sync, multi-cursor presence,
live chat, and syntax highlighting for 8 languages.

## How to run (super easy)

### Windows
1. Install Python 3.9+ from https://python.org (tick "Add Python to PATH")
2. Double-click **run.bat** — it installs dependencies and starts the server.
3. Open http://localhost:5000 in your browser.

### macOS / Linux
```bash
chmod +x run.sh
./run.sh
```

### Manual
```bash
pip install -r requirements.txt
python server.py
```
Then open http://localhost:5000

## Demo flow for your presentation
1. Open http://localhost:5000 — enter your name, create a room, pick a language.
2. Copy the room URL (or 8-char code) and open it in a **second browser window**
   (or share with a friend on the same Wi-Fi using your PC's local IP, e.g.
   `http://192.168.x.x:5000/room/ABCD1234`).
3. Type in one window — watch it appear instantly in the other, with cursors + chat.

## Features
- ⚡ Real-time code sync via WebSockets (Socket.IO)
- 👥 Multi-user color-coded cursors
- 💬 In-room chat
- 🎨 Syntax highlighting: JS, TS, Python, HTML, CSS, SQL, JSON, Markdown
- 📊 Live stats (lines, chars, words, online users)
- 🔗 Shareable room links
- ▶ In-browser JS execution
- ↓ Code download
- No database — fully in-memory

## Project Structure
```
codesync/
├── server.py          # Flask + Socket.IO backend
├── requirements.txt   # Python dependencies
├── run.bat            # Windows launcher
├── run.sh             # macOS/Linux launcher
├── README.md
└── templates/
    └── index.html     # Frontend (CodeMirror + Socket.IO)
```

## Stack
- Backend: Python, Flask, Flask-SocketIO (threading mode — no extra deps)
- Frontend: Vanilla JS, CodeMirror 5, Socket.IO client
