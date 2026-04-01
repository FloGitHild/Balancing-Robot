from typing import Dict, Any, List


def _safe_float(val, default=0.5):
    if val is None:
        return default
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return default


class MoodTool:
    """Sets the robot mood/emotion. Maps to LEDs, eye expressions, and display."""

    VALID_EMOTIONS = ["happy", "sad", "thinking", "excited", "curious", "neutral", "surprised", "relaxed"]

    EMOTION_MAP = {
        "happy": {"led": "green", "eyes": "wide", "expression": "smile"},
        "sad": {"led": "blue", "eyes": "down", "expression": "frown"},
        "thinking": {"led": "yellow", "eyes": "moving", "expression": "neutral"},
        "excited": {"led": "rainbow", "eyes": "fast", "expression": "big_smile"},
        "curious": {"led": "yellow", "eyes": "wide", "expression": "raised_brow"},
        "neutral": {"led": "green", "eyes": "normal", "expression": "neutral"},
        "surprised": {"led": "orange", "eyes": "wide", "expression": "surprised"},
        "relaxed": {"led": "light_blue", "eyes": "half_closed", "expression": "calm"},
    }

    def __init__(self):
        self.current_emotion = "neutral"
        self.current_intensity = 0.5

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "set_mood":
            return self._set_mood(
                emotion=args.get("emotion", "neutral"),
                intensity=_safe_float(args.get("intensity", 0.5), 0.5),
                target=args.get("target", ""),
            )
        return f"Unknown mood tool: {tool_name}"

    def _set_mood(self, emotion: str, intensity: float, target: str = "") -> str:
        emotion = str(emotion).lower()
        if emotion not in self.VALID_EMOTIONS:
            return f"Invalid emotion. Valid: {', '.join(self.VALID_EMOTIONS)}"
        intensity = max(0.0, min(1.0, intensity))

        old = self.current_emotion
        self.current_emotion = emotion
        self.current_intensity = intensity

        mapping = self.EMOTION_MAP.get(emotion, self.EMOTION_MAP["neutral"])
        target_str = f" for {target}" if target else ""
        return f"Mood changed from {old} to {emotion} (intensity: {intensity}). LEDs: {mapping['led']}, Eyes: {mapping['eyes']}{target_str}"

    def get_current(self) -> Dict[str, Any]:
        return {
            "emotion": self.current_emotion,
            "intensity": self.current_intensity,
        }

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_mood",
                    "description": "Set the robot's mood/emotion. This controls LEDs, eye expressions, and display. Use this to express how the robot feels. emotion: one of the valid emotions. intensity: 0.0 to 1.0. target: optional person name.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emotion": {
                                "type": "string",
                                "enum": self.VALID_EMOTIONS,
                                "description": "The emotion to display",
                            },
                            "intensity": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "default": 0.5,
                                "description": "Intensity of the emotion",
                            },
                            "target": {
                                "type": "string",
                                "description": "Optional person this emotion is directed at",
                            },
                        },
                        "required": ["emotion"],
                    },
                },
            },
        ]
