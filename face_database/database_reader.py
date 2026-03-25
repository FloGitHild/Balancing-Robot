import pickle

DB_PATH = r"D:\Florian\Freizeit\Balancing_Robot\face_database\faces.pkl"

with open(DB_PATH, "rb") as f:
    encodings, names = pickle.load(f)

print("Gespeicherte Namen:")
for n in names:
    print("-", n)

print(f"Anzahl Encodings: {len(encodings)}")