import os
import json
from datetime import datetime, timezone
from openai import OpenAI
from pydub import AudioSegment, effects
import pyttsx3

client = OpenAI(api_key="sk-proj-1Xw0hRQ2YHk2pqhezmN6T3BlbkFJOzZNEtz1CoscN17iweOe")
USER_DIR = "user_files"
os.makedirs(USER_DIR, exist_ok=True)

def get_user_file(person_name):
    return os.path.join(USER_DIR, f"{person_name.replace(' ','_')}.json")

def load_user_history(person_name):
    path = get_user_file(person_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_history(person_name, history):
    with open(get_user_file(person_name), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_user_message(person_name, message):
    history = load_user_history(person_name)
    timestamp = datetime.now(timezone.utc).isoformat()
    history.append({"role":"user","content":message,"timestamp":timestamp})
    save_user_history(person_name, history)

def ask_gpt_with_user_history(person_name, model="gpt-3.5-turbo"):
    history = load_user_history(person_name)

    system_message = {
        "role":"system",
        "content":(
            "Du bist ein hilfreicher Assistent. "
            "Nutze die bisherigen Nachrichten des Benutzers, um sinnvoll zu antworten. "
            "Gib keinerlei Timestamps oder Zeitinformationen zurück."
        )
    }

    # Wichtig: Nur content, keine Timestamps
    messages = [system_message] + [{"role":e["role"], "content":e["content"]} for e in history]

    try:
        response = client.chat.completions.create(model=model, messages=messages)
        assistant_message = response.choices[0].message.content
    except Exception as e:
        assistant_message = f" Fehler: {e}"

    # Antwort intern speichern (mit Timestamp, aber GPT sieht sie nicht)
    history.append({"role":"assistant","content":assistant_message,"timestamp":datetime.now(timezone.utc).isoformat()})
    save_user_history(person_name, history)

    return assistant_message  # Nur Text

def text_to_robot_voice(text, filename="robot_voice.mp3"):
    AudioSegment.converter = r"C:\ProgramData\ffmpeg-2025-09-18-full_build\bin\ffmpeg.exe"
    tts_file = "temp_tts.wav"

    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.setProperty("volume", 1.0)
    engine.save_to_file(text, tts_file)
    engine.runAndWait()

    audio = AudioSegment.from_wav(tts_file)
    octaves = 0.3
    new_sample_rate = int(audio.frame_rate * (2.0 ** octaves))
    pitched = audio._spawn(audio.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(audio.frame_rate)
    echo = pitched.overlay(pitched - 8, position=60)
    final_audio = effects.normalize(echo)
    final_audio.export(filename, format="mp3")
    print(f"Audio gespeichert als {filename}")

if __name__ == "__main__":
    person_name = input("Name der Person: ")
    print(f"Starte Chat mit {person_name}. Tippe 'exit' zum Beenden.\n")

    while True:
        user_input = input(f"{person_name}: ")
        if user_input.lower() in ["exit","quit"]:
            print("Chat beendet.")
            break

        add_user_message(person_name, user_input)
        reply = ask_gpt_with_user_history(person_name)
        print(f"GPT: {reply}\n")
        text_to_robot_voice(reply)
