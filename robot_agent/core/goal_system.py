from typing import Dict, Optional


MODE_GOALS: Dict[str, str] = {
    "Idle": "Wait for triggers. Observe surroundings. Do not initiate actions unless a task requires it.",
    "Play": "Find people and interact playfully. Make jokes. Look for objects to bring to people. Entertain.",
    "Assist": "Ask if people need help. Handle reminders, timers, and notes. Do research if asked.",
    "Explore": "Move around safely. Discover new objects and areas. Build a gallery of interesting things.",
    "Auto": "Mix behaviors from all modes. Make experimental decisions. Be creative but safe.",
}


class GoalSystem:
    """Resolves the current goal based on mode and active task."""

    def resolve(self, mode: str, active_task: Optional[dict]) -> str:
        base_goal = MODE_GOALS.get(mode, MODE_GOALS["Idle"])

        if active_task:
            task_goal = active_task.get("goal", "")
            priority = active_task.get("priority", 4)
            if priority <= 2:
                return f"URGENT TASK: {task_goal}. Drop everything else and handle this. Base context: {base_goal}"
            else:
                return f"Current task: {task_goal}. Base context: {base_goal}"

        return base_goal
