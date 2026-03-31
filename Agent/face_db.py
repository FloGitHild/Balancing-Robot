# face_db.py
import face_recognition
import os
import pickle

DB_PATH = r"/home/florian/data/Florian/Freizeit/Balancing_Robot/face_database/faces.pkl"

class FaceDB:
    def __init__(self):
        self.encodings = []
        self.names = []
        self.load()

    def load(self):
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "rb") as f:
                self.encodings, self.names = pickle.load(f)

    def save(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, "wb") as f:
            pickle.dump((self.encodings, self.names), f)

    def add_face(self, encoding, name, n_samples=3):
        """Speichert ein Gesicht mehrere Male, um die Erkennung zu stabilisieren"""
        for _ in range(n_samples):
            self.encodings.append(encoding)
            self.names.append(name)
        self.save()