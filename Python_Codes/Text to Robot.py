import pyttsx3
from pydub import AudioSegment, effects

def text_to_robot_voice(text, filename="robot_voice.mp3"):
    # ---- Pfad zu ffmpeg setzen ----
    from pydub.utils import which
    AudioSegment.converter = r"C:\ProgramData\ffmpeg-2025-09-18-full_build\bin\ffmpeg.exe"

    tts_file = "temp_tts.wav"

    # ---- Schritt 1: Text mit pyttsx3 in WAV speichern ----
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)  # freundlicher Sprechfluss
    engine.setProperty("volume", 1.0)
    engine.save_to_file(text, tts_file)
    engine.runAndWait()

    # ---- Schritt 2: Audio mit pydub laden ----
    audio = AudioSegment.from_wav(tts_file)

    # ---- Schritt 3: Tonhöhe leicht anheben (süßlicher Klang) ----
    octaves = 0.3  # +0.2 Oktaven (~15 % höher)
    new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
    pitched = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate})
    pitched = pitched.set_frame_rate(audio.frame_rate)

    # ---- Schritt 4: Sanftes Echo hinzufügen ----
    # Leisere Kopie (-8 dB), 60 ms verzögert
    echo = pitched.overlay(pitched - 8, position=60)

    # ---- Schritt 5: Normalisieren (damit es sauber klingt) ----
    final_audio = effects.normalize(echo)

    # ---- Schritt 6: Exportieren ----
    final_audio.export(filename, format="mp3")
    print(f"✅ Audio gespeichert als {filename}")



mein_text = "Hallo! Ich bin dein süßer Roboterfreund. Ich freue mich, mit dir zu sprechen."
text_to_robot_voice(mein_text)
