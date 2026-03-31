import socket
import json
import time
from typing import Optional, Dict, Any

class Movements:
    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.socket = None
        self._connect()
    
    def _connect(self):
        try:
            import socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"✅ Connected to Robot at {self.host}:{self.port}")
        except Exception as e:
            print(f"⚠️ Cannot connect to Robot: {e}")
            self.socket = None
    
    def _send(self, event: str, data: Any):
        if not self.socket:
            self._connect()
        if self.socket:
            try:
                # Using socketio client would be better, but this is a simple fallback
                print(f"📤 Would send via socket: {event} - {data}")
                return True
            except Exception as e:
                print(f"❌ Send failed: {e}")
                return False
        return False
    
    def move(self, direction: str) -> str:
        """Control robot movement direction"""
        valid = ["forward", "backward", "left", "right", "stop"]
        if direction not in valid:
            return f"Invalid direction. Use: {valid}"
        self._send("move", direction)
        return f"Moving {direction}"
    
    def speed(self, value: int) -> str:
        """Set robot speed (0-100)"""
        if not 0 <= value <= 100:
            return "Speed must be between 0 and 100"
        self._send("speed", value)
        return f"Speed set to {value}"
    
    def head(self, rotate: Optional[int] = None, tilt: Optional[int] = None) -> str:
        """Control head position"""
        if rotate is not None and not -90 <= rotate <= 90:
            return "Rotate must be between -90 and 90"
        if tilt is not None and not -90 <= tilt <= 90:
            return "Tilt must be between -90 and 90"
        if rotate is not None:
            self._send("head", {"type": "rotate", "val": rotate})
        if tilt is not None:
            self._send("head", {"type": "tilt", "val": tilt})
        return f"Head set - rotate: {rotate}, tilt: {tilt}"
    
    def arm(self, side: str, h: Optional[int] = None, v: Optional[int] = None) -> str:
        """Control arm position (side: 'left' or 'right')"""
        if side not in ["left", "right"]:
            return "Side must be 'left' or 'right'"
        if h is not None and not -90 <= h <= 90:
            return "Horizontal must be between -90 and 90"
        if v is not None and not -90 <= v <= 90:
            return "Vertical must be between -90 and 90"
        if h is not None:
            self._send("arm", {"side": side, "axis": "h", "val": h})
        if v is not None:
            self._send("arm", {"side": side, "axis": "v", "val": v})
        return f"{side.capitalize()} arm set - h: {h}, v: {v}"
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "move",
                    "description": "Control the direction the Robot is moving",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["forward", "backward", "left", "right", "stop"],
                                "description": "The direction to move"
                            }
                        },
                        "required": ["direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "speed",
                    "description": "Set the robot's movement speed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Speed value from 0 to 100"
                            }
                        },
                        "required": ["value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "head",
                    "description": "Control the head position (rotate and tilt)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rotate": {"type": "integer", "minimum": -90, "maximum": 90},
                            "tilt": {"type": "integer", "minimum": -90, "maximum": 90}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "arm",
                    "description": "Control an arm's position",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "side": {"type": "string", "enum": ["left", "right"]},
                            "h": {"type": "integer", "minimum": -90, "maximum": 90},
                            "v": {"type": "integer", "minimum": -90, "maximum": 90}
                        },
                        "required": ["side"]
                    }
                }
            }
        ]

if __name__ == "__main__":
    m = Movements()
    print(m.move("forward"))
    print(m.speed(50))
    print(m.head(rotate=10, tilt=5))
    print(m.arm("left", h=20, v=10))
