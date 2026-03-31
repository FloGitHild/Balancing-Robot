import threading
from typing import Optional, List, Dict, Any
import json
import time

class Vision:
    def __init__(self):
        self.objects: List[Dict[str, Any]] = []
        self.faces: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.last_update = 0
    
    def update(self, objects: List[Dict[str, Any]], faces: List[Dict[str, Any]]):
        """Update vision data from the vision thread"""
        with self.lock:
            self.objects = objects
            self.faces = faces
            self.last_update = time.time()
    
    def update_from_dict(self, data: Dict[str, Any]):
        """Update from dict received via socket"""
        objects = data.get("objects", [])
        faces = data.get("faces", [])
        self.update(objects, faces)
    
    def request_update(self):
        """Placeholder - actual request sent via agent's socket"""
        pass
    
    def get_objects(self) -> str:
        """Get current object list"""
        with self.lock:
            if not self.objects:
                return "No objects detected"
            
            result = "Detected Objects:\n"
            for obj in self.objects:
                bbox = obj.get("bbox", {})
                result += f"  - {obj['name']}: {bbox.get('xmin', 0)*100:.0f}-{bbox.get('xmax', 0)*100:.0f}% width, "
                result += f"{bbox.get('ymin', 0)*100:.0f}-{bbox.get('ymax', 0)*100:.0f}% height"
                conf = obj.get("confidence", 0)
                if conf:
                    result += f" ({conf*100:.0f}% conf)"
                result += "\n"
            return result.strip()
    
    def get_faces(self) -> str:
        """Get current face list with names and positions"""
        with self.lock:
            if not self.faces:
                return "No faces detected"
            
            result = "Detected Faces:\n"
            for face in self.faces:
                name = face.get("name", "Unknown")
                box = face.get("box", [0, 0, 0, 0])
                result += f"  - {name}: box[{box[0]}, {box[1]}, {box[2]}, {box[3]}]\n"
            return result.strip()
    
    def get_summary(self) -> str:
        """Get a concise summary for the LLM"""
        with self.lock:
            obj_count = len(self.objects)
            face_count = len(self.faces)
            
            face_names = [f.get("name", "Unknown") for f in self.faces]
            known_faces = [n for n in face_names if n != "Unknown"]
            unknown_count = face_names.count("Unknown")
            
            result = f"Objects: {obj_count}, Faces: {face_count}"
            if known_faces:
                result += f", Known people: {', '.join(known_faces)}"
            if unknown_count > 0:
                result += f", {unknown_count} unknown"
            
            return result
    
    def find_object_near_position(self, x_pct: float, y_pct: float, tolerance: float = 0.2) -> Optional[Dict[str, Any]]:
        """Find an object near a specific position (0-1 range)"""
        with self.lock:
            for obj in self.objects:
                bbox = obj.get("bbox", {})
                center_x = (bbox.get("xmin", 0) + bbox.get("xmax", 0)) / 2
                center_y = (bbox.get("ymin", 0) + bbox.get("ymax", 0)) / 2
                
                if abs(center_x - x_pct) < tolerance and abs(center_y - y_pct) < tolerance:
                    return obj
            return None
    
    def find_person_near_position(self, x_pct: float) -> Optional[Dict[str, Any]]:
        """Find a person at a horizontal position (left/center/right)"""
        with self.lock:
            if not self.faces:
                return None
            
            for face in self.faces:
                box = face.get("box", [0, 0, 0, 0])
                left, right = box[0], box[2]
                center = (left + right) / 2
                
                if x_pct == "left" and center < 0.4:
                    return face
                elif x_pct == "center" and 0.3 < center < 0.7:
                    return face
                elif x_pct == "right" and center > 0.6:
                    return face
            return None
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "vision_get_objects",
                    "description": "Get the list of currently detected objects with their positions",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "vision_get_faces",
                    "description": "Get the list of detected faces with names and positions",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "vision_get_summary",
                    "description": "Get a concise summary of what the robot currently sees",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

if __name__ == "__main__":
    v = Vision()
    v.update(
        [{"name": "cup", "bbox": {"xmin": 0.2, "xmax": 0.4, "ymin": 0.3, "ymax": 0.5}, "confidence": 0.9}],
        [{"name": "John", "box": [100, 50, 200, 150]}]
    )
    print(v.get_objects())
    print(v.get_faces())
    print(v.get_summary())
