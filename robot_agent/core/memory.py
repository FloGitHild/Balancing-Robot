import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class MemorySystem:
    """Persistent memory: short-term, long-term, people, and task log."""

    def __init__(self, data_dir: str = "data/memory"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.short_term_path = os.path.join(data_dir, "short_term.json")
        self.long_term_path = os.path.join(data_dir, "long_term.json")
        self.people_path = os.path.join(data_dir, "people.json")

        self.short_term: List[Dict[str, Any]] = []
        self.long_term: List[Dict[str, Any]] = []
        self.people: Dict[str, Dict[str, Any]] = {}

        self._load_all()

    def _load_all(self):
        self.short_term = self._load_json(self.short_term_path, [])
        self.long_term = self._load_json(self.long_term_path, [])
        self.people = self._load_json(self.people_path, {})

    def _load_json(self, path: str, default):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save(self, path: str, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # --- Short-term memory (last interactions, recent observations) ---

    def store_short(self, key: str, value: Any):
        entry = {"key": key, "value": value, "timestamp": datetime.now().isoformat()}
        self.short_term.append(entry)
        self.short_term = self.short_term[-50:]
        self._save(self.short_term_path, self.short_term)

    def recall_short(self, query: str) -> str:
        results = [e for e in self.short_term if query.lower() in str(e).lower()]
        if not results:
            return "No recent memory found for that query."
        return "\n".join([f"- [{e['timestamp']}] {e['key']}: {e['value']}" for e in results[-10:]])

    def clear_short(self):
        self.short_term = []
        self._save(self.short_term_path, self.short_term)

    # --- Long-term memory (preferences, learned facts) ---

    def store_long(self, key: str, value: Any):
        entry = {"key": key, "value": value, "timestamp": datetime.now().isoformat()}
        self.long_term.append(entry)
        self._save(self.long_term_path, self.long_term)

    def recall_long(self, query: str) -> str:
        results = [e for e in self.long_term if query.lower() in str(e).lower()]
        if not results:
            return "No long-term memory found for that query."
        return "\n".join([f"- [{e['timestamp']}] {e['key']}: {e['value']}" for e in results[-10:]])

    # --- People memory ---

    def add_person(self, name: str, preferences: Optional[List[str]] = None):
        name_cap = name.strip().capitalize()
        if name_cap not in self.people:
            self.people[name_cap] = {
                "name": name_cap,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "preferences": preferences or [],
                "interactions": [],
            }
        else:
            self.people[name_cap]["last_seen"] = datetime.now().isoformat()
        self._save(self.people_path, self.people)

    def update_person(self, name: str, **kwargs):
        name_cap = name.strip().capitalize()
        if name_cap in self.people:
            self.people[name_cap].update(kwargs)
            self.people[name_cap]["last_seen"] = datetime.now().isoformat()
            self._save(self.people_path, self.people)

    def add_interaction(self, name: str, summary: str):
        name_cap = name.strip().capitalize()
        if name_cap not in self.people:
            self.add_person(name_cap)
        self.people[name_cap]["interactions"].append({
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        })
        self.people[name_cap]["interactions"] = self.people[name_cap]["interactions"][-30:]
        self._save(self.people_path, self.people)

    def get_person(self, name: str) -> Optional[Dict[str, Any]]:
        name_cap = name.strip().capitalize()
        return self.people.get(name_cap)

    def get_all_people(self) -> List[str]:
        return list(self.people.keys())

    def recall_person(self, name: str) -> str:
        person = self.get_person(name)
        if not person:
            return f"No memory of {name}."
        lines = [f"Person: {person['name']}"]
        lines.append(f"First seen: {person['first_seen']}")
        lines.append(f"Last seen: {person['last_seen']}")
        if person.get("preferences"):
            lines.append(f"Preferences: {', '.join(person['preferences'])}")
        if person.get("interactions"):
            lines.append("Recent interactions:")
            for i in person["interactions"][-5:]:
                lines.append(f"  - [{i['timestamp']}] {i['summary']}")
        return "\n".join(lines)

    # --- Tool-compatible interface ---

    def remember(self, key: str, value: str) -> str:
        self.store_long(key, value)
        return f"Remembered: {key} = {value}"

    def recall(self, query: str) -> str:
        st = self.recall_short(query)
        lt = self.recall_long(query)
        combined = f"Short-term:\n{st}\n\nLong-term:\n{lt}"
        return combined

    def get_context_for_prompt(self) -> str:
        lines = ["=== MEMORY CONTEXT ==="]
        if self.short_term:
            lines.append("Recent (short-term):")
            for e in self.short_term[-5:]:
                lines.append(f"  - {e['key']}: {e['value']}")
        if self.long_term:
            lines.append("Learned (long-term):")
            for e in self.long_term[-5:]:
                lines.append(f"  - {e['key']}: {e['value']}")
        if self.people:
            lines.append(f"Known people: {', '.join(self.people.keys())}")
        lines.append("=== END MEMORY ===")
        return "\n".join(lines)
