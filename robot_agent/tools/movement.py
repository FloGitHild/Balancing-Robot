import json
import requests
from typing import Dict, Any, List
import robot_agent.config as config


def _safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return default


def _safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return default


class MovementTool:
    """Tool for controlling robot movement, head, and arms."""

    def __init__(self, robot_url: str = None):
        self.robot_url = robot_url or config.ROBOT_URL
        self.host = self.robot_url.replace("http://", "").split(":")[0]
        self.port = int(self.robot_url.replace("http://", "").split(":")[1]) if ":" in self.robot_url.replace("http://", "") else 5000

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "move":
            return self._move(args.get("direction", "stop"), _safe_int(args.get("speed", 50), 50))
        elif tool_name == "turn":
            return self._turn(_safe_int(args.get("angle", 0), 0))
        elif tool_name == "set_head":
            return self._set_head(_safe_int(args.get("rotate", 0), 0), _safe_int(args.get("tilt", 0), 0))
        elif tool_name == "move_arm":
            return self._move_arm(args.get("side", "left"), _safe_int(args.get("position", 0), 0))
        elif tool_name == "stop":
            return self._move("stop", 0)
        return f"Unknown movement tool: {tool_name}"

    def _send(self, msg_type: str, data: Dict[str, Any]) -> bool:
        try:
            payload = {"type": msg_type, **data}
            resp = requests.post(f"{self.robot_url}/api/cmd", json=payload, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def _move(self, direction: str, speed: int) -> str:
        valid = ["forward", "backward", "left", "right", "stop"]
        if direction not in valid:
            return f"Invalid direction. Use: {valid}"
        speed = max(0, min(100, speed))
        left = speed if direction == "forward" else (-speed if direction == "backward" else (speed if direction == "left" else 0))
        right = speed if direction == "forward" else (-speed if direction == "backward" else (-speed if direction == "left" else 0))
        self._send("movement", {"left": left, "right": right})
        return f"Moving {direction} at speed {speed}"

    def _turn(self, angle: int) -> str:
        angle = max(-90, min(90, angle))
        speed = 30
        left = speed if angle > 0 else -speed
        right = -speed if angle > 0 else speed
        self._send("movement", {"left": left, "right": right})
        return f"Turning {angle} degrees"

    def _set_head(self, rotate: int, tilt: int) -> str:
        rotate = max(-90, min(90, rotate))
        tilt = max(-90, min(90, tilt))
        self._send("head", {"rotate": rotate, "tilt": tilt})
        return f"Head set to rotate={rotate}, tilt={tilt}"

    def _move_arm(self, side: str, position: int) -> str:
        if side not in ("left", "right"):
            return "Side must be 'left' or 'right'"
        position = max(-90, min(90, position))
        self._send("arm", {"side": side, "position": position})
        return f"{side.capitalize()} arm moved to position {position}"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "move",
                    "description": "Move the robot in a direction. direction: forward, backward, left, right, stop. speed: 0-100.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["forward", "backward", "left", "right", "stop"]},
                            "speed": {"type": "integer", "minimum": 0, "maximum": 100, "default": 50},
                        },
                        "required": ["direction"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "turn",
                    "description": "Turn the robot by an angle in degrees. Positive = right, negative = left. Range: -90 to 90.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "angle": {"type": "integer", "minimum": -90, "maximum": 90},
                        },
                        "required": ["angle"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "set_head",
                    "description": "Set head position. rotate: -90 (left) to 90 (right). tilt: -90 (down) to 90 (up).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rotate": {"type": "integer", "minimum": -90, "maximum": 90, "default": 0},
                            "tilt": {"type": "integer", "minimum": -90, "maximum": 90, "default": 0},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "move_arm",
                    "description": "Move an arm. side: left or right. position: -90 to 90.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "side": {"type": "string", "enum": ["left", "right"]},
                            "position": {"type": "integer", "minimum": -90, "maximum": 90, "default": 0},
                        },
                        "required": ["side"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stop",
                    "description": "Stop all movement immediately.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
