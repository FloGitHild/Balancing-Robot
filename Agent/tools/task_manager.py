"""
Task Manager - Handles triggers, prioritization, and task execution
"""

import threading
import time
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict
from enum import Enum

class TaskPriority(Enum):
    URGENT = 1      # Timers, immediate triggers
    HIGH = 2        # Face detection, mode changes
    NORMAL = 3      # Regular user input
    LOW = 4         # Mode-based missions

class TaskType(Enum):
    TIMER = "timer"
    TRIGGER = "trigger"
    USER_INPUT = "user_input"
    MODE_MISSION = "mode_mission"
    FACE_DETECTED = "face_detected"
    FACE_RETURNED = "face_returned"

@dataclass
class Task:
    id: int
    name: str
    task_type: TaskType
    priority: TaskPriority
    created_at: datetime
    due_time: Optional[datetime] = None
    data: Dict = field(default_factory=dict)
    completed: bool = False
    completed_at: Optional[datetime] = None
    result: str = ""
    iterations: int = 0
    execution_time: float = 0.0
    
    def __lt__(self, other):
        # Sort by priority first, then by due time
        if self.priority != other.priority:
            return self.priority.value < other.priority.value
        if self.due_time and other.due_time:
            return self.due_time < other.due_time
        return self.created_at < other.created_at

class TaskManager:
    def __init__(self, log_dir: str = None):
        # Default to data directory in Agent folder
        if log_dir is None:
            import os
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tasks")
        
        self.log_dir = log_dir
        self.tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.current_task: Optional[Task] = None
        self.task_counter = 0
        self.lock = threading.Lock()
        
        # Triggers
        self.triggers: Dict[str, Callable] = {}
        self.known_faces: List[str] = []  # Track known faces
        self.last_seen_faces: Dict[str, datetime] = {}
        
        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        
        os.makedirs(log_dir, exist_ok=True)
        self._load_completed_tasks()
    
    def _load_completed_tasks(self):
        """Load completed tasks from log"""
        log_file = os.path.join(self.log_dir, "completed_tasks.json")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    data = json.load(f)
                    for t in data:
                        task = Task(
                            id=t["id"],
                            name=t["name"],
                            task_type=TaskType(t["task_type"]),
                            priority=TaskPriority(t["priority"]),
                            created_at=datetime.fromisoformat(t["created_at"]),
                            due_time=datetime.fromisoformat(t["due_time"]) if t.get("due_time") else None,
                            data=t.get("data", {}),
                            completed=True,
                            completed_at=datetime.fromisoformat(t["completed_at"]) if t.get("completed_at") else None,
                            result=t.get("result", ""),
                            iterations=t.get("iterations", 0),
                            execution_time=t.get("execution_time", 0)
                        )
                        self.completed_tasks.append(task)
            except Exception as e:
                print(f"Error loading tasks: {e}")
    
    def _save_completed_tasks(self):
        """Save completed tasks to log"""
        log_file = os.path.join(self.log_dir, "completed_tasks.json")
        data = []
        # Keep last 100 completed tasks
        for t in self.completed_tasks[-100:]:
            data.append({
                "id": t.id,
                "name": t.name,
                "task_type": t.task_type.value,
                "priority": t.priority.value,
                "created_at": t.created_at.isoformat(),
                "due_time": t.due_time.isoformat() if t.due_time else None,
                "data": t.data,
                "completed": True,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "result": t.result,
                "iterations": t.iterations,
                "execution_time": t.execution_time
            })
        with open(log_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_task(self, name: str, task_type: TaskType, priority: TaskPriority, 
                 due_time: Optional[datetime] = None, data: Dict = None) -> int:
        """Add a new task with priority"""
        with self.lock:
            self.task_counter += 1
            task = Task(
                id=self.task_counter,
                name=name,
                task_type=task_type,
                priority=priority,
                created_at=datetime.now(),
                due_time=due_time,
                data=data or {}
            )
            self.tasks.append(task)
            # Sort by priority
            self.tasks.sort()
            self._save_current_tasks()
            return task.id
    
    def add_timer(self, task_name: str, minutes: int, data: Dict = None) -> int:
        """Add a timer task"""
        due = datetime.now() + timedelta(minutes=minutes)
        return self.add_task(
            name=task_name,
            task_type=TaskType.TIMER,
            priority=TaskPriority.URGENT,
            due_time=due,
            data=data
        )
    
    def add_user_input(self, input_text: str) -> int:
        """Add user input as task"""
        return self.add_task(
            name=f"User: {input_text[:50]}",
            task_type=TaskType.USER_INPUT,
            priority=TaskPriority.NORMAL,
            data={"input": input_text}
        )
    
    def add_mode_mission(self, mode: str, description: str = "") -> int:
        """Add mode-based mission"""
        return self.add_task(
            name=f"Mode {mode}: {description or 'Auto mission'}",
            task_type=TaskType.MODE_MISSION,
            priority=TaskPriority.LOW,
            data={"mode": mode, "description": description}
        )
    
    def add_face_trigger(self, face_name: str, is_new: bool = False) -> int:
        """Add face detection trigger"""
        task_type = TaskType.FACE_DETECTED if is_new else TaskType.FACE_RETURNED
        return self.add_task(
            name=f"Face detected: {face_name}",
            task_type=task_type,
            priority=TaskPriority.HIGH,
            data={"face_name": face_name, "is_new": is_new}
        )
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next pending task (highest priority)"""
        with self.lock:
            now = datetime.now()
            
            # First check for due tasks
            for task in self.tasks:
                if not task.completed:
                    if task.due_time and task.due_time <= now:
                        return task
            
            # Then return highest priority non-due task
            for task in self.tasks:
                if not task.completed:
                    return task
            
            return None
    
    def get_due_tasks(self) -> List[Task]:
        """Get all tasks that are due"""
        with self.lock:
            now = datetime.now()
            due = []
            for task in self.tasks:
                if not task.completed:
                    if task.due_time and task.due_time <= now:
                        due.append(task)
            return due
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        with self.lock:
            return [t for t in self.tasks if not t.completed]
    
    def complete_task(self, task_id: int, result: str, iterations: int, execution_time: float):
        """Mark task as completed"""
        with self.lock:
            for task in self.tasks:
                if task.id == task_id:
                    task.completed = True
                    task.completed_at = datetime.now()
                    task.result = result
                    task.iterations = iterations
                    task.execution_time = execution_time
                    self.completed_tasks.append(task)
                    self._save_completed_tasks()
                    self._save_current_tasks()
                    break
    
    def clear_mode_tasks(self):
        """Clear all mode-based tasks (called on mode change)"""
        with self.lock:
            self.tasks = [t for t in self.tasks if t.task_type != TaskType.MODE_MISSION]
            self._save_current_tasks()
    
    def register_trigger(self, name: str, callback: Callable):
        """Register a trigger callback"""
        self.triggers[name] = callback
    
    def update_known_faces(self, faces: List[str]):
        """Update known faces and check for new/returned"""
        with self.lock:
            current_time = datetime.now()
            
            for face in faces:
                if face != "Unknown":
                    if face not in self.known_faces:
                        # New face detected
                        self.known_faces.append(face)
                        self.last_seen_faces[face] = current_time
                        print(f"👤 New face detected: {face}")
                    elif face not in self.last_seen_faces or \
                         (current_time - self.last_seen_faces[face]).seconds > 300:
                        # Face returned after 5 minutes
                        print(f"👤 Welcome back: {face}")
                        self.last_seen_faces[face] = current_time
    
    def _save_current_tasks(self):
        """Save current pending tasks"""
        tasks_file = os.path.join(self.log_dir, "current_tasks.json")
        data = []
        for t in self.tasks:
            if not t.completed:
                data.append({
                    "id": t.id,
                    "name": t.name,
                    "task_type": t.task_type.value,
                    "priority": t.priority.value,
                    "created_at": t.created_at.isoformat(),
                    "due_time": t.due_time.isoformat() if t.due_time else None,
                    "data": t.data
                })
        with open(tasks_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_summary(self) -> str:
        """Get task summary"""
        with self.lock:
            pending = len([t for t in self.tasks if not t.completed])
            due = len(self.get_due_tasks())
            
            # Recent completed
            recent = self.completed_tasks[-5:] if self.completed_tasks else []
            recent_str = "\n".join([f"  ✓ {t.name} ({t.execution_time:.1f}s)" for t in recent])
            
            return f"""
📋 Task Manager:
  Pending: {pending}
  Due now: {due}
  Completed: {len(self.completed_tasks)}

Recent:
{recent_str or '  No completed tasks'}
"""


if __name__ == "__main__":
    tm = TaskManager()
    tm.add_timer("Test timer", 5)
    tm.add_user_input("Hello!")
    print(tm.get_summary())
    print(tm.get_next_task())