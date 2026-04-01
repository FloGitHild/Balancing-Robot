from typing import Dict, Any, List


class VisionTool:
    """Read-only vision tool. Provides objects and faces detected by the vision system."""

    def __init__(self):
        self._objects: List[Dict[str, Any]] = []
        self._faces: List[Dict[str, Any]] = []

    def update(self, objects: List[Dict[str, Any]], faces: List[Dict[str, Any]]):
        self._objects = objects
        self._faces = faces

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "get_visible_objects":
            return self._get_objects()
        elif tool_name == "get_visible_faces":
            return self._get_faces()
        return f"Unknown vision tool: {tool_name}"

    def _get_objects(self) -> str:
        if not self._objects:
            return "No objects detected."
        lines = ["Detected objects:"]
        for obj in self._objects[:10]:
            label = obj.get("label", "unknown")
            x = obj.get("x", 0.5)
            y = obj.get("y", 0.5)
            conf = obj.get("confidence", 0)
            lines.append(f"  - {label} at position ({x:.2f}, {y:.2f}) confidence {conf:.0%}")
        return "\n".join(lines)

    def _get_faces(self) -> str:
        if not self._faces:
            return "No faces detected."
        lines = ["Detected faces:"]
        for face in self._faces:
            name = face.get("name", "Unknown")
            x = face.get("x", 0.5)
            y = face.get("y", 0.5)
            lines.append(f"  - {name} at position ({x:.2f}, {y:.2f})")
        return "\n".join(lines)

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_visible_objects",
                    "description": "Get list of currently visible objects with positions. Positions are normalized 0-1 (0=left/top, 1=right/bottom).",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_visible_faces",
                    "description": "Get list of currently visible faces with names and positions. Positions are normalized 0-1.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
