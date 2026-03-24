import socketio
import base64
import time
import os

SIM_URL = 'http://localhost:5000'
AUDIO_FILE = r'D:\Florian\Freizeit\Balancing_Robot\Lokal\test.wav'
CHUNK_SIZE = 60000  # ~60 KB pro Chunk

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("✅ Verbunden zur Simulation!")

@sio.event
def disconnect():
    print("❌ Verbindung getrennt!")

@sio.event
def connect_error(data):
    print("❌ Verbindungsfehler:", data)

def send_audio_in_chunks(file_path):
    filesize = os.path.getsize(file_path)
    print(f"🎵 Gesamte Datei: {filesize} Bytes")

    sio.emit("play_audio_start")  # Server weiß, dass Audio startet

    with open(file_path, "rb") as f:
        chunk_number = 1
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            b64_chunk = base64.b64encode(chunk).decode('utf-8')
            sio.emit("play_audio_chunk", {'chunk': b64_chunk})
            print(f"✅ Chunk {chunk_number} gesendet ({len(chunk)} Bytes)")
            chunk_number += 1
            time.sleep(0.02)  # kleine Pause, Server kann mitkommen

    sio.emit("play_audio_end")  # Signalisiert Ende
    print("✅ Alle Chunks gesendet, Audio sollte starten.")

if __name__ == "__main__":
    try:
        if not sio.connected:
            sio.connect(SIM_URL, transports=['websocket'])
        send_audio_in_chunks(AUDIO_FILE)
        time.sleep(2)
    finally:
        if sio.connected:
            sio.disconnect()
            print("🔌 Verbindung beendet")