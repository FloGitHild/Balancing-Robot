import os
import json
import random
from typing import Dict, Any, List
import robot_agent.config as config


class AudioTool:
    """Audio input (speech) and output (TTS, file playback) tools."""

    def __init__(self, audio_dir: str = "data/audio"):
        self.audio_dir = audio_dir
        os.makedirs(audio_dir, exist_ok=True)
        self._last_speech = ""

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "speak":
            return self._speak(args.get("text", ""))
        elif tool_name == "play_audio":
            return self._play_audio(args.get("file", ""))
        elif tool_name == "audio_search":
            return self._audio_search(args.get("keyword", ""))
        elif tool_name == "audio_play_category":
            return self._play_category(args.get("category", ""))
        return f"Unknown audio tool: {tool_name}"

    def _speak(self, text: str) -> str:
        if not text:
            return "No text to speak."
        self._last_speech = text
        return f"TTS queued: {text[:100]}"

    def _play_audio(self, filepath: str) -> str:
        full_path = os.path.join(self.audio_dir, filepath)
        if os.path.exists(full_path):
            return f"Playing audio file: {filepath}"
        return f"Audio file not found: {filepath}"

    def _audio_search(self, keyword: str) -> str:
        try:
            files = os.listdir(self.audio_dir)
            matches = [f for f in files if keyword.lower() in f.lower()]
            if matches:
                return f"Found audio files: {', '.join(matches[:5])}"
            return f"No audio files found for '{keyword}'"
        except Exception:
            return "Error searching audio files."

    def _play_category(self, category: str) -> str:
        categories = {
            "greeting": ["hello.mp3", "hi.mp3"],
            "success": ["success.mp3", "done.mp3"],
            "error": ["error.mp3"],
            "music": ["music.mp3"],
            "notification": ["beep.mp3", "ding.mp3"],
        }
        sounds = categories.get(category, [])
        if sounds:
            sound = random.choice(sounds)
            return f"Playing {category} sound: {sound}"
        return f"Category '{category}' not found. Available: {', '.join(categories.keys())}"

    def get_last_speech(self) -> str:
        return self._last_speech

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "speak",
                    "description": "Generate speech from text. The text will be spoken by the robot. Keep it short (1-2 sentences).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to speak"},
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "play_audio",
                    "description": "Play an audio file from the audio directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string", "description": "Filename of audio to play"},
                        },
                        "required": ["file"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_search",
                    "description": "Search for audio files by keyword.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "Search keyword"},
                        },
                        "required": ["keyword"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_play_category",
                    "description": "Play a sound from a category: greeting, success, error, music, notification.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["greeting", "success", "error", "music", "notification"]},
                        },
                        "required": ["category"],
                    },
                },
            },
        ]
