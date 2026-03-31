import socketio
import soundfile as sf
import numpy as np
import time
import base64
import os

SIM_URL = 'http://127.0.0.1:5000'
CHUNK_SIZE = 30000

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
    if not os.path.exists(file_path):
        print(f"❌ Datei nicht gefunden: {file_path}")
        return
    
    with open(file_path, 'rb') as f:
        data = f.read()
    total_size = len(data)
    print(f"🎵 Audio-Datei: {total_size} Bytes")

    sio.emit("play_audio_start")
    for i in range(0, total_size, CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        b64_chunk = base64.b64encode(chunk).decode('utf-8')
        sio.emit("play_audio_chunk", {'chunk': b64_chunk})
        time.sleep(0.01)
    sio.emit("play_audio_end")
    print("✅ Audio fertig gesendet")

def play_tts(text, voice="default"):
    """Generate TTS and send to robot"""
    try:
        import requests
        
        response = requests.post(
            "http://localhost:5002/tts",
            json={"text": text, "voice": voice},
            timeout=30
        )
        
        if response.status_code == 200:
            audio_data = response.content
            sio.emit("play_audio_start")
            
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i:i+CHUNK_SIZE]
                b64_chunk = base64.b64encode(chunk).decode('utf-8')
                sio.emit("play_audio_chunk", {'chunk': b64_chunk})
                time.sleep(0.01)
            
            sio.emit("play_audio_end")
            print(f"✅ TTS gesendet: {text[:50]}...")
        else:
            print(f"❌ TTS Fehler: {response.status_code}")
    except Exception as e:
        print(f"❌ TTS Fehler: {e}")

def generate_tts_file(text, output_path, voice="default"):
    """Generate TTS to a file (for offline use)"""
    try:
        import requests
        
        response = requests.post(
            "http://localhost:5002/tts",
            json={"text": text, "voice": voice},
            timeout=30
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
    except Exception as e:
        print(f"❌ TTS Generierung Fehler: {e}")
    return None

if __name__ == "__main__":
    sio.connect(SIM_URL, transports=['websocket'])
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Audio file to send")
    parser.add_argument("--tts", help="Text to convert to speech")
    args = parser.parse_args()
    
    if args.file:
        send_audio(args.file)
    elif args.tts:
        play_tts(args.tts)
    else:
        print("Usage: python audio_client.py <file.wav>")
        print("   or: python audio_client.py --tts 'Hello world'")
    
    time.sleep(1)
    sio.disconnect()
