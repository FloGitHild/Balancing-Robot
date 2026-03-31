import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

class Memory:
    def __init__(self, storage_dir: str = "data/memory"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.short_term: List[Dict[str, Any]] = []
        self.long_term: List[Dict[str, Any]] = []
        self.interactions: Dict[str, List[Dict[str, Any]]] = {}  # Per person
        self._load()
    
    def _load(self):
        for filename in ["short_term.json", "long_term.json", "interactions.json"]:
            filepath = os.path.join(self.storage_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        if filename == "short_term.json":
                            self.short_term = data
                        elif filename == "long_term.json":
                            self.long_term = data
                        elif filename == "interactions.json":
                            self.interactions = data
                except:
                    pass
    
    def _save(self):
        with open(os.path.join(self.storage_dir, "short_term.json"), "w") as f:
            json.dump(self.short_term, f, indent=2)
        with open(os.path.join(self.storage_dir, "long_term.json"), "w") as f:
            json.dump(self.long_term, f, indent=2)
        with open(os.path.join(self.storage_dir, "interactions.json"), "w") as f:
            json.dump(self.interactions, f, indent=2)
    
    def add_short_term(self, task: str, priority: str = "normal") -> str:
        """Add a short-term task"""
        item = {
            "id": len(self.short_term) + 1,
            "task": task,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.short_term.append(item)
        self._save()
        return f"Added short-term task: {task}"
    
    def add_long_term(self, task: str, priority: str = "normal") -> str:
        """Add a long-term goal"""
        item = {
            "id": len(self.long_term) + 1,
            "task": task,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.long_term.append(item)
        self._save()
        return f"Added long-term task: {task}"
    
    def add_interaction(self, person: str, interaction: Dict[str, Any]) -> str:
        """Add an interaction with a person"""
        if person not in self.interactions:
            self.interactions[person] = []
        
        interaction["timestamp"] = datetime.now().isoformat()
        self.interactions[person].append(interaction)
        
        # Keep last 50 per person
        if len(self.interactions[person]) > 50:
            self.interactions[person] = self.interactions[person][-50:]
        
        self._save()
        return f"Added interaction with {person}"
    
    def get_short_term(self) -> str:
        if not self.short_term:
            return "No short-term tasks"
        result = "Short-term Tasks:\n"
        for t in self.short_term:
            status = "✓" if t["completed"] else "○"
            result += f"  {status} {t['task']}\n"
        return result.strip()
    
    def get_long_term(self) -> str:
        if not self.long_term:
            return "No long-term goals"
        result = "Long-term Goals:\n"
        for t in self.long_term:
            status = "✓" if t["completed"] else "○"
            result += f"  {status} {t['task']}\n"
        return result.strip()
    
    def get_interactions(self, person: str, limit: int = 10) -> str:
        if person not in self.interactions:
            return f"No interactions with {person}"
        result = f"Interactions with {person}:\n"
        for i in self.interactions[person][-limit:]:
            result += f"  - [{i.get('timestamp', '')}] {i.get('summary', '')}\n"
        return result.strip()
    
    def get_all_people(self) -> List[str]:
        return list(self.interactions.keys())
    
    def complete_short_term(self, task_id: int) -> str:
        for t in self.short_term:
            if t["id"] == task_id:
                t["completed"] = True
                self._save()
                return f"Completed: {t['task']}"
        return "Task not found"
    
    def complete_long_term(self, task_id: int) -> str:
        for t in self.long_term:
            if t["id"] == task_id:
                t["completed"] = True
                self._save()
                return f"Completed: {t['task']}"
        return "Task not found"
    
    def clear_short_term(self) -> str:
        """Clear completed short-term tasks"""
        self.short_term = [t for t in self.short_term if not t["completed"]]
        self._save()
        return "Cleared completed short-term tasks"
    
    def get_summary(self) -> str:
        """Get a summary of memory status"""
        st_completed = len([t for t in self.short_term if t["completed"]])
        st_pending = len([t for t in self.short_term if not t["completed"]])
        lt_completed = len([t for t in self.long_term if t["completed"]])
        lt_pending = len([t for t in self.long_term if not t["completed"]])
        
        return f"Memory: {st_pending}/{st_completed} short-term pending/completed, {lt_pending}/{lt_completed} long-term, {len(self.interactions)} people known"

if __name__ == "__main__":
    m = Memory()
    print(m.add_short_term("Check if person needs help"))
    print(m.add_long_term("Learn to play a new game"))
    print(m.add_interaction("John", {"summary": "Taught me a joke", "mood": "happy"}))
    print(m.get_short_term())
    print(m.get_interactions("John"))
    print(m.get_summary())
