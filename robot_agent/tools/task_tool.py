from typing import Dict, Any, List


class TaskTool:
    """Tools for creating, listing, and completing tasks."""

    def __init__(self, task_manager):
        self.tm = task_manager

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "create_task":
            return self._create_task(
                goal=args.get("goal", ""),
                priority=args.get("priority", 3),
                time=args.get("time", ""),
            )
        elif tool_name == "list_tasks":
            return self._list_tasks()
        elif tool_name == "complete_task":
            return self._complete_task(args.get("id", ""))
        return f"Unknown task tool: {tool_name}"

    def _create_task(self, goal: str, priority: int, time: str = "") -> str:
        if not goal:
            return "Cannot create task without a goal."
        from robot_agent.core.task_manager import Priority
        try:
            prio = Priority(priority)
        except ValueError:
            prio = Priority.NORMAL

        task_id = self.tm.create(goal=goal, priority=prio, task_type="llm_created")
        return f"Task created: {goal} (ID: {task_id[:8]}..., priority: {prio.name})"

    def _list_tasks(self) -> str:
        pending = self.tm.get_pending()
        if not pending:
            return "No pending tasks."
        lines = ["Pending tasks:"]
        for t in pending:
            dl = ""
            if t.get("deadline"):
                from datetime import datetime
                dl_dt = datetime.fromisoformat(t["deadline"])
                dl = f" due {dl_dt.strftime('%H:%M')}"
            lines.append(f"  [{t['priority_name']}] {t['goal']}{dl} (ID: {t['id'][:8]})")
        return "\n".join(lines)

    def _complete_task(self, task_id: str) -> str:
        if not task_id:
            return "No task ID provided."
        self.tm.mark_completed(task_id, "Completed via tool")
        return f"Task {task_id[:8]} marked as completed."

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task for future execution. Use this to schedule actions, set reminders, or queue work. priority: 1=URGENT (timers due now), 2=HIGH (important reminders), 3=NORMAL (user commands), 4=LOW (mode missions). time: optional hint like 'in 5 minutes'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string", "description": "What the task should accomplish"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 4, "default": 3},
                            "time": {"type": "string", "description": "Optional time hint (e.g. 'in 5 minutes')"},
                        },
                        "required": ["goal"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List all pending tasks in the queue with their priority and deadline.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed by its ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Task ID to complete"},
                        },
                        "required": ["id"],
                    },
                },
            },
        ]
