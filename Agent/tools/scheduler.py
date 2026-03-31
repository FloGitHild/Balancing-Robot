import threading
import time
import json
import os
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class ScheduledTask:
    id: int
    task: str
    due_time: Optional[datetime] = None
    interval_minutes: Optional[int] = None
    priority: str = "normal"
    completed: bool = False
    last_run: Optional[datetime] = None
    created: datetime = field(default_factory=datetime.now)
    callback: Optional[Callable] = None

class Scheduler:
    def __init__(self, storage_path: str = "data/scheduler.json"):
        self.storage_path = storage_path
        self.tasks: List[ScheduledTask] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._callbacks: Dict[str, Callable] = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for t in data.get("tasks", []):
                        task = ScheduledTask(
                            id=t["id"],
                            task=t["task"],
                            due_time=datetime.fromisoformat(t["due_time"]) if t.get("due_time") else None,
                            interval_minutes=t.get("interval_minutes"),
                            priority=t.get("priority", "normal"),
                            completed=t.get("completed", False),
                            last_run=datetime.fromisoformat(t["last_run"]) if t.get("last_run") else None,
                            created=datetime.fromisoformat(t["created"])
                        )
                        self.tasks.append(task)
            except Exception as e:
                print(f"Scheduler load error: {e}")
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else ".", exist_ok=True)
            with open(self.storage_path, "w") as f:
                data = {
                    "tasks": [
                        {
                            "id": t.id,
                            "task": t.task,
                            "due_time": t.due_time.isoformat() if t.due_time else None,
                            "interval_minutes": t.interval_minutes,
                            "priority": t.priority,
                            "completed": t.completed,
                            "last_run": t.last_run.isoformat() if t.last_run else None,
                            "created": t.created.isoformat()
                        }
                        for t in self.tasks
                    ]
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Scheduler save error: {e}")
    
    def register_callback(self, event: str, callback: Callable):
        self._callbacks[event] = callback
    
    def add_one_time(self, task: str, due_time: datetime, priority: str = "normal") -> int:
        with self._lock:
            task_id = max([t.id for t in self.tasks], default=0) + 1
            new_task = ScheduledTask(
                id=task_id,
                task=task,
                due_time=due_time,
                priority=priority
            )
            self.tasks.append(new_task)
            self._save()
            return task_id
    
    def add_recurring(self, task: str, interval_minutes: int, priority: str = "normal") -> int:
        with self._lock:
            task_id = max([t.id for t in self.tasks], default=0) + 1
            new_task = ScheduledTask(
                id=task_id,
                task=task,
                interval_minutes=interval_minutes,
                priority=priority
            )
            self.tasks.append(new_task)
            self._save()
            return task_id
    
    def add_timer(self, task: str, delay_minutes: int, priority: str = "normal") -> int:
        due = datetime.now() + timedelta(minutes=delay_minutes)
        return self.add_one_time(task, due, priority)
    
    def remove(self, task_id: int) -> str:
        with self._lock:
            for t in self.tasks:
                if t.id == task_id:
                    self.tasks.remove(t)
                    self._save()
                    return f"Removed task {task_id}"
            return f"Task {task_id} not found"
    
    def get_due_tasks(self) -> List[ScheduledTask]:
        with self._lock:
            now = datetime.now()
            due = []
            for t in self.tasks:
                if t.completed:
                    continue
                if t.due_time and t.due_time <= now:
                    due.append(t)
                elif t.interval_minutes and t.last_run:
                    next_run = t.last_run + timedelta(minutes=t.interval_minutes)
                    if next_run <= now:
                        due.append(t)
            return due
    
    def get_pending(self) -> str:
        with self._lock:
            if not self.tasks:
                return "No scheduled tasks"
            result = "Scheduled Tasks:\n"
            for t in self.tasks:
                status = "✓" if t.completed else "○"
                if t.due_time:
                    time_info = f" due {t.due_time.strftime('%H:%M')}"
                elif t.interval_minutes:
                    time_info = f" every {t.interval_minutes}min"
                else:
                    time_info = ""
                result += f"  {status} [{t.id}] {t.task}{time_info} ({t.priority})\n"
            return result.strip()
    
    def complete(self, task_id: int) -> str:
        with self._lock:
            for t in self.tasks:
                if t.id == task_id:
                    if t.interval_minutes:
                        t.last_run = datetime.now()
                        t.completed = False
                    else:
                        t.completed = True
                    self._save()
                    return f"Completed: {t.task}"
            return f"Task {task_id} not found"
    
    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"✅ Scheduler started with {len(self.tasks)} tasks")
    
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🛑 Scheduler stopped")
    
    def _run_loop(self):
        while self.running:
            due_tasks = self.get_due_tasks()
            for task in due_tasks:
                print(f"🔔 Running task: {task.task}")
                if callback := self._callbacks.get("task_due"):
                    try:
                        callback(task)
                    except Exception as e:
                        print(f"Task callback error: {e}")
                
                self.complete(task.id)
            
            time.sleep(10)
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "scheduler_add_timer",
                    "description": "Add a timer that runs after X minutes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "What to do"},
                            "minutes": {"type": "integer", "description": "Minutes until execution"}
                        },
                        "required": ["task", "minutes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scheduler_add_scheduled",
                    "description": "Schedule a task at a specific time (HH:MM)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "What to do"},
                            "time": {"type": "string", "description": "Time in HH:MM format"}
                        },
                        "required": ["task", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scheduler_add_recurring",
                    "description": "Add a recurring task every X minutes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "What to do"},
                            "interval_minutes": {"type": "integer", "description": "Repeat every X minutes"}
                        },
                        "required": ["task", "interval_minutes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scheduler_list",
                    "description": "List all scheduled tasks",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scheduler_complete",
                    "description": "Mark a task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "Task ID"}
                        },
                        "required": ["task_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scheduler_remove",
                    "description": "Remove a scheduled task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer", "description": "Task ID"}
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

if __name__ == "__main__":
    s = Scheduler()
    print(s.add_timer("Check battery", 5))
    print(s.add_recurring("Look around", 10))
    print(s.get_pending())
    s.start()
    time.sleep(15)
    s.stop()