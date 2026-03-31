def continuous_listen(silence_sec):
    """
    Kontinuierliche Spracherkennung:
    - stoppt Aufnahme nach 'silence_sec' Sekunden Stille
    - gibt automatisch erkannte Sätze aus
    """
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    # Optimierung für Stille-Erkennung
    recognizer.pause_threshold = silence_sec       # Sekunden Stille bis Stop
    recognizer.non_speaking_duration = 0.5        # kurze Pausen innerhalb der Sprache ignorieren
    recognizer.energy_threshold = 300             # Mikrofonempfindlichkeit

    print("Bereit für Spracheingabe. Sprich einfach... (Strg+C zum Beenden)")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        while True:
            try:
                print("\nHöre zu...")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
                try:
                    text = recognizer.recognize_google(audio, language="de-DE")
                    if text.strip():
                        print("Erkannter Text:", text)
                except sr.UnknownValueError:
                    print("Sprache konnte nicht erkannt werden.")
                except sr.RequestError as e:
                    print(f"Fehler bei der Anfrage: {e}")
            except KeyboardInterrupt:
                print("\nBeende kontinuierliche Aufnahme.")
                break
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten: {e}")