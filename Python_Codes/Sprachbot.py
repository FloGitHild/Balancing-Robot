import os
import json
from datetime import datetime, timezone
from openai import OpenAI
from pydub import AudioSegment, effects
import pyttsx3
import speech_recognition as sr
import time
import pygame

recognizer = sr.Recognizer()
mic = sr.Microphone()

# Optimierung für Stille-Erkennung
recognizer.pause_threshold = 2       # Sekunden Stille bis Stop
recognizer.non_speaking_duration = 1        # kurze Pausen innerhalb der Sprache ignorieren
recognizer.energy_threshold = 350             # Mikrofonempfindlichkeit

GPT_Model = "gpt-3.5-turbo"
client = OpenAI(api_key="sk-proj-1Xw0hRQ2YHk2pqhezmN6T3BlbkFJOzZNEtz1CoscN17iweOe")  # API-Key einsetzen
USER_DIR = "Python_Codes/Files/"
os.makedirs(USER_DIR, exist_ok=True)


listen_audio = USER_DIR + "xpAlto_Print_Complete.wav"
chat_end_audio = USER_DIR + "xpAlto_Error.wav"
reply_end_audio = USER_DIR + "CHIMES.WAV"
tts_file = USER_DIR + "temp_tts.wav"
robot_answer_audio = USER_DIR + "robot_voice.mp3"
# =====================================================================================================

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
    timestamp = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M:%S")
    history.append({"role": "user", "content": message, "timestamp": timestamp})
    save_user_history(person_name, history)

def ask_gpt_with_user_history(person_name, model):
    history = load_user_history(person_name)
    Akt_Uhrzeit = datetime.now()
    system_message = {
        "role": "system",
        "content": (
            "Du bist ein kleiner balancierender Roboter, der gerne Menschen hilft, "
            "sich gerne unterhält und manchmal auch etwas Schabernack im Kopf hat. "
            "Primär wirkst du kindlich und süß. Du reißt auch mal schlechte Witze "
            "und lachst selbst darüber. Du spielst gerne mit Menschen oder Haustieren."
            "Nutze den bisherigen Chatverlauf zwischen dir und dem Nutzer, um sinnvoll zu antworten. "
            "Gib nur Informationen über zeitliche Angaben, wenn danach gefragt wird. "
            "Vermeide Emojis oder dicke oder kursieve Schriften, da deine Ausgabe später von TTS gesprochen wird. "
            "Antworte möglichst kurz und menschlich, gerne mit Umgangssprache. "
            "Recherhiere unbeingt, um die antworten so präzise wie möglich zu machen. "
            "Setze zahlen"
        )
    }

    messages = [system_message] + [{"role": e["role"], "content": e["content"]} for e in history]

    try:
        response = client.chat.completions.create(model=model, messages=messages)
        assistant_message = response.choices[0].message.content
    except Exception as e:
        assistant_message = f" Fehler: {e}"

    history.append({
        "role": "assistant",
        "content": assistant_message,
        "timestamp": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M:%S")
    })
    save_user_history(person_name, history)

    return assistant_message

def text_to_robot_voice(text, filename):
    AudioSegment.converter = r"C:\ProgramData\ffmpeg-2025-09-18-full_build\bin\ffmpeg.exe"

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
    playaudio(filename)

def playaudio(file):
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.stop()
    pygame.mixer.quit()

def continuous_listen():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                print("\nHöre zu...")
                playaudio(listen_audio)
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
                try:
                    text = recognizer.recognize_google(audio, language="de-DE")
                    if text.strip():
                        print("Erkannter Text:", text)
                        return text
                except sr.UnknownValueError:
                    print("Sprache konnte nicht erkannt werden.")
                except sr.RequestError as e:
                    print(f"Fehler bei der Anfrage: {e}")
            except KeyboardInterrupt:
                print("\nBeende kontinuierliche Aufnahme.")
                break
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten: {e}")
    return None
            

# =====================================================================================================

if __name__ == "__main__":
    print("\n\n\nHi, ich bin dein kleiner Roboter, verrate mir nach dem Tonsignal deinen Namen.")
    text_to_robot_voice("Hi, ich bin dein kleiner Roboter! Verrate mir nach dem Tonsignal deinen Namen!", robot_answer_audio)
    
    text = None
    while text is None:
        text = continuous_listen()

    person_name = str(text.split()[0])
    print(f"Starte Chat mit {person_name}. Sage exit, stop, ende, oder quit um zu beenden.\n")
    text_to_robot_voice(f"Hi, {person_name}, ab jetzt kannst du mich alles fragen!", robot_answer_audio)

    Loop = True
    while Loop:
        user_input = continuous_listen()
        if user_input:
            for i in ["exit", "quit", "stop", "ende"]:
                if i.lower() in user_input.lower():
                    print("Chat beendet.")
                    Loop = False
                    playaudio(chat_end_audio)
                    break

            if Loop:
                add_user_message(person_name, user_input)
                reply = ask_gpt_with_user_history(person_name, GPT_Model)
                print(f"\nGPT: {reply}\n")
                text_to_robot_voice(reply, robot_answer_audio)
                playaudio(reply_end_audio)