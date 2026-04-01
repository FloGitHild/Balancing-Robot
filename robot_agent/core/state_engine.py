import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional


class StateEngine:
    """Maintains the current world state of the robot and environment."""

    def __init__(self):
        self.state: Dict[str, Any] = {
            "people": [],
            "objects": [],
            "robot_pose": {"x": 0.0, "y": 0.0, "heading": 0.0},
            "environment": {
                "distance_cm": 999,
                "battery_pct": 100,
                "imu": {"pitch": 0.0, "roll": 0.0, "yaw": 0.0},
            },
            "mode": "Idle",
            "mood": {"emotion": "neutral", "intensity": 0.5},
            "last_interactions": [],
            "last_update": datetime.now().isoformat(),
            "speech_input": "",
            "active_task_id": None,
        }

    def update(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        if "vision" in inputs:
            self.state["people"] = inputs["vision"].get("people", [])
            self.state["objects"] = inputs["vision"].get("objects", [])
        if "sensors" in inputs:
            sensors = inputs["sensors"]
            if "distance" in sensors:
                self.state["environment"]["distance_cm"] = sensors["distance"]
            if "battery" in sensors:
                self.state["environment"]["battery_pct"] = sensors["battery"]
            if "imu" in sensors:
                self.state["environment"]["imu"] = sensors["imu"]
        if "speech" in inputs:
            self.state["speech_input"] = inputs["speech"]
        if "mode" in inputs:
            self.state["mode"] = inputs["mode"]
        if "mood" in inputs:
            self.state["mood"] = inputs["mood"]

        self.state["last_update"] = datetime.now().isoformat()
        return self.state

    def get(self) -> Dict[str, Any]:
        return dict(self.state)

    def get_mode(self) -> str:
        return self.state["mode"]

    def get_distance(self) -> float:
        return self.state["environment"]["distance_cm"]

    def get_people(self) -> List[Dict[str, Any]]:
        return self.state["people"]

    def get_objects(self) -> List[Dict[str, Any]]:
        return self.state["objects"]

    def set_active_task(self, task_id: Optional[str]):
        self.state["active_task_id"] = task_id

    def get_active_task_id(self) -> Optional[str]:
        return self.state.get("active_task_id")

    def add_interaction(self, interaction: str):
        self.state["last_interactions"].append({
            "text": interaction,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.state["last_interactions"]) > 20:
            self.state["last_interactions"] = self.state["last_interactions"][-20:]

    def to_prompt_context(self) -> str:
        parts = []
        mode = self.state["mode"]
        mood = self.state["mood"]
        parts.append(f"Mode: {mode}")
        parts.append(f"Mood: {mood['emotion']} (intensity: {mood['intensity']})")

        people = self.state.get("people", [])
        if people:
            names = [p.get("name", "Unknown") for p in people]
            parts.append(f"People present: {', '.join(names)}")
        else:
            parts.append("No people visible")

        objects_list = self.state.get("objects", [])
        if objects_list:
            obj_desc = ", ".join(
                [f"{o.get('label', 'object')} at ({o.get('x', 0):.1f}, {o.get('y', 0):.1f})" for o in objects_list[:5]]
            )
            parts.append(f"Objects: {obj_desc}")
        else:
            parts.append("No objects visible")

        dist = self.state["environment"]["distance_cm"]
        parts.append(f"Distance ahead: {dist:.0f}cm")
        parts.append(f"Battery: {self.state['environment']['battery_pct']}%")

        speech = self.state.get("speech_input", "")
        if speech:
            parts.append(f"Last speech: {speech}")

        return "\n".join(parts)
