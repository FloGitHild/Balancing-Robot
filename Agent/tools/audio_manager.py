"""
Audio Manager - Search and play audio files
"""

import os
import random
from typing import List, Optional

class AudioManager:
    def __init__(self, audio_dir: str = "data/audio"):
        self.audio_dir = audio_dir
        os.makedirs(audio_dir, exist_ok=True)
        
        # Sample sounds - in real implementation would scan the directory
        self.sample_sounds = {
            "greeting": ["hello.mp3", "hi.mp3", "greetings.mp3"],
            "success": ["success.mp3", "done.mp3", "complete.mp3"],
            "error": ["error.mp3", "fail.mp3", "wrong.mp3"],
            "music": ["music1.mp3", "music2.mp3"],
            "notification": ["beep.mp3", "ding.mp3", "alert.mp3"]
        }
    
    def search_sounds(self, query: str) -> str:
        """Search for sounds matching query"""
        query = query.lower()
        
        # Search in categories
        results = []
        for category, sounds in self.sample_sounds.items():
            if query in category:
                results.extend(sounds)
        
        # If no category match, try filename search
        if not results:
            try:
                files = os.listdir(self.audio_dir)
                results = [f for f in files if query in f.lower()]
            except:
                pass
        
        if results:
            return f"Found sounds: {', '.join(results[:5])}"
        return f"No sounds found for '{query}'"
    
    def play_category(self, category: str) -> str:
        """Play a random sound from category"""
        sounds = self.sample_sounds.get(category, [])
        if sounds:
            sound = random.choice(sounds)
            return f"Playing {category}: {sound}"
        return f"Category '{category}' not found"
    
    def get_available_categories(self) -> str:
        """Get list of available sound categories"""
        return f"Categories: {', '.join(self.sample_sounds.keys())}"
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "audio_search",
                    "description": "Search for sound files by keyword or category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query for sounds"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_play_category",
                    "description": "Play a sound from a category (greeting, success, error, music, notification)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "Sound category to play"}
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_list_categories",
                    "description": "List available sound categories",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]


if __name__ == "__main__":
    am = AudioManager()
    print(am.get_available_categories())
    print(am.search_sounds("hello"))
    print(am.play_category("greeting"))