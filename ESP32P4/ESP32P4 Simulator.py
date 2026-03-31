import base64
import cv2
import numpy as np
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except OSError:
    print("⚠️ PortAudio nicht verfügbar - Audio deaktiviert")
    AUDIO_AVAILABLE = False
    sd = None
    sf = None
from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO
import threading, time, io, sys

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# -----------------------------
# ROBOT STATE
# -----------------------------
state = {
    "mode": "Idle",
    "movement": "Stop",
    "speed": 0,
    "emotion": "Neutral",
    "head": {"rotate": 0, "tilt": 0},
    "arms": {"left": {"h":0,"v":0}, "right": {"h":0,"v":0}}
}

video_frame = None
audio_queue = []
temp_audio_chunks = []

# -----------------------------
# KAMERA THREAD
# -----------------------------
def camera_thread():
    global video_frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Kamera konnte nicht geöffnet werden!")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    print(f"✅ Kamera gestartet mit Auflösung: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    while True:
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode('.jpg', frame)
            video_frame = base64.b64encode(buffer).decode('utf-8')
        time.sleep(0.03)  # ~30 FPS

threading.Thread(target=camera_thread, daemon=True).start()

# -----------------------------
# AUDIO PLAYBACK THREAD
# -----------------------------
def play_audio_thread():
    while True:
        if audio_queue and AUDIO_AVAILABLE:
            try:
                audio_data, samplerate = audio_queue.pop(0)
                sd.play(audio_data, samplerate=samplerate)  # type: ignore
                sd.wait()  # type: ignore
            except Exception as e:
                print(f"⚠️ Audio-Fehler: {e}")
        else:
            time.sleep(0.05)

if AUDIO_AVAILABLE:
    threading.Thread(target=play_audio_thread, daemon=True).start()

# -----------------------------
# VIDEO GENERATOR
# -----------------------------
def generate_frames():
    global video_frame
    while True:
        if video_frame:
            frame = base64.b64decode(video_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)

# -----------------------------
# WEBPAGE
# -----------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>🤖 ESP32P4 Simulator</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<style>
body { font-family: Arial, sans-serif; background: #f0f2f5; color: #333; }
h1 { color: #2c3e50; }
h3 { margin-bottom: 5px; }
button { margin: 3px; padding: 5px 10px; font-size: 14px; cursor: pointer; }
input[type=range] { width: 200px; }
#status_box { 
    white-space: pre; 
    font-family: monospace; 
    border: 2px solid #2c3e50; 
    padding: 10px; 
    width: 420px; 
    height: 250px; 
    background: #fff; 
    overflow-y: auto; 
    margin-top: 10px;
}
.container { display: flex; gap: 40px; flex-wrap: wrap; }
.column { display: flex; flex-direction: column; }
</style>
</head>
<body>
<h1>🤖 ESP32P4 Robot Simulator</h1>

<div class="container">
    <div class="column">
        <img src="/video_feed" width="400" style="border:2px solid #2c3e50; margin-bottom:10px;"/>
        
        <button onclick="resetRobot()">🔄 Reset</button>
        
        <h3>Movement 🕹️</h3>
        <div>
            <button onclick="send('forward')">⬆️ Forward</button>
            <button onclick="send('backward')">⬇️ Backward</button>
            <button onclick="send('left')">⬅️ Left</button>
            <button onclick="send('right')">➡️ Right</button>
            <button onclick="send('stop')">⏹️ Stop</button>
        </div>

        <h3>Speed ⚡</h3>
        <input id="speed_slider" type="range" min="0" max="100" oninput="setSpeed(this.value)">

        <!-- Head -->
        Rotate: <input id="head_rotate" type="range" min="-90" max="90" oninput="setHead('rotate', this.value)">
        Tilt:   <input id="head_tilt" type="range" min="-90" max="90" oninput="setHead('tilt', this.value)">

        <!-- Arms -->
        Left H:  <input id="left_h" type="range" min="-90" max="90" oninput="setArm('left','h',this.value)">
        Left V:  <input id="left_v" type="range" min="-90" max="90" oninput="setArm('left','v',this.value)">
        Right H: <input id="right_h" type="range" min="-90" max="90" oninput="setArm('right','h',this.value)">
        Right V: <input id="right_v" type="range" min="-90" max="90" oninput="setArm('right','v',this.value)">
    </div>

    <div class="column">
        <h3>Modes 🛠️</h3>
        <div>
            <button onclick="setMode('Play')">🎮 Play</button>
            <button onclick="setMode('Assist')">🤝 Assist</button>
            <button onclick="setMode('Explore')">🌍 Explore</button>
            <button onclick="setMode('Auto')">⚙️ Auto</button>
            <button onclick="setMode('Idle')">💤 Idle</button>
        </div>

        <h3>Emotion 😃</h3>
        <div id="emotion">Neutral</div>

        <h3>Audio 🔊</h3>
        <div id="audio_indicator" style="font-size: 24px;">❌</div>

        <h3>Command Input 📝</h3>
        <input id="cmd" type="text" placeholder="Gib Befehl ein" 
            onkeydown="if(event.key==='Enter'){sendCmd();}">
        <button onclick="sendCmd()">Send</button>

        <h3>Status 📊</h3>
        <div id="status_box">Lade Status...</div>
        
        <h3>Letzte Eingabe 📨</h3>
        <div id="last_input" style="border:1px solid #ccc; padding:5px; background:#fff; width:420px;">–</div>
    </div>
</div>

<script>
var socket = io();
let audioTimeout;

function send(dir){ socket.emit('move', dir); }
function setSpeed(val){ socket.emit('speed', val); }
function setHead(type,val){ socket.emit('head',{type:type,val:val}); }
function setArm(side,axis,val){ socket.emit('arm',{side:side,axis:axis,val:val}); }
function setMode(mode){ socket.emit('mode', mode); }
function sendCmd(){
    let cmd = document.getElementById('cmd').value;
    if(cmd.trim() !== ""){
        socket.emit('cmd', cmd);
        document.getElementById('cmd').value = "";
        document.getElementById('last_input').innerText = cmd;  // <--- Zeigt die gesendete Nachricht
    }
}

function resetRobot(){
    socket.emit('reset');
}



function updateStatus(data){
    let text = `
Bewegung       : ${data.movement}
Geschwindigkeit: ${data.speed}
Kopf Rotate    : ${data.head.rotate}
Kopf Tilt      : ${data.head.tilt}
Arme L H       : ${data.arms.left.h}
Arme L V       : ${data.arms.left.v}
Arme R H       : ${data.arms.right.h}
Arme R V       : ${data.arms.right.v}
Modus          : ${data.mode}
Emotion        : ${data.emotion}
Audio          : ${data.audio ? "🔊" : "❌"}
`;
    document.getElementById('status_box').innerText = text;

    // Update Slider Werte live
    document.getElementById('speed_slider').value = data.speed;
    document.getElementById('head_rotate').value = data.head.rotate;
    document.getElementById('head_tilt').value = data.head.tilt;
    document.getElementById('left_h').value = data.arms.left.h;
    document.getElementById('left_v').value = data.arms.left.v;
    document.getElementById('right_h').value = data.arms.right.h;
    document.getElementById('right_v').value = data.arms.right.v;
    document.getElementById('audio_indicator').innerText = data.audio ? "🔊" : "❌";
}

socket.on('state', function(data){
    if(!data.audio) data.audio = false;
    updateStatus(data);
    document.getElementById('emotion').innerText = data.emotion;
});

socket.on('audio_stream', function(data){
    if(data === 'start'){
        socket.emit('audio_active', true);
        if(audioTimeout) clearTimeout(audioTimeout);
        audioTimeout = setTimeout(()=>{
            socket.emit('audio_active', false);
        }, 500);
    }
});


</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# -----------------------------
# SOCKET EVENTS
# -----------------------------
@socketio.on('move')
def move(direction): state['movement'] = direction
@socketio.on('speed')
def speed(val): state['speed'] = int(val)
@socketio.on('head')
def head(data): state['head'][data['type']] = int(data['val'])
@socketio.on('arm')
def arm(data): state['arms'][data['side']][data['axis']] = int(data['val'])
@socketio.on('mode')
def mode(m): state['mode'] = m

# -----------------------------
# SOCKET EVENT: Command
# -----------------------------
@socketio.on('cmd')
def cmd(c):
    if "happy" in c: state['emotion']="Freudig"
    elif "sad" in c: state['emotion']="Traurig"
    elif "curious" in c: state['emotion']="Neugierig"
    elif "relaxed" in c: state['emotion']="Entspannt"

    # Letzte Eingabe speichern
    state['last_input'] = c

# -----------------------------
# AUDIO CHUNKS HANDLING
# -----------------------------
@socketio.on('play_audio_start')
def play_audio_start():
    global temp_audio_chunks
    temp_audio_chunks = []
    print("📥 Audio-Datei startet Empfang...")

@socketio.on('play_audio_chunk')
def play_audio_chunk(data):
    global temp_audio_chunks
    chunk_bytes = base64.b64decode(data['chunk'])
    temp_audio_chunks.append(chunk_bytes)
    print(f"🔊 Chunk empfangen, Größe: {len(chunk_bytes)} Bytes")

@socketio.on('play_audio_end')
def play_audio_end():
    if not AUDIO_AVAILABLE:
        return
    global temp_audio_chunks
    full_audio = b''.join(temp_audio_chunks)
    file_like = io.BytesIO(full_audio)
    audio_data, samplerate = sf.read(file_like, dtype='int16')  # type: ignore
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1).astype(np.int16)
    audio_queue.append((audio_data, samplerate))
    print(f"🎵 Audio in Queue, {len(audio_data)} Samples, {samplerate} Hz")
    
    b64_audio = base64.b64encode(full_audio).decode('utf-8')
    socketio.emit('play_audio', b64_audio)
    print(f"📢 play_audio Event gesendet an Website, Größe: {len(b64_audio)} Zeichen")
    
    state['audio'] = True
    socketio.emit('audio_stream','start')
    def reset_audio():
        time.sleep(0.5)
        state['audio'] = False
    socketio.start_background_task(reset_audio)
    temp_audio_chunks = []

@socketio.on('reset')
def reset():
    state['mode'] = "Idle"
    state['movement'] = "Stop"
    state['speed'] = 50
    state['head'] = {"rotate":0,"tilt":0}
    state['arms'] = {"left":{"h":0,"v":0}, "right":{"h":0,"v":0}}
    state['emotion'] = "Neutral"
    state['last_input'] = ""  # Optional: letzte Eingabe löschen
    print("🔄 Robot state zurückgesetzt")

@socketio.on('vision_update')
def vision_update(data):
    pass


# -----------------------------
# BROADCAST LOOP (Auto-Update + Terminal Debug)
# -----------------------------
def broadcast():
    while True:
        if video_frame: socketio.emit('video', video_frame)

        # Audio-Flag für Anzeige
        data_to_send = state.copy()
        if 'audio' not in data_to_send: data_to_send['audio'] = False
        socketio.emit('state', data_to_send)

        # Terminal Live-Dashboard
        text = (
            f"Bewegung       : {state['movement']}\n"
            f"Geschwindigkeit: {state['speed']}\n"
            f"Kopf Rotate    : {state['head']['rotate']}\n"
            f"Kopf Tilt      : {state['head']['tilt']}\n"
            f"Arme L H       : {state['arms']['left']['h']}\n"
            f"Arme L V       : {state['arms']['left']['v']}\n"
            f"Arme R H       : {state['arms']['right']['h']}\n"
            f"Arme R V       : {state['arms']['right']['v']}\n"
            f"Modus          : {state['mode']}\n"
            f"Emotion        : {state['emotion']}\n"
            f"Audio          : {'🔊' if data_to_send.get('audio',False) else '❌'}\n"
            f"Eingabe        : {state.get('last_input','')}\n"
        )
        sys.stdout.write("\033[H\033[J" + text)
        sys.stdout.flush()

        socketio.sleep(0.05)  # 1 second interval

socketio.start_background_task(broadcast)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("🚀 Simulator läuft auf http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)