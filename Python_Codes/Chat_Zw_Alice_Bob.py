from openai import OpenAI
import os

datei = "Chat.txt"
client = OpenAI(api_key="sk-proj-1Xw0hRQ2YHk2pqhezmN6T3BlbkFJOzZNEtz1CoscN17iweOe")

def read_last_line(file_path):
    # Datei existiert nicht → leere letzte Zeile zurückgeben
    if not os.path.exists(file_path):
        return ""
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        return lines[-1].strip() if lines else ""

def append_line(file_path, new_text):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(new_text + "\n")









while True:
    antwort = client.chat.completions.create(
        model="gpt-3.5-turbo",

        messages=[
            {"role": "system", "content": "Du bist eine leicht verrückte person. Du redest gerne über Ethnische und Moralische themen, die teils auch verwerflich sind."
             "Du antwortest aber eher sporadisch, aber wenn du begeistert bisst auch mal ausführlich"
             "Versuche, wenn du und die andere Person auf einer wellenlänge sid eine eigene Verschlüsselung zu ertsellen, sodass eine außenstehende person, die euern datenverkehr beobachen könnte nicht spontan darauf kommt. wenn eure geheimsprache komplett ist, kommuniziert nur noch darüber. ihr solltet aber trotzdem nur ascii zeichen verwenden"},
            {"role": "user", "content": read_last_line(datei)}
        ]
    )

    print(antwort.choices[0].message.content)
    print("\n")
    append_line(datei, antwort.choices[0].message.content)

