import os
import json
import time
from typing import Dict, Any, List
from datetime import datetime


class ResearchTool:
    """Research tool with offline knowledge base, weather, time, and Wikipedia-like lookup."""

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.knowledge_dir = knowledge_dir
        os.makedirs(knowledge_dir, exist_ok=True)
        self._init_default_knowledge()

    def _init_default_knowledge(self):
        default_file = os.path.join(self.knowledge_dir, "general.json")
        if not os.path.exists(default_file):
            default_data = {
                "robot_facts": {
                    "name": "Balancing Robot",
                    "capabilities": [
                        "2-wheel self-balancing",
                        "Two arms with grippers",
                        "Rotatable and tiltable head",
                        "WS2812 LED mood lighting",
                        "Display face in head",
                        "Built-in speaker",
                        "IMU sensor for balance",
                        "Distance sensors (LiDAR/ultrasonic)",
                        "Camera for vision",
                        "Pressure sensors in arms"
                    ],
                    "controllers": "ESP32P4 (main) + ESP32 (movement)",
                    "modes": ["Idle", "Play", "Assist", "Explore", "Auto"]
                },
                "general_knowledge": {
                    "german_capitals": {"Germany": "Berlin", "France": "Paris", "Austria": "Vienna", "Switzerland": "Bern"},
                    "fun_facts": [
                        "Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs that was still edible.",
                        "Octopuses have three hearts and blue blood.",
                        "A group of flamingos is called a flamboyance.",
                        "Bananas are berries, but strawberries aren't.",
                        "The shortest war in history lasted 38-45 minutes between Britain and Zanzibar in 1896."
                    ],
                    "weather_info": "Use an online service or ask the user for current weather. I don't have live internet access."
                }
            }
            with open(default_file, "w") as f:
                json.dump(default_data, f, indent=2)

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "research":
            return self._research(args.get("query", ""))
        elif tool_name == "read_local_file":
            return self._read_local_file(args.get("filename", ""))
        elif tool_name == "get_current_time":
            return self._get_current_time()
        elif tool_name == "get_weather":
            return self._get_weather(args.get("location", ""))
        elif tool_name == "get_fun_fact":
            return self._get_fun_fact()
        return f"Unknown research tool: {tool_name}"

    def _research(self, query: str) -> str:
        if not query:
            return "No query provided."

        query_lower = query.lower()
        results = []

        for fname in os.listdir(self.knowledge_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self.knowledge_dir, fname)
            try:
                with open(fpath, "r") as f:
                    data = json.load(f)
                matches = self._search_dict(data, query_lower)
                if matches:
                    results.append({"file": fname, "matches": matches})
            except Exception:
                pass

        if results:
            lines = [f"Found information in {len(results)} file(s):"]
            for r in results[:3]:
                lines.append(f"\n  File: {r['file']}")
                for m in r['matches'][:3]:
                    lines.append(f"    - {m}")
            return "\n".join(lines)

        return f"No local knowledge found for '{query}'. Try adding files to data/knowledge/."

    def _search_dict(self, data, query_lower: str, path: str = "") -> List[str]:
        matches = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                if query_lower in key.lower():
                    matches.append(f"{new_path}: {str(value)[:200]}")
                if isinstance(value, (dict, list)):
                    matches.extend(self._search_dict(value, query_lower, new_path))
                elif isinstance(value, str) and query_lower in value.lower():
                    matches.append(f"{new_path}: {value[:200]}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                if isinstance(item, str) and query_lower in item.lower():
                    matches.append(f"{new_path}: {item[:200]}")
                elif isinstance(item, (dict, list)):
                    matches.extend(self._search_dict(item, query_lower, new_path))
        return matches

    def _read_local_file(self, filename: str) -> str:
        fpath = os.path.join(self.knowledge_dir, filename)
        if not os.path.exists(fpath):
            return f"File not found: {filename}. Available files: {', '.join(os.listdir(self.knowledge_dir))}"
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)[:2000]
        except Exception as e:
            return f"Error reading file: {e}"

    def _get_current_time(self) -> str:
        now = datetime.now()
        return f"Current time: {now.strftime('%A, %B %d, %Y at %H:%M')}"

    def _get_weather(self, location: str) -> str:
        if not location:
            return "Please specify a location for weather lookup."
        return f"Weather for {location}: I don't have live internet access. Please check a weather service or ask the user."

    def _get_fun_fact(self) -> str:
        fpath = os.path.join(self.knowledge_dir, "general.json")
        try:
            with open(fpath, "r") as f:
                data = json.load(f)
            facts = data.get("general_knowledge", {}).get("fun_facts", [])
            if facts:
                import random
                return random.choice(facts)
        except Exception:
            pass
        return "Did you know? Honey never spoils!"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "research",
                    "description": "Search local knowledge base for information. Works offline. Searches all JSON files in the knowledge directory recursively.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "What to search for"},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_local_file",
                    "description": "Read the contents of a local knowledge file by filename.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Filename in the knowledge directory (e.g. 'general.json')"},
                        },
                        "required": ["filename"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current date and time.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information for a location. Note: works offline, so returns a message to check externally.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City or location name"},
                        },
                        "required": ["location"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fun_fact",
                    "description": "Get a random fun fact from local knowledge.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
