import cv2
import sys
import os
import threading
import time
import socketio
import importlib.util

# Load config
spec = importlib.util.spec_from_file_location("config", os.path.join(os.path.dirname(__file__), "config.py"))
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Lokal'))
from detector import Detector
from face_db import FaceDB
import face_recognition

STREAM_URL = "http://localhost:5000/video_feed"
SIM_URL = "http://localhost:5000"
Face_Recog_Tolerance = config.VISION_FACE_TOLERANCE
Object_Confidence_Threshold = config.VISION_OBJECT_CONFIDENCE
SHOW_WINDOW = config.VISION_SHOW_WINDOW
ANALYSIS_INTERVAL = config.VISION_DETECTION_INTERVAL

detector = Detector()
db = FaceDB()

sio = socketio.Client(logger=False, engineio_logger=False)

# Vision will only run when requested
vision_active = False

cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print("❌ Stream konnte nicht geöffnet werden")
    exit()

print("✅ Stream läuft!")
# Silent - no print when connected

latest_frame = None
frame_lock = threading.Lock()
interval = ANALYSIS_INTERVAL
last_time = 0

last_faces = []
last_names = []
last_objects = []

@sio.event
def connect():
    pass  # Silent connection

@sio.on('request_vision')
def on_request_vision():
    """Called when Agent wants vision data"""
    global vision_active
    vision_active = True
    print("📹 Vision requested by Agent")
    # Send current detection results to Agent
    send_vision_data(last_objects, last_faces, last_names)
    # Print detection results to terminal
    print("\n" + "="*50)
    print("📷 VISION DETECTION (Agent requested):")
    print("-"*50)
    for face, name in zip(last_faces, last_names):
        print(f"  👤 Face: {name}")
    for obj in last_objects:
        print(f"  📦 Object: {obj['name']}")
    print("="*50 + "\n")

def send_vision_data(objects, faces, names):
    """Send vision data to Agent"""
    try:
        sio.emit('vision_update', {
            'objects': objects,
            'faces': [{'name': n, 'box': f['box']} for f, n in zip(faces, names)]
        })
    except Exception as e:
        pass

def frame_reader():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        with frame_lock:
            latest_frame = frame.copy()

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

threading.Thread(target=frame_reader, daemon=True).start()

try:
    sio.connect(SIM_URL, transports=['websocket'])
except Exception as e:
    print(f"⚠️ Could not connect socket: {e}")

# Wait for vision requests - only send when asked
# But run detection continuously for better face detection
while True:
    current_time = time.time()

    with frame_lock:
        frame_copy = latest_frame.copy() if latest_frame is not None else None
    if frame_copy is None:
        continue

    if current_time - last_time > interval:
        last_time = current_time

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

        add_face_interactively(frame_copy, detector, db)
        last_faces = faces
        last_names = names

        objects = detector.detect_objects(frame_copy, confidence_threshold=Object_Confidence_Threshold)
        last_objects = objects

        # Detection continues in background for face recognition
        
        # Only send data to Agent when explicitly requested
        # send_vision_data is called in on_request_vision handler
        
        # Only use request system if we need to trigger (for backward compat)

        if SHOW_WINDOW:
            face_list = []
            h, w = frame_copy.shape[:2]
            for face, name in zip(last_faces, last_names):
                top, right, bottom, left = face["box"]
                width_px = right - left
                height_px = bottom - top
                width_pct = (width_px / w) * 100
                height_pct = (height_px / h) * 100
                face_list.append(
                    f"{name}: {width_px}x{height_px}px ({width_pct:.1f}% x {height_pct:.1f}%)"
                )

            obj_list = []
            for obj in last_objects:
                bbox = obj["bbox"]
                conf = obj.get("confidence", 1.0)
                obj_list.append(
                    f"{obj['name']} ({conf*100:.1f}% conf)"
                )

            print("\033c", end="")
            print("Detected Faces:")
            for f in face_list:
                print(" -", f)
            print("\nObjects:")
            for o in obj_list:
                print(" -", o)
            
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

            cv2.imshow("Detection", frame_copy)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                exit()

cap.release()
cv2.destroyAllWindows()
if sio.connected:
    sio.disconnect()
