import cv2
import face_recognition

# === Schritt 1: Bekannte Gesichter laden ===
# Lade Beispielbilder von bekannten Personen (jpg/png im Projektordner)
bild_alice = face_recognition.load_image_file("alice.jpg")
enc_alice = face_recognition.face_encodings(bild_alice)[0]

bild_bob = face_recognition.load_image_file("bob.jpg")
enc_bob = face_recognition.face_encodings(bild_bob)[0]

known_encodings = [enc_alice, enc_bob]
known_names = ["Alice", "Bob"]

# === Schritt 2: Kamera starten ===
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Frame verkleinern (schneller)
    small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Gesichter im aktuellen Bild finden
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Vergleich mit bekannten Gesichtern
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        name = "Unbekannt"

        # Falls Treffer vorhanden → den ersten nehmen
        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]

        # Koordinaten zurück auf Originalgröße skalieren
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Rechteck + Name ins Bild zeichnen
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Frame anzeigen
    cv2.imshow("Gesichtserkennung", frame)

    # ESC = beenden
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
