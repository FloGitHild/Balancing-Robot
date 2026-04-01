import json
import threading
import time
from typing import Dict, Any, Optional, Callable
import robot_agent.config as config

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False


class CommLayer:
    """WebSocket communication between PC and ESP32P4 robot."""

    def __init__(self, robot_url: str = None):
        self.robot_url = robot_url or config.ROBOT_URL
        self.sio = None
        self.connected = False
        self._sensor_data: Dict[str, Any] = {}
        self._vision_data: Dict[str, Any] = {"objects": [], "faces": []}
        self._speech_data: str = ""
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()

        if SOCKETIO_AVAILABLE:
            self._setup_socketio()

    def _setup_socketio(self):
        self.sio = socketio.Client(logger=False, engineio_logger=False)

        @self.sio.event
        def connect():
            self.connected = True
            print("Connected to robot")

        @self.sio.event
        def disconnect():
            self.connected = False
            print("Disconnected from robot")

        @self.sio.on("sensor_update")
        def on_sensor(data):
            with self._lock:
                self._sensor_data.update(data)

        @self.sio.on("vision_update")
        def on_vision(data):
            with self._lock:
                self._vision_data = data

        @self.sio.on("speech_input")
        def on_speech(data):
            with self._lock:
                self._speech_data = data.get("text", "")

    def connect(self):
        if not SOCKETIO_AVAILABLE or not self.sio:
            print("SocketIO not available, running in local mode")
            return
        try:
            self.sio.connect(self.robot_url, transports=["websocket"])
        except Exception as e:
            print(f"Could not connect to robot: {e}")

    def disconnect(self):
        if self.sio and self.connected:
            self.sio.disconnect()

    def send_movement(self, left: int, right: int):
        if self.sio and self.connected:
            self.sio.emit("cmd", json.dumps({"type": "movement", "left": left, "right": right}))
        else:
            print(f"[LOCAL] Movement: left={left}, right={right}")

    def send_mood(self, emotion: str):
        if self.sio and self.connected:
            self.sio.emit("cmd", json.dumps({"type": "mood", "emotion": emotion}))
        else:
            print(f"[LOCAL] Mood: {emotion}")

    def send_audio_file(self, filepath: str):
        if self.sio and self.connected:
            self.sio.emit("cmd", json.dumps({"type": "audio", "file": filepath}))
        else:
            print(f"[LOCAL] Audio file: {filepath}")

    def send_head(self, rotate: int, tilt: int):
        if self.sio and self.connected:
            self.sio.emit("cmd", json.dumps({"type": "head", "rotate": rotate, "tilt": tilt}))
        else:
            print(f"[LOCAL] Head: rotate={rotate}, tilt={tilt}")

    def send_arm(self, side: str, position: int):
        if self.sio and self.connected:
            self.sio.emit("cmd", json.dumps({"type": "arm", "side": side, "position": position}))
        else:
            print(f"[LOCAL] Arm: side={side}, position={position}")

    def get_sensor_data(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._sensor_data)

    def get_vision_data(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._vision_data)

    def get_speech(self) -> str:
        with self._lock:
            text = self._speech_data
            self._speech_data = ""
            return text

    def get_inputs(self) -> Dict[str, Any]:
        """Collect all inputs for the agent loop."""
        with self._lock:
            vision = dict(self._vision_data)
            sensors = dict(self._sensor_data)
            speech = self._speech_data
            self._speech_data = ""

        return {
            "vision": {
                "objects": vision.get("objects", []),
                "people": vision.get("faces", []),
            },
            "sensors": sensors,
            "speech": speech,
        }
