import os
import json
import re
import time
from datetime import datetime
from openai import OpenAI
import speech_recognition as sr
import pygame
from pydub import AudioSegment, effects
import pyttsx3

# =========================
# KONFIGURATION
# =========================
MODEL = "gpt-4.1"
USER_DIR = "Python_Codes/Files/"
os.makedirs(USER_DIR, exist_ok=True)

client = OpenAI(api_key="sk-proj-1Xw0hRQ2YHk2pqhezmN6T3BlbkFJOzZNEtz1CoscN17iweOe")

recognizer = sr.Recognizer()
mic = sr.Microphone()
recognizer.pause_threshold = 1.3
recognizer.dynamic_energy_threshold = True
        
pygame.mixer.init()


# =========================
# AUDIO FILES
# =========================
listen_audio = os.path.join(USER_DIR, "xpAlto_Print_Complete.wav")
chat_end_audio = os.path.join(USER_DIR, "xpAlto_Error.wav")
reply_end_audio = os.path.join(USER_DIR, "CHIMES.WAV")
tts_file = os.path.join(USER_DIR, "temp_tts.wav")
robot_audio = os.path.join(USER_DIR, "robot_voice.mp3")

# =========================
# AUDIO PLAYER
# =========================
def playaudio(file):
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

# =========================
# USER DATA
# =========================
def get_user_file(name):
    return os.path.join(USER_DIR, f"{name}.json")

def load_user_data(name):
    if os.path.exists(get_user_file(name)):
        with open(get_user_file(name), "r", encoding="utf-8") as f:
            return json.load(f)
    return {"profile": {}, "history": []}

def save_user_data(name, data):
    with open(get_user_file(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# MEMORY EXTRACTION
# =========================
def extract_memory(text, profile):
    t = text.lower()
    age = re.search(r"ich bin (\d+)", t)
    if age:
        profile["age"] = int(age.group(1))
    city = re.search(r"ich wohne in (\w+)", t)
    if city:
        profile["city"] = city.group(1)
    hobby = re.search(r"mein hobby ist (\w+)", t)
    if hobby:
        profile.setdefault("hobbies", [])
        if hobby.group(1) not in profile["hobbies"]:
            profile["hobbies"].append(hobby.group(1))
    dog = re.search(r"mein hund heißt (\w+)", t)
    if dog:
        profile.setdefault("pets", [])
        profile["pets"].append({"type": "dog","name": dog.group(1)})
    return profile

# =========================
# MESSAGE RANKING
# =========================
def rank_messages(history, query, max_results=6):
    q_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for m in history:
        words = set(re.findall(r"\w+", m["content"].lower()))
        score = len(q_words & words)
        if score > 0:
            scored.append((score, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:max_results]]

# =========================
# CONTEXT BUILDER
# =========================
def build_messages(profile, history, query):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory_text = "User Infos:\n"
    for k, v in profile.items():
        memory_text += f"{k}: {v}\n"

    system_prompt = f"""
Du bist Robo, ein kleiner hilfsbereiter empathischer Roboter. Immer lustig drauf.
Antworte so, als würdest du persönlich mit dem Nutzer sprechen.
Kurze, natürliche Antworten, Quellen als kurze Domain am Ende (z.B. Wetter.de). Nutze Websearch nur, wenn unbedingt nötig.
Keine Emojis, Zahlen als Ziffern, keine Formatierungen, keine umbrüche, nur der Standard-Ascii-Satz einer Tastatur.
Mache bei Satzpausen immer das Satzzeichen und anschließend 2 leerzeichen.
Vermeide '[keine Zeit]' oder '[aktuelle_zeit]' in deinen antworten
Antwort im metrischen System, lasse das C bei Grad weg, wenn nicht unbedingt erforderlich.
Aktuelles datum & Uhrzeit: {now}.
Nutzerinfos:
{memory_text}
"""
    relevant = rank_messages(history[:-10], query)
    recent = history[-10:]
    messages = [{"role": "system", "content": system_prompt}]
    for m in relevant + recent:
        ts = m.get("timestamp", "keine Zeit")
        messages.append({"role": m["role"], "content": f"[{ts}] {m['content']}"})
    messages.append({"role": "user", "content": query})
    return messages

# =========================
# GPT
# =========================
def ask_gpt(name, query):
    """Fragt GPT, speichert Antwort + Zeitstempel"""
    data = load_user_data(name)
    profile = data["profile"]
    history = data["history"]

    # Zeitstempel der Anfrage
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Memory aktualisieren
    profile = extract_memory(query, profile)

    # GPT-Nachrichten aufbauen
    messages = build_messages(profile, history, query)

    try:
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search"}],
            input=messages
        )
        answer = response.output_text
        answer = clean_gpt_response(answer)
        answer = shorten_sources(answer)
    except Exception as e:
        answer = f"Fehler bei Recherche: {e}"

    # Historie aktualisieren mit Zeitstempel
    history.append({"role": "user", "content": query, "timestamp": now})
    history.append({"role": "assistant", "content": answer, "timestamp": now})

    data["profile"] = profile
    data["history"] = history
    save_user_data(name, data)

    return answer

# =========================
# TTS ROBOT VOICE
# =========================
def robot_voice(text):
        engine= pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, tts_file)
        engine.runAndWait()
        
        audio = AudioSegment.from_wav(tts_file)
        # Pitch & Echo Effekt
        pitched = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate*1.3)}).set_frame_rate(audio.frame_rate)
        echo = pitched.overlay(pitched-8, position=60)
        final = effects.normalize(echo)
        final.export(robot_audio, format="mp3")
        playaudio(robot_audio)
        return
# =========================
# SPEECH RECOGNITION
# =========================
def listen():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, 0.4)
        print("Höre zu...")
        playaudio(listen_audio)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language="de-DE")
            print("User:", text)
            return text
        except:
            return None

# =========================
# CLEAN GPT RESPONSE
# =========================
def clean_gpt_response(text):
    text = re.sub(r"", "", text, flags=re.DOTALL)
    text = re.sub(r"\(https?://[^\s)]+\)", "", text)
    text = text.replace("xx","")
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

# =========================
# SHORTEN SOURCES
# =========================
def shorten_sources(text):
    def repl(m):
        url = m.group(1)
        domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
        return f"({domain})"
    return re.sub(r"\((https?://[^\s)]+)\)", repl, text)

# =========================
# MAIN LOOP
# =========================
print("\n\nHi! Ich bin dein kleiner Roboter. Wie heißt du?")
robot_voice("Hi! Ich bin dein kleiner Roboter. Wie heißt du?")

name = None
while not name:
    name = listen()
person = name.split()[0]

print(f"Hi {person}! Frag mich alles was du willst.")
robot_voice(f"Hi {person}! Frag mich alles was du willst.")

print("Chat gestartet mit", person)

while True:
    user = listen()
    if not user:
        continue
    if any(x in user.lower() for x in ["exit", "stop", "ende", "quit"]):
        playaudio(chat_end_audio)
        break
    reply = ask_gpt(person, user)
    print("GPT:", reply)
    robot_voice(reply)
    playaudio(reply_end_audio)