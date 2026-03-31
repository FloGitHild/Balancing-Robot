import cv2
import requests
import numpy as np

# URL des ESP32-Streams
url = "http://192.168.31.9:81/stream"

stream = requests.get(url, stream=True)
bytes_data = b''

for chunk in stream.iter_content(chunk_size=1024):
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')  # Start Marker JPEG
    b = bytes_data.find(b'\xff\xd9')  # End Marker JPEG
    if a != -1 and b != -1:
        jpg = bytes_data[a:b+2]
        bytes_data = bytes_data[b+2:]
        img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            cv2.imshow('ESP32-CAM Stream', img)
        if cv2.waitKey(1) == 27:  # ESC zum Beenden
            break

cv2.destroyAllWindows()
