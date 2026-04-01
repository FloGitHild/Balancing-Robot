import json
import os
import uuid
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum


class Priority(Enum):
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """Priority-based task queue. All agent behavior is driven by tasks."""

    def __init__(self, data_dir: str = "data/tasks"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.tasks: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self._counter = 0

        self.current_tasks_path = os.path.join(data_dir, "current_tasks.json")
        self.completed_tasks_path = os.path.join(data_dir, "completed_tasks.json")

        self._load()

    def _load(self):
        try:
            with open(self.current_tasks_path, "r") as f:
                data = json.load(f)
                self.tasks = data
                self._counter = max((t.get("_id_num", 0) for t in data), default=0)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []

    def _save_current(self):
        with open(self.current_tasks_path, "w") as f:
            json.dump(self.tasks, f, indent=2)

    def _log_completed(self, task: Dict[str, Any]):
        try:
            with open(self.completed_tasks_path, "r") as f:
                completed = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            completed = []

        completed.append(task)
        completed = completed[-200:]

        with open(self.completed_tasks_path, "w") as f:
            json.dump(completed, f, indent=2)

    def create(
        self,
        goal: str,
        priority: Priority,
        task_type: str = "manual",
        deadline: Optional[datetime] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        with self.lock:
            self._counter += 1
            task = {
                "id": str(uuid.uuid4()),
                "_id_num": self._counter,
                "type": task_type,
                "priority": priority.value,
                "priority_name": priority.name,
                "goal": goal,
                "deadline": deadline.isoformat() if deadline else None,
                "status": TaskStatus.PENDING.value,
                "data": data or {},
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "result": "",
            }
            self.tasks.append(task)
            self._sort()
            self._save_current()
            return task["id"]

    def _sort(self):
        self.tasks.sort(key=lambda t: (t["priority"], t.get("deadline") or "9999"))

    def get_next(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            now = datetime.now()
            for task in self.tasks:
                if task["status"] != TaskStatus.PENDING.value:
                    continue
                if task.get("deadline"):
                    dl = datetime.fromisoformat(task["deadline"])
                    if dl > now:
                        continue
                return task
            return None

    def get_pending(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [t for t in self.tasks if t["status"] == TaskStatus.PENDING.value]

    def get_due_timers(self) -> List[Dict[str, Any]]:
        with self.lock:
            now = datetime.now()
            due = []
            for task in self.tasks:
                if task["status"] != TaskStatus.PENDING.value:
                    continue
                if task["type"] == "timer" and task.get("deadline"):
                    dl = datetime.fromisoformat(task["deadline"])
                    if dl <= now:
                        due.append(task)
            return due

    def mark_running(self, task_id: str):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = TaskStatus.RUNNING.value
                    task["started_at"] = datetime.now().isoformat()
                    self._save_current()
                    break

    def mark_completed(self, task_id: str, result: str = ""):
        with self.lock:
            for i, task in enumerate(self.tasks):
                if task["id"] == task_id:
                    task["status"] = TaskStatus.COMPLETED.value
                    task["completed_at"] = datetime.now().isoformat()
                    task["result"] = result
                    completed_task = self.tasks.pop(i)
                    self._log_completed(completed_task)
                    self._save_current()
                    break

    def mark_failed(self, task_id: str, reason: str = ""):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = TaskStatus.FAILED.value
                    task["result"] = f"Failed: {reason}"
                    task["completed_at"] = datetime.now().isoformat()
                    self._save_current()
                    break

    def cancel(self, task_id: str):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = TaskStatus.CANCELLED.value
                    self._save_current()
                    break

    def clear_type(self, task_type: str):
        with self.lock:
            self.tasks = [t for t in self.tasks if t["type"] != task_type]
            self._save_current()

    def clear_mode_tasks(self):
        self.clear_type("mode")

    def add_timer(self, goal: str, minutes: int) -> str:
        deadline = datetime.now() + timedelta(minutes=minutes)
        return self.create(
            goal=goal,
            priority=Priority.URGENT,
            task_type="timer",
            deadline=deadline,
        )

    def add_reminder(self, goal: str, hour: int, minute: int = 0) -> str:
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target = target.replace(day=target.day + 1)
        return self.create(
            goal=goal,
            priority=Priority.HIGH,
            task_type="reminder",
            deadline=target,
        )

    def add_face_trigger(self, name: str, is_new: bool) -> str:
        prio = Priority.HIGH
        goal = f"Greet {name}" if not is_new else f"Introduce yourself to {name}"
        return self.create(
            goal=goal,
            priority=prio,
            task_type="face",
            data={"name": name, "is_new": is_new},
        )

    def add_mode_mission(self, mode: str, goal: str) -> str:
        return self.create(
            goal=goal,
            priority=Priority.LOW,
            task_type="mode",
            data={"mode": mode},
        )

    def add_user_command(self, command: str) -> str:
        return self.create(
            goal=f"Handle user command: {command}",
            priority=Priority.NORMAL,
            task_type="command",
            data={"command": command},
        )

    def summary(self) -> str:
        with self.lock:
            pending = len([t for t in self.tasks if t["status"] == TaskStatus.PENDING.value])
            running = len([t for t in self.tasks if t["status"] == TaskStatus.RUNNING.value])
            lines = [f"Tasks: {pending} pending, {running} running"]
            for t in self.tasks[:5]:
                if t["status"] == TaskStatus.PENDING.value:
                    lines.append(f"  [{t['priority_name']}] {t['goal']}")
            return "\n".join(lines)
