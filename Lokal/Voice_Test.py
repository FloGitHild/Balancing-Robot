import subprocess
import uuid
import os
from pydub import AudioSegment
import simpleaudio as sa

MODEL = "de_DE-thorsten-high.onnx"


# ---------- Piper ----------
def tts_piper(text):
    filename = f"/tmp/voice_{uuid.uuid4().hex}.wav"

    cmd = [
        "piper",
        "--model", MODEL,
        "--output_file", filename
    ]

    result = subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        capture_output=True
    )

    if result.returncode != 0 or not os.path.exists(filename):
        print("❌ Piper Fehler")
        print(result.stderr.decode())
        return None

    return filename


# ---------- Pitch (OHNE Speed kaputt zu machen) ----------
def change_pitch(sound, semitones=4):
    # saubere Pitch-Änderung (weniger Artefakte)
    new_rate = int(sound.frame_rate * (2 ** (semitones / 12)))

    pitched = sound._spawn(sound.raw_data, overrides={
        "frame_rate": new_rate
    })

    # zurück auf normale Rate → verhindert Speed-Explosion
    return pitched.set_frame_rate(44100)


# ---------- Hauptfunktion ----------
def robot_voice(text):
    wav_file = tts_piper(text)

    if wav_file is None:
        return

    # ⚠️ IMMER ORIGINAL neu laden → kein stacking
    sound = AudioSegment.from_wav(wav_file)

    # Grundformat fixieren
    sound = sound.set_frame_rate(44100).set_channels(1).set_sample_width(2)

    # 🎛️ Effekte (stabil)
    sound = change_pitch(sound, semitones=10)  # höher
    sound = sound.speedup(playback_speed=0.9)  # leicht schneller

    # nochmal stabilisieren
    sound = sound.set_frame_rate(44100)

    # 🎧 Abspielen
    play_obj = sa.play_buffer(
        sound.raw_data,
        num_channels=1,
        bytes_per_sample=2,
        sample_rate=44100
    )
    play_obj.wait_done()

    # 🧹 Datei löschen (wichtig!)
    os.remove(wav_file)


# ---------- TEST ----------
robot_voice("Hey! Ich bin dein Roboter! Lass uns was Cooles machen!")