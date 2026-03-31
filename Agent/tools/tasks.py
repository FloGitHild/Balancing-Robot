import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

class Tasks:
    def __init__(self, storage_path: str = "data/tasks.json"):
        self.storage_path = storage_path
        self.global_tasks: List[Dict[str, Any]] = []
        self.mode_tasks: Dict[str, List[Dict[str, Any]]] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.global_tasks = data.get("global", [])
                    self.mode_tasks = data.get("mode", {})
            except Exception as e:
                print(f"⚠️ Could not load tasks: {e}")
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else ".", exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump({
                    "global": self.global_tasks,
                    "mode": self.mode_tasks
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save tasks: {e}")
    
    def add_global(self, task: str, due: Optional[str] = None, priority: str = "normal") -> str:
        """Add a global task (timers/reminders)"""
        task_obj = {
            "id": len(self.global_tasks) + 1,
            "task": task,
            "due": due,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.global_tasks.append(task_obj)
        self._save()
        return f"Added global task: {task}"
    
    def add_mode(self, mode: str, task: str, priority: str = "normal") -> str:
        """Add a task specific to a mode"""
        if mode not in self.mode_tasks:
            self.mode_tasks[mode] = []
        task_obj = {
            "id": len(self.mode_tasks[mode]) + 1,
            "task": task,
            "priority": priority,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.mode_tasks[mode].append(task_obj)
        self._save()
        return f"Added task to {mode} mode: {task}"
    
    def list_global(self) -> str:
        if not self.global_tasks:
            return "No global tasks"
        result = "Global Tasks:\n"
        for t in self.global_tasks:
            status = "✓" if t["completed"] else "○"
            result += f"  {status} [{t['id']}] {t['task']}"
            if t.get("due"):
                result += f" (due: {t['due']})"
            result += "\n"
        return result.strip()
    
    def list_mode(self, mode: str) -> str:
        if mode not in self.mode_tasks or not self.mode_tasks[mode]:
            return f"No tasks for {mode} mode"
        result = f"Tasks for {mode} mode:\n"
        for t in self.mode_tasks[mode]:
            status = "✓" if t["completed"] else "○"
            result += f"  {status} [{t['id']}] {t['task']}\n"
        return result.strip()
    
    def complete_global(self, task_id: int) -> str:
        for t in self.global_tasks:
            if t["id"] == task_id:
                t["completed"] = True
                self._save()
                return f"Completed task: {t['task']}"
        return "Task not found"
    
    def complete_mode(self, mode: str, task_id: int) -> str:
        if mode not in self.mode_tasks:
            return "Mode not found"
        for t in self.mode_tasks[mode]:
            if t["id"] == task_id:
                t["completed"] = True
                self._save()
                return f"Completed task: {t['task']}"
        return "Task not found"
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "tasks_add_global",
                    "description": "Add a global task, timer, or reminder",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "The task description"},
                            "due": {"type": "string", "description": "Optional due date/time"},
                            "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"}
                        },
                        "required": ["task"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tasks_add_mode",
                    "description": "Add a task specific to a mode",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "description": "The mode (Play, Assist, Explore, Auto, Idle)"},
                            "task": {"type": "string", "description": "The task description"},
                            "priority": {"type": "string", "enum": ["low", "normal", "high"], "default": "normal"}
                        },
                        "required": ["mode", "task"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tasks_list_global",
                    "description": "List all global tasks and reminders",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tasks_list_mode",
                    "description": "List tasks for a specific mode",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "description": "The mode name"}
                        },
                        "required": ["mode"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tasks_complete_global",
                    "description": "Mark a global task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "The task ID"}
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tasks_complete_mode",
                    "description": "Mark a mode-specific task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "description": "The mode name"},
                            "task_id": {"type": "integer", "description": "The task ID"}
                        },
                        "required": ["mode", "task_id"]
                    }
                }
            }
        ]

if __name__ == "__main__":
    t = Tasks()
    print(t.add_global("Reminder: Check robot battery", due="2024-12-31", priority="high"))
    print(t.add_mode("Play", "Find a ball to play with"))
    print(t.list_global())
    print(t.list_mode("Play"))
