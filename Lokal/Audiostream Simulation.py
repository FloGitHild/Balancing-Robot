import socketio
import soundfile as sf
import numpy as np
import time
import base64

SIM_URL = 'http://127.0.0.1:5000'
AUDIO_FILE = r'D:\Florian\Freizeit\Balancing_Robot\Lokal\test.wav'
CHUNK_SIZE = 30000  # ~30 KB pro Chunk

sio = socketio.Client(logger=False, engineio_logger=False)

@sio.event
def connect():
    print("✅ Verbunden zur Simulation!")

@sio.event
def disconnect():
    print("❌ Verbindung getrennt!")

@sio.event
def connect_error(data):
    print("❌ Verbindungsfehler:", data)

def send_audio(file_path):
    # Audio als Byte-Array einlesen
    with open(file_path, 'rb') as f:
        data = f.read()
    total_size = len(data)
    print(f"🎵 Audio-Datei: {total_size} Bytes")

    sio.emit("play_audio_start")
    for i in range(0, total_size, CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        # Base64 nur falls Server es so erwartet
        b64_chunk = base64.b64encode(chunk).decode('utf-8')
        sio.emit("play_audio_chunk", {'chunk': b64_chunk})
        time.sleep(0.01)  # kleine Pause
    sio.emit("play_audio_end")
    print("✅ Audio fertig gesendet")

if __name__ == "__main__":
    sio.connect(SIM_URL, transports=['websocket'])
    send_audio(AUDIO_FILE)
    time.sleep(1)
    sio.disconnect()