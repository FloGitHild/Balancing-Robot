# Vision_Main_Threaded.py
import cv2
from detector import Detector
from face_db import FaceDB
import threading
import time
import face_recognition

STREAM_URL = "http://localhost:5000/video_feed"
Face_Recog_Tolerance = 0.6
Object_Confidence_Threshold = 0.6  # anpassbar

# ---------- Init ----------
detector = Detector()
db = FaceDB()

cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print("❌ Stream konnte nicht geöffnet werden")
    exit()

print("✅ Stream läuft!")
cv2.namedWindow("Detection", cv2.WINDOW_NORMAL)

# ---------- Shared Variables ----------
latest_frame = None
frame_lock = threading.Lock()
interval = 1.0  # Analyse alle 1.0 Sekunden (~1 FPS)
last_time = 0

last_faces = []
last_names = []
last_objects = []

# ---------- Thread: Frames immer aktuell ----------
def frame_reader():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        with frame_lock:
            latest_frame = frame

# ---------- Funktion: Gesichter hinzufügen ----------
def add_face_interactively(frame, detector, db):
    faces = detector.detect_faces(frame)
    if not faces:
        return

    for f in faces:
        enc = f["encoding"]
        matches = face_recognition.compare_faces(db.encodings, enc, tolerance=Face_Recog_Tolerance)
        if True not in matches:
            top, right, bottom, left = f["box"]
            face_img = frame[top:bottom, left:right]
            if face_img.size == 0:
                continue
            cv2.imshow("Neues Gesicht erkannt", face_img)
            cv2.waitKey(1)
            name = input("Neues Gesicht erkannt! Bitte Name eingeben: ")
            db.add_face(enc, name, n_samples=5)
            print(f"✅ Gesicht '{name}' gespeichert!")
            cv2.destroyWindow("Neues Gesicht erkannt")

# Start Frame Reader Thread
threading.Thread(target=frame_reader, daemon=True).start()

# ---------- Hauptloop ----------
while True:
    current_time = time.time()

    # 🔹 Hol den aktuellsten Frame
    with frame_lock:
        frame_copy = latest_frame.copy() if latest_frame is not None else None
    if frame_copy is None:
        continue

    # 🔹 Detection Intervall (für FPS-Kontrolle)
    if current_time - last_time > interval:
        last_time = current_time

        # ---------- Gesichter ----------
        faces = detector.detect_faces(frame_copy)
        names = []

        for f in faces:
            enc = f["encoding"]
            matches = face_recognition.compare_faces(db.encodings, enc, tolerance=Face_Recog_Tolerance)
            if True in matches:
                idx = matches.index(True)
                names.append(db.names[idx])
            else:
                names.append("Unknown")

        # Neues Gesicht abfragen
        add_face_interactively(frame_copy, detector, db)
        last_faces = faces
        last_names = names

        # ---------- Objekte ----------
        objects = detector.detect_objects(frame_copy, confidence_threshold=Object_Confidence_Threshold)
        last_objects = objects

        # ---------- Terminal-Ausgabe ----------
        # Gesichter
        face_list = []
        h, w = frame_copy.shape[:2]
        for face, name in zip(last_faces, last_names):
            top, right, bottom, left = face["box"]
            width_px = right - left
            height_px = bottom - top
            width_pct = (width_px / w) * 100
            height_pct = (height_px / h) * 100
            face_list.append(
                f"{name}: Pixels[{left},{top},{right},{bottom}], "
                f"{width_px}x{height_px}px ({width_pct:.1f}% x {height_pct:.1f}%)"
            )

        # Objekte
        obj_list = []
        for obj in last_objects:
            bbox = obj["bbox"]
            conf = obj.get("confidence", 1.0)
            obj_list.append(
                f"{obj['name']} ({bbox['xmin']*100:.1f}-{bbox['xmax']*100:.1f}% width, "
                f"{bbox['ymin']*100:.1f}-{bbox['ymax']*100:.1f}% height, "
                f"{conf*100:.1f}% conf)"
            )

        # Terminalausgabe
        print("\033c", end="")  # Konsole löschen
        print("Erkannte Gesichter:")
        for f in face_list:
            print(" -", f)
        print("\nAktuelle Objekte im Frame:")
        for o in obj_list:
            print(" -", o)

    # ---------- Boxen zeichnen ----------
    for face, name in zip(last_faces, last_names):
        top, right, bottom, left = face["box"]
        cv2.rectangle(frame_copy, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame_copy, name, (left, top-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    h, w = frame_copy.shape[:2]
    for obj in last_objects:
        bbox = obj["bbox"]
        x1 = int(bbox["xmin"] * w)
        y1 = int(bbox["ymin"] * h)
        x2 = int(bbox["xmax"] * w)
        y2 = int(bbox["ymax"] * h)
        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(frame_copy, obj["name"], (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # ---------- Frame anzeigen ----------
    cv2.imshow("Detection", frame_copy)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()