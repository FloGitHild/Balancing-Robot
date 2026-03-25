# detector.py
import cv2
from ultralytics import YOLO
import face_recognition

class Detector:
    def __init__(self):
        print("🧠 Lade YOLO Modell...")
        self.model = YOLO("yolov8x.pt")  # kleines Modell,auflistung von schlecht nach gut: yolov8n.pt yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt

    def detect_faces(self, frame):
        """Erkennt Gesichter und liefert Bounding Boxes + Encodings"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)

        faces = []
        h, w = frame.shape[:2]
        for (box, enc) in zip(boxes, encodings):
            top, right, bottom, left = box
            faces.append({
                "box": (top, right, bottom, left),
                "bbox": {
                    "xmin": left / w,
                    "ymin": top / h,
                    "xmax": right / w,
                    "ymax": bottom / h
                },
                "encoding": enc
            })
        return faces

    def detect_objects(self, frame, confidence_threshold=0.25):
        """Erkennt Objekte und gibt Bounding Boxes in Prozent zurück"""
        h, w = frame.shape[:2]
        results = self.model(frame, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf < confidence_threshold:
                    continue  # Filtere schwache Treffer
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls = int(box.cls[0])
                name = self.model.names[cls]
                detections.append({
                    "name": name,
                    "bbox": {
                        "xmin": x1 / w,
                        "ymin": y1 / h,
                        "xmax": x2 / w,
                        "ymax": y2 / h
                    },
                    "confidence": conf
                })
        return detections