import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

MOODS = {
    "neutral": {"emoji": "😐", "led_color": [0, 255, 0], "description": "Neutral state"},
    "happy": {"emoji": "😄", "led_color": [0, 255, 255], "description": "Happy and playful"},
    "sad": {"emoji": "😢", "led_color": [0, 0, 255], "description": "Sad or empathetic"},
    "curious": {"emoji": "🤔", "led_color": [255, 255, 0], "description": "Curious or interested"},
    "excited": {"emoji": "🎉", "led_color": [255, 0, 255], "description": "Excited or enthusiastic"},
    "thinking": {"emoji": "🤨", "led_color": [128, 0, 128], "description": "Thinking or processing"},
    "surprised": {"emoji": "😮", "led_color": [255, 165, 0], "description": "Surprised or amazed"},
    "scared": {"emoji": "😨", "led_color": [255, 0, 0], "description": "Scared or cautious"},
    "angry": {"emoji": "😠", "led_color": [255, 0, 0], "description": "Angry or frustrated"},
    "relaxed": {"emoji": "😌", "led_color": [0, 128, 255], "description": "Relaxed or calm"},
}

class Mood:
    def __init__(self, storage_path: str = "data/mood.json"):
        self.storage_path = storage_path
        self.current_mood = "neutral"
        self.mood_history: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.current_mood = data.get("current", "neutral")
                    self.mood_history = data.get("history", [])
            except:
                pass
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else ".", exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump({
                    "current": self.current_mood,
                    "history": self.mood_history
                }, f, indent=2)
        except:
            pass
    
    def set_mood(self, mood: str) -> str:
        """Set the current mood"""
        mood_lower = mood.lower()
        if mood_lower not in MOODS:
            valid = ", ".join(MOODS.keys())
            return f"Invalid mood. Valid moods: {valid}"
        
        old_mood = self.current_mood
        self.current_mood = mood_lower
        
        self.mood_history.append({
            "from": old_mood,
            "to": mood_lower,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
        
        mood_info = MOODS[mood_lower]
        return f"Mood changed from {old_mood} to {mood_lower} {mood_info['emoji']}"
    
    def get_current(self) -> Dict[str, Any]:
        """Get current mood info"""
        return {
            "mood": self.current_mood,
            **MOODS[self.current_mood]
        }
    
    def get_led_color(self) -> List[int]:
        """Get LED color for current mood"""
        return MOODS[self.current_mood]["led_color"]
    
    def get_history(self, limit: int = 10) -> str:
        """Get mood history"""
        if not self.mood_history:
            return "No mood history"
        result = "Mood History:\n"
        for h in self.mood_history[-limit:]:
            result += f"  {h['from']} → {h['to']} at {h['timestamp']}\n"
        return result.strip()
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "mood_set",
                    "description": "Set the robot's mood. Affects LED colors and expression.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mood": {
                                "type": "string",
                                "enum": list(MOODS.keys()),
                                "description": "The mood to set"
                            }
                        },
                        "required": ["mood"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mood_get_current",
                    "description": "Get the current mood information",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mood_get_history",
                    "description": "Get the mood change history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            }
        ]

if __name__ == "__main__":
    m = Mood()
    print(m.set_mood("happy"))
    print(m.get_current())
    print(m.get_history())
