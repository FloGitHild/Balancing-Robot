import json
import time
import threading
import sys
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from robot_agent.core.state_engine import StateEngine
from robot_agent.core.goal_system import GoalSystem
from robot_agent.core.task_manager import TaskManager, Priority
from robot_agent.core.memory import MemorySystem
from robot_agent.core.llm_client import LLMClient
from robot_agent.core.safety import SafetyLayer
from robot_agent.tools.movement import MovementTool
from robot_agent.tools.vision import VisionTool
from robot_agent.tools.audio import AudioTool
from robot_agent.tools.mood import MoodTool
from robot_agent.tools.task_tool import TaskTool
from robot_agent.tools.memory_tool import MemoryTool
from robot_agent.tools.research import ResearchTool
from robot_agent.comm.websocket_client import CommLayer
import robot_agent.config as config


class TimerDaemon:
    """Background thread that checks for due timer tasks and triggers them."""

    def __init__(self, task_manager, on_timer_due=None):
        self.tm = task_manager
        self.on_timer_due = on_timer_due
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="TimerDaemon")
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _loop(self):
        while self.running:
            try:
                for task in self.tm.get_due_timers():
                    self.tm.mark_running(task["id"])
                    if self.on_timer_due:
                        self.on_timer_due(task)
            except Exception as e:
                _log(f"[TimerDaemon] Error: {e}")
            time.sleep(2)


class OutputFormatter:
    """Clean, non-mixing terminal output."""

    _lock = threading.Lock()

    @classmethod
    def print_agent(cls, text: str):
        with cls._lock:
            sys.stdout.write(f"\r\033[K  {text}\n")
            sys.stdout.flush()

    @classmethod
    def print_banner(cls, text: str):
        with cls._lock:
            sys.stdout.write(f"\n{'='*50}\n  {text}\n{'='*50}\n")
            sys.stdout.flush()

    @classmethod
    def print_status(cls, mode: str, mood: str, tasks: int):
        with cls._lock:
            sys.stdout.write(f"\r\033[K  [{mode}] mood={mood} | pending={tasks} | {datetime.now().strftime('%H:%M:%S')}")
            sys.stdout.flush()

    @classmethod
    def prompt(cls) -> str:
        with cls._lock:
            sys.stdout.write("\r\033[K\nYou: ")
            sys.stdout.flush()
            try:
                return input()
            except (EOFError, KeyboardInterrupt):
                return ""


def _log(msg: str):
    OutputFormatter.print_agent(msg)


class InputClassifier:
    """Fast classification of user input to decide if LLM is needed."""

    TIMER_PATTERN = re.compile(r'(timer|reminder|alarm|wecker|erinnere)\s*(?:in|for|nach|\(?\s*)\s*(\d+)\s*(min|minute|sec|second|hour|stunde|minuten|sekunden|stunden)?', re.IGNORECASE)
    TIME_PATTERN = re.compile(r'(timer|reminder|alarm)\s+.*?(\d{1,2}):(\d{2})', re.IGNORECASE)
    MODE_PATTERN = re.compile(r'^mode\s+(\w+)', re.IGNORECASE)
    TASK_PATTERN = re.compile(r'^(task|aufgabe)\s+(.+)', re.IGNORECASE)
    STATUS_PATTERN = re.compile(r'^(status|state|what.*doing|was.*los|was.*machst)', re.IGNORECASE)
    HELP_PATTERN = re.compile(r'^(help|hilfe|commands|what can you|was kannst)', re.IGNORECASE)
    TIME_QUERY = re.compile(r'(what time|wie spat|wie viel uhr|current time|uhrzeit)', re.IGNORECASE)
    WEATHER_QUERY = re.compile(r'(weather|wetter|temperature|temperatur)', re.IGNORECASE)
    FUN_FACT = re.compile(r'(fun fact|funny|joke|witz|fact.*know|fact.*tell|erzaehl.*witz|witz.*erzahl)', re.IGNORECASE)
    VISION_QUERY = re.compile(r'(what.*see|what.*look|was.*siehst|was.*seh|look.*around|umseh|was.*da|erkenn.*etwas)', re.IGNORECASE)
    GREETING = re.compile(r'^(hi|hello|hey|hallo|moin|servus|gruess|greet|guten tag|guten morgen|guten abend)', re.IGNORECASE)
    RESEARCH_QUERY = re.compile(r'(research|search|what.*know|what.*about|was.*weisst|was.*kennst|info.*about|info.*uber)', re.IGNORECASE)
    MEMORY_QUERY = re.compile(r'(remember|recall|what.*memory|was.*erinner|was.*weisst.*uber|do.*know.*me)', re.IGNORECASE)
    THANKS = re.compile(r'(thanks|thank you|danke|dankeschoen|thx)', re.IGNORECASE)
    GOODBYE = re.compile(r'(bye|goodbye|tschuess|ciao|auf wiedersehen|bis spaeter)', re.IGNORECASE)

    @classmethod
    def classify(cls, text: str) -> Dict[str, Any]:
        text = text.strip()

        if cls.MODE_PATTERN.match(text):
            return {"type": "mode", "match": cls.MODE_PATTERN.match(text)}

        if cls.TASK_PATTERN.match(text):
            return {"type": "task", "match": cls.TASK_PATTERN.match(text)}

        if cls.STATUS_PATTERN.match(text):
            return {"type": "status"}

        if cls.HELP_PATTERN.match(text):
            return {"type": "help"}

        if cls.TIME_QUERY.search(text):
            return {"type": "time_query"}

        if cls.WEATHER_QUERY.search(text):
            return {"type": "weather_query"}

        if cls.FUN_FACT.search(text):
            return {"type": "fun_fact"}

        if cls.VISION_QUERY.search(text):
            return {"type": "vision_query"}

        timer_match = cls.TIMER_PATTERN.search(text)
        if timer_match:
            minutes = int(timer_match.group(2))
            unit = (timer_match.group(3) or "min").lower()
            if "hour" in unit or "stunde" in unit:
                minutes *= 60
            elif "sec" in unit or "sekunde" in unit:
                minutes = max(1, minutes // 60)
            goal = text[:80]
            return {"type": "timer", "minutes": minutes, "goal": goal}

        time_match = cls.TIME_PATTERN.search(text)
        if time_match:
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))
            return {"type": "reminder_time", "hour": hour, "minute": minute, "goal": text[:80]}

        if cls.GREETING.match(text):
            return {"type": "greeting"}

        if cls.THANKS.search(text):
            return {"type": "thanks"}

        if cls.GOODBYE.search(text):
            return {"type": "goodbye"}

        if cls.RESEARCH_QUERY.search(text):
            return {"type": "research_query", "query": text}

        if cls.MEMORY_QUERY.search(text):
            return {"type": "memory_query", "query": text}

        return {"type": "llm"}


class Agent:
    """Task-based autonomous robot agent. All behavior is driven by the task queue."""

    def __init__(self, mode: str = None, robot_url: str = None):
        self.mode = mode or config.DEFAULT_MODE
        self.robot_url = robot_url or config.ROBOT_URL

        self.state = StateEngine()
        self.state.state["mode"] = self.mode

        self.goal_system = GoalSystem()
        self.task_manager = TaskManager()
        self.memory = MemorySystem()
        self.llm = LLMClient()
        self.safety = SafetyLayer()
        self.comm = CommLayer(self.robot_url)

        self.vision_tool = VisionTool()
        self.movement_tool = MovementTool(self.robot_url)
        self.audio_tool = AudioTool()
        self.mood_tool = MoodTool()
        self.task_tool = TaskTool(self.task_manager)
        self.memory_tool = MemoryTool(self.memory)
        self.research_tool = ResearchTool()

        self.all_tools = {
            "movement": self.movement_tool,
            "vision": self.vision_tool,
            "audio": self.audio_tool,
            "mood": self.mood_tool,
            "task": self.task_tool,
            "memory": self.memory_tool,
            "research": self.research_tool,
        }

        self.tool_definitions = []
        for tool in self.all_tools.values():
            self.tool_definitions.extend(tool.get_definitions())

        self.system_prompt = self._build_system_prompt()
        self.running = False
        self._loop_thread = None
        self._timer_daemon = TimerDaemon(self.task_manager, on_timer_due=self._on_timer_due)

        self._cycle_count = 0
        self._last_cycle_time = 0

        OutputFormatter.print_agent(f"Agent initialized. Mode: {self.mode}")

    def _build_system_prompt(self) -> str:
        mode_desc = config.MODES.get(self.mode, {}).get("description", "")
        goal = config.MODES.get(self.mode, {}).get("goal", "")

        return f"""You are a robot agent. Respond naturally. Use tools ONLY when they add real value.

Mode: {self.mode} - {mode_desc}
Current mood: {self.mood_tool.get_current()['emotion']}

RULES:
1. Respond with plain text for greetings, questions, and conversation.
2. ONLY use tools when the user explicitly asks for an action (move, set timer, etc).
3. If unsure, respond with text - do NOT call tools unnecessarily.
4. Keep answers SHORT (1-2 sentences).
5. NEVER invent facts.

TOOLS (use sparingly):
- move, turn, set_head, move_arm, stop (physical actions)
- get_visible_objects, get_visible_faces (check surroundings)
- speak (say something aloud)
- set_mood (express emotion)
- create_task, list_tasks, complete_task (task management)
- remember, recall (memory)
- research, read_local_file, get_current_time, get_weather, get_fun_fact (knowledge)"""

    def collect_inputs(self) -> Dict[str, Any]:
        inputs = self.comm.get_inputs()
        vision_data = inputs.get("vision", {})
        if vision_data:
            self.vision_tool.update(
                vision_data.get("objects", []),
                vision_data.get("people", []),
            )
        return inputs

    def update_state(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return self.state.update(inputs)

    def _handle_fast_path(self, classification: Dict[str, Any], user_input: str) -> Optional[Dict[str, Any]]:
        """Handle simple inputs without LLM. Returns result dict or None if LLM needed."""
        ctype = classification["type"]

        if ctype == "mode":
            new_mode = classification["match"].group(1).capitalize()
            result = self.set_mode(new_mode)
            return {"goal": f"Change mode to {new_mode}", "task": None, "plan": result,
                    "tool_calls": [], "results": [result], "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "task":
            goal = classification["match"].group(2).strip()
            result = self.add_command(goal)
            return {"goal": goal, "task": None, "plan": "Added task to queue",
                    "tool_calls": [], "results": [result], "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "status":
            pending = len(self.task_manager.get_pending())
            status = f"Mode: {self.mode} | Mood: {self.mood_tool.get_current()['emotion']} | Pending tasks: {pending} | Cycles: {self._cycle_count}"
            if self._last_cycle_time > 0:
                status += f" | Last cycle: {self._last_cycle_time:.1f}s"
            return {"goal": "Status check", "task": None, "plan": status,
                    "tool_calls": [], "results": [status], "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "help":
            help_text = ("Commands: quit | mode <name> | task <goal> | timer <goal> <min>\n"
                        "Tools: move, speak, set_mood, create_task, research, remember\n"
                        f"Current mode: {self.mode}")
            return {"goal": "Help", "task": None, "plan": help_text,
                    "tool_calls": [], "results": [help_text], "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "timer":
            minutes = classification["minutes"]
            goal = classification.get("goal", user_input)
            result = self.add_timer(goal, minutes)
            self.mood_tool._set_mood("happy", 0.6)
            return {"goal": f"Set timer for {minutes}min", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "reminder_time":
            hour = classification["hour"]
            minute = classification["minute"]
            goal = classification.get("goal", user_input)
            task_id = self.task_manager.add_reminder(goal, hour, minute)
            result = f"Reminder set for {hour:02d}:{minute:02d}: {goal}"
            self.mood_tool._set_mood("happy", 0.6)
            return {"goal": f"Set reminder at {hour:02d}:{minute:02d}", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "time_query":
            result = self.research_tool._get_current_time()
            return {"goal": "Get current time", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "weather_query":
            location = re.search(r'(?:in|for|at|nach)\s+(\w+)', user_input, re.IGNORECASE)
            loc = location.group(1) if location else "your location"
            result = self.research_tool._get_weather(loc)
            return {"goal": f"Weather for {loc}", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "fun_fact":
            result = self.research_tool._get_fun_fact()
            self.mood_tool._set_mood("happy", 0.7)
            return {"goal": "Tell fun fact", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "greeting":
            import random
            greetings_en = ["Hello! Nice to see you!", "Hi there! How can I help?", "Hey! What's up?", "Hello! Good to have you here."]
            greetings_de = ["Hallo! Schoen, dich zu sehen!", "Hi! Wie kann ich helfen?", "Hallo! Was gibt's?"]
            is_german = any(w in user_input.lower() for w in ["hallo", "moin", "servus", "gruess", "guten"])
            result = random.choice(greetings_de if is_german else greetings_en)
            self.mood_tool._set_mood("happy", 0.7)
            return {"goal": "Greet user", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "thanks":
            import random
            responses_en = ["You're welcome!", "Happy to help!", "Anytime!", "No problem!"]
            responses_de = ["Gern geschehen!", "Immer wieder gerne!", "Kein Problem!", "Freut mich!"]
            is_german = any(w in user_input.lower() for w in ["danke", "dankeschoen"])
            result = random.choice(responses_de if is_german else responses_en)
            self.mood_tool._set_mood("happy", 0.6)
            return {"goal": "Respond to thanks", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "goodbye":
            import random
            responses_en = ["Goodbye! See you soon!", "Bye! Have a great day!", "See you later!"]
            responses_de = ["Tschuess! Bis bald!", "Auf Wiedersehen! Hab einen schoenen Tag!", "Bis spaeter!"]
            is_german = any(w in user_input.lower() for w in ["tschuess", "wiedersehen", "bis spaeter"])
            result = random.choice(responses_de if is_german else responses_en)
            self.mood_tool._set_mood("relaxed", 0.5)
            return {"goal": "Say goodbye", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "research_query":
            query = classification.get("query", user_input)
            # Extract search term
            import re as _re
            search_match = _re.search(r'(?:research|search|about|uber|weisst.*|kennst.*)(?:\s+(?:about|what|was|info|on))?\s+(.+)', query, re.IGNORECASE)
            search_term = search_match.group(1) if search_match else query
            result = self.research_tool._research(search_term)
            return {"goal": f"Research: {search_term[:50]}", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "memory_query":
            query = classification.get("query", user_input)
            result = self.memory.recall(query)
            return {"goal": f"Memory recall: {query[:50]}", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        if ctype == "vision_query":
            self.collect_inputs()
            objects = self.vision_tool._get_objects()
            faces = self.vision_tool._get_faces()
            result = f"Vision: {objects}\n{faces}"
            return {"goal": "Check vision", "task": None, "plan": result,
                    "tool_calls": [], "results": [result],
                    "mood": self.mood_tool.get_current(), "elapsed": 0}

        return None

    def _run_llm_cycle(self, user_input: str = "") -> Dict[str, Any]:
        """Full LLM-based agent cycle."""
        cycle_start = time.time()
        inputs = self.collect_inputs()
        if user_input:
            inputs["speech"] = user_input

        state = self.update_state(inputs)
        task = self.task_manager.get_next()
        goal = self.goal_system.resolve(self.mode, task)

        if task:
            self.state.set_active_task(task["id"])
        else:
            self.state.set_active_task(None)

        memory_context = self.memory.get_context_for_prompt()
        plan = self.llm.plan(
            system_prompt=self.system_prompt,
            user_prompt=f"Goal: {goal}\n\nState:\n{self.state.to_prompt_context()}\n\nMemory:\n{memory_context}\n\nUser input: {user_input}\n\nDecide what to do.",
            tools=self.tool_definitions,
        )

        results = []
        tool_calls = plan.get("tool_calls", [])

        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            args = tc.get("args", {})

            safety_msg = self.safety.validate(tc, self.state.get())
            if safety_msg:
                results.append(f"SAFETY: {safety_msg}")
                OutputFormatter.print_agent(f"[SAFETY] {safety_msg}")
                continue

            result = self._execute_single_tool(tool_name, args)
            results.append(f"{tool_name}: {result}")
            OutputFormatter.print_agent(f"[TOOL] {tool_name} -> {result}")
            self._apply_side_effects(tool_name, args, result)

        if task and results:
            self.task_manager.mark_completed(task["id"], "; ".join(results))

        self.memory.store_short("last_cycle", {
            "goal": goal,
            "tool_calls": len(tool_calls),
            "results_count": len(results),
            "timestamp": datetime.now().isoformat(),
        })

        if inputs.get("speech"):
            self.state.add_interaction(inputs["speech"])

        if plan.get("mood"):
            self.mood_tool._set_mood(
                plan["mood"].get("emotion", "neutral"),
                plan["mood"].get("intensity", 0.5),
            )

        elapsed = time.time() - cycle_start
        self._cycle_count += 1
        self._last_cycle_time = elapsed

        return {
            "goal": goal,
            "task": task["goal"] if task else None,
            "plan": plan.get("thought", ""),
            "tool_calls": tool_calls,
            "results": results,
            "mood": plan.get("mood", {}),
            "elapsed": elapsed,
        }

    def _execute_single_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        for tool in self.all_tools.values():
            for defn in tool.get_definitions():
                if defn["function"]["name"] == tool_name:
                    return tool.execute(tool_name, args)
        return f"Unknown tool: {tool_name}"

    def _apply_side_effects(self, tool_name: str, args: Dict[str, Any], result: str):
        if tool_name == "set_mood":
            emotion = args.get("emotion", "neutral")
            self.comm.send_mood(emotion)
            self.state.state["mood"] = {"emotion": emotion, "intensity": args.get("intensity", 0.5)}

        if tool_name == "speak":
            text = args.get("text", "")
            if text:
                OutputFormatter.print_agent(f"[SPEAK] {text}")

        if tool_name == "move":
            direction = args.get("direction", "stop")
            speed = args.get("speed", 50)
            if direction == "forward":
                self.comm.send_movement(speed, speed)
            elif direction == "backward":
                self.comm.send_movement(-speed, -speed)
            elif direction == "left":
                self.comm.send_movement(-speed, speed)
            elif direction == "right":
                self.comm.send_movement(speed, -speed)
            else:
                self.comm.send_movement(0, 0)

        if tool_name == "turn":
            angle = args.get("angle", 0)
            speed = 30
            if angle > 0:
                self.comm.send_movement(speed, -speed)
            else:
                self.comm.send_movement(-speed, speed)
            time.sleep(max(0.1, abs(angle) / 180.0))
            self.comm.send_movement(0, 0)

        if tool_name == "set_head":
            self.comm.send_head(args.get("rotate", 0), args.get("tilt", 0))

        if tool_name == "move_arm":
            self.comm.send_arm(args.get("side", "left"), args.get("position", 0))

    def _on_timer_due(self, task: Dict[str, Any]):
        OutputFormatter.print_banner(f"TIMER DUE: {task['goal']}")
        result = self._run_llm_cycle(f"Timer reminder: {task['goal']}")
        OutputFormatter.print_agent(f"Timer handled. Mood: {result['mood'].get('emotion', 'neutral')}")

    def run_cycle(self, user_input: str = "") -> Dict[str, Any]:
        """Main entry point. Fast-path for simple inputs, LLM for complex ones."""
        classification = InputClassifier.classify(user_input)
        fast_result = self._handle_fast_path(classification, user_input)
        if fast_result is not None:
            return fast_result
        return self._run_llm_cycle(user_input)

    def set_mode(self, mode: str) -> str:
        valid = list(config.MODES.keys())
        if mode not in valid:
            return f"Invalid mode. Use: {valid}"

        self.mode = mode
        self.state.state["mode"] = mode
        self.task_manager.clear_mode_tasks()

        mode_goal = config.MODES[mode]["description"]
        self.task_manager.add_mode_mission(mode, mode_goal)

        self.system_prompt = self._build_system_prompt()
        OutputFormatter.print_agent(f"Mode changed to {mode}")
        return f"Mode changed to {mode}"

    def add_command(self, command: str) -> str:
        self.task_manager.add_user_command(command)
        return f"Command queued: {command}"

    def add_timer(self, goal: str, minutes: int) -> str:
        task_id = self.task_manager.add_timer(goal, minutes)
        return f"Timer set: {goal} in {minutes} minutes (ID: {task_id[:8]})"

    def start_loop(self):
        self.running = True
        self._timer_daemon.start()
        self._loop_thread = threading.Thread(target=self._main_loop, daemon=True, name="AgentLoop")
        self._loop_thread.start()
        OutputFormatter.print_agent("Agent loop started")

    def stop_loop(self):
        self.running = False
        self._timer_daemon.stop()
        if self._loop_thread:
            self._loop_thread.join(timeout=5)
        self.comm.disconnect()
        OutputFormatter.print_agent("Agent loop stopped")

    def _main_loop(self):
        hb_map = {
            "Idle": config.HEARTBEAT_IDLE,
            "Play": config.HEARTBEAT_PLAY,
            "Assist": config.HEARTBEAT_ASSIST,
            "Explore": config.HEARTBEAT_EXPLORE,
            "Auto": config.HEARTBEAT_AUTO,
        }
        heartbeat = hb_map.get(self.mode)
        if heartbeat is None:
            heartbeat = 60

        OutputFormatter.print_agent(f"Main loop running. Heartbeat: {heartbeat}s")

        while self.running:
            try:
                result = self.run_cycle("")
                pending = len(self.task_manager.get_pending())
                OutputFormatter.print_status(self.mode, result['mood'].get('emotion', 'neutral'), pending)
            except Exception as e:
                OutputFormatter.print_agent(f"[ERROR] Agent cycle: {e}")
            time.sleep(config.LOOP_DELAY)

    def run_interactive(self):
        self.running = True

        OutputFormatter.print_banner(f"Robot Agent - Mode: {self.mode}")
        OutputFormatter.print_agent("Commands: quit | mode <name> | task <goal> | timer <goal> <min>")
        OutputFormatter.print_agent("Type anything to give a direct command.\n")

        hb_map = {
            "Idle": config.HEARTBEAT_IDLE,
            "Play": config.HEARTBEAT_PLAY,
            "Assist": config.HEARTBEAT_ASSIST,
            "Explore": config.HEARTBEAT_EXPLORE,
            "Auto": config.HEARTBEAT_AUTO,
        }
        heartbeat = hb_map.get(self.mode)
        if heartbeat:
            self.start_loop()

        try:
            while self.running:
                try:
                    user_input = OutputFormatter.prompt().strip()
                except (EOFError, KeyboardInterrupt):
                    break

                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    break

                result = self.run_cycle(user_input)

                OutputFormatter.print_banner("Response")
                OutputFormatter.print_agent(f"Goal: {result['goal']}")
                if result["plan"]:
                    OutputFormatter.print_agent(f"Response: {result['plan'][:300]}")
                if result["results"]:
                    OutputFormatter.print_agent("Actions:")
                    for r in result["results"]:
                        OutputFormatter.print_agent(f"  - {r}")
                OutputFormatter.print_agent(f"Mood: {result['mood'].get('emotion', 'neutral')}")
                OutputFormatter.print_agent(f"Time: {result.get('elapsed', 0):.1f}s")
                OutputFormatter.print_agent("")

        except KeyboardInterrupt:
            pass
        finally:
            self.stop_loop()
