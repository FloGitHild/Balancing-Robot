# Robot Agent Documentation

## Overview

This agent is an AI-powered system that controls a balancing robot (ESP32P4). It uses a Large Language Model (LLM) via Ollama to make decisions and interact with people naturally.

## How Agents Work

### Basic Concept

An agent is like a loop that:
1. **Perceives** - Gets information from the world (vision, audio, state)
2. **Thinks** - Uses an LLM to decide what to do
3. **Acts** - Uses tools to control the robot or interact with the world
4. **Repeats** - Runs forever in a loop

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT LOOP                           │
│                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│   │ Perceive │ -> │  Think  │ -> │   Act   │          │
│   └─────────┘    └─────────┘    └─────────┘          │
│       ^                                      │         │
│       └────────────── FEEDBACK ──────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### In This Agent

```
User Input ──┐
             │
Vision Data ──┼──> LLM (Ollama) ──> Decision ──> Tools ──> Robot
             │        │                                    │
Audio Data ──┘        │                                    │
                     v                                    │
              System Prompt                               │
              (defines role) ────────────────────────────┘
```

## Architecture

### 1. Core Components

```
Agent/
├── agent.py         # Main loop - the "brain"
├── llm.py          # Ollama wrapper (talks to LLM)
├── memory.py       # Remembers tasks & interactions
├── vision_for_agent.py  # Vision system
└── tools/           # Individual tools
    ├── movements.py     # Move robot
    ├── research.py      # Search internet
    ├── tasks.py        # Manage todo lists
    ├── mood.py         # Set robot mood
    ├── vision.py      # Get vision info
    ├── audio_input.py  # Listen to people
    └── audio_output.py # Speak to people
```

### 2. The Agent Loop (agent.py)

```python
# Simplified version of the main loop
while running:
    # 1. Get user input
    user_input = input("You: ")
    
    # 2. Gather context (vision, audio, state)
    vision_info = vision.get_summary()
    
    # 3. Build messages for LLM
    messages = [
        {"role": "system", "content": system_prompt},  # "You are a robot..."
        {"role": "user", "content": user_input},       # "Who am I?"
        {"role": "user", "content": f"Vision: {vision_info}"}
    ]
    
    # 4. Send to LLM with tools
    response = llm.chat(messages, tools=tools)
    
    # 5. If LLM wants to use a tool, execute it
    if response.has_tool_calls():
        result = execute_tool(tool_name, arguments)
        # Send result back to LLM for final answer
        response = llm.chat(more_messages)
    
    # 6. Print response
    print(f"Bot: {response}")
```

### 3. System Prompt

The system prompt tells the LLM WHO it is and WHAT it can do:

```
You are an AI agent controlling a balancing robot with the ESP32P4.

Current State:
- Mode: Idle
- Mood: neutral

Robot Capabilities:
- 2-wheeled balancing robot with arms and grippers
- Camera for vision (objects and faces)
- Speaker for audio output
- Microphone for audio input

Your goal is to interact naturally with people based on the current mode.

Available modes:
- Play: Search for people, play, make jokes
- Assist: Help people, make notes, set timers
- Explore: Drive around, discover new things
- Auto: Free to make your own decisions
- Idle: Wait for tasks, listen and look for people

Use tools appropriately...
```

### 4. Tools (Function Calling)

Tools let the LLM control the robot. Each tool has:
- **Name** - What it's called
- **Description** - When to use it (LLM reads this!)
- **Parameters** - What inputs it needs

Example from movements.py:

```python
{
    "type": "function",
    "function": {
        "name": "move",
        "description": "Control the direction the Robot is moving",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["forward", "backward", "left", "right", "stop"],
                    "description": "The direction to move"
                }
            },
            "required": ["direction"]
        }
    }
}
```

When the LLM calls a tool, the agent executes it and returns the result:

```
LLM: "I should move forward to greet the person"
     -> calls move(direction="forward")
Agent: executes movements.move("forward")
        returns "Moving forward"
LLM: "Hello! I'm coming to say hi!"
```

### Available Tools

Each tool is a separate file in the `tools/` folder. Here's what each one can do:

---

#### 1. Movements (`tools/movements.py`)

Controls the robot's physical movement.

| Tool | Description | Parameters |
|------|-------------|------------|
| `move` | Control movement direction | `direction`: forward, backward, left, right, stop |
| `speed` | Set movement speed (0-100) | `value`: 0-100 |
| `head` | Control head position | `rotate`: -90 to 90, `tilt`: -90 to 90 |
| `arm` | Control arm position | `side`: left/right, `h`: horizontal -90 to 90, `v`: vertical -90 to 90 |

**Example usage:**
```
move(direction="forward")    → "Moving forward"
speed(value=50)              → "Speed set to 50"
head(rotate=20, tilt=10)     → "Head set - rotate: 20, tilt: 10"
arm(side="left", h=30, v=45) → "Left arm set - h: 30, v: 45"
```

---

#### 2. Research (`tools/research.py`)

Search the internet for information.

| Tool | Description | Parameters |
|------|-------------|------------|
| `research_search` | Search the web | `query`: search string |
| `research_wikipedia` | Get Wikipedia summary | `topic`: article name |
| `research_weather` | Get weather info | `location`: city name |

**Example usage:**
```
research_search(query="Python programming")  → "Search completed for: Python..."
research_wikipedia(topic="Berlin")          → "📖 Berlin\nBerlin is the capital..."
research_weather(location="Berlin")          → "Weather for Berlin: ..."
```

---

#### 3. Tasks (`tools/tasks.py`)

Manage todo lists and reminders.

| Tool | Description | Parameters |
|------|-------------|------------|
| `tasks_add_global` | Add global task/timer | `task`: description, `due`: optional datetime, `priority`: low/normal/high |
| `tasks_add_mode` | Add mode-specific task | `mode`: Play/Assist/Explore/Auto/Idle, `task`: description |
| `tasks_list_global` | List all global tasks | (none) |
| `tasks_list_mode` | List tasks for mode | `mode`: mode name |
| `tasks_complete_global` | Mark global task done | `task_id`: task ID |
| `tasks_complete_mode` | Mark mode task done | `mode`: mode name, `task_id`: task ID |

**Example usage:**
```
tasks_add_global(task="Call mom at 5pm", due="17:00", priority="high")
tasks_add_mode(mode="Play", task="Find a ball")
tasks_list_global()       → "Global Tasks: ○ [1] Call mom..."
tasks_complete_global(task_id=1)  → "Completed: Call mom at 5pm"
```

---

#### 4. Mood (`tools/mood.py`)

Set the robot's mood (affects LEDs and expressions).

| Mood | LED Color | Description |
|------|-----------|-------------|
| neutral | Green | Default state |
| happy | Cyan | Happy and playful |
| sad | Blue | Sad or empathetic |
| curious | Yellow | Curious or interested |
| excited | Magenta | Excited or enthusiastic |
| thinking | Purple | Thinking or processing |
| surprised | Orange | Surprised or amazed |
| scared | Red | Scared or cautious |
| angry | Red | Angry or frustrated |
| relaxed | Light Blue | Relaxed or calm |

| Tool | Description | Parameters |
|------|-------------|------------|
| `mood_set` | Set robot mood | `mood`: one of the moods above |
| `mood_get_current` | Get current mood info | (none) |
| `mood_get_history` | Get mood change history | `limit`: number of entries |

**Example usage:**
```
mood_set(mood="happy")     → "Mood changed from neutral to happy 😄"
mood_get_current()        → "{'mood': 'happy', 'emoji': '😄', 'led_color': [0, 255, 255]}"
mood_get_history()        → "Mood History: neutral → happy at 2024-01-01T12:00:00"
```

---

#### 5. Vision (`tools/vision.py`)

Get information about what the robot sees.

| Tool | Description | Parameters |
|------|-------------|------------|
| `vision_get_objects` | List detected objects with positions | (none) |
| `vision_get_faces` | List detected faces with names | (none) |
| `vision_get_summary` | Quick summary for LLM | (none) |

**Example usage:**
```
vision_get_objects()  → "Detected Objects:
  - cup: 30%-50% width, 40%-60% height (90% conf)
  - person: 20%-40% width, 10%-50% height (95% conf)"

vision_get_faces()    → "Detected Faces:
  - John: box[100, 50, 200, 150]"

vision_get_summary() → "Objects: 2, Faces: 1, Known people: John"
```

---

### 6. Audio Input (`tools/audio_input.py`)

Listen to and transcribe speech.

| Tool | Description | Parameters |
|------|-------------|------------|
| `audio_input_get_transcriptions` | Get recent transcriptions | `limit`: number of entries |
| `audio_input_is_listening` | Check if listening | (none) |

**Example usage:**
```
audio_input_get_transcriptions(limit=5)  → "Recent Transcriptions:
  - [12:30:15] Hello robot
  - [12:30:45] How are you?"

audio_input_is_listening()  → "True"
```

---

### 7. Audio Output (`tools/audio_output.py`)

Play audio or generate speech.

| Tool | Description | Parameters |
|------|-------------|------------|
| `audio_output_play_file` | Play audio file | `filepath`: path to .wav/.mp3 |
| `audio_output_play_tts` | Generate and play TTS | `text`: text to speak, `voice`: voice name |
| `audio_output_queue` | Queue audio for later | `filepath`: path to audio file |
| `audio_output_get_queue` | Show queue status | (none) |
| `audio_output_stop` | Stop playback | (none) |

**Example usage:**
```
audio_output_play_file(filepath="data/audio/greeting.wav")  → "Playing: greeting.wav"
audio_output_play_tts(text="Hello! I am your robot assistant!")  → "TTS: Hello!..."
audio_output_get_queue()  → "Queue: 1. greeting.wav"
audio_output_stop()      → "Stopped"
```

---

### 8. Memory (`tools/memory.py`)

Remember interactions with specific people.

| Tool | Description | Parameters |
|------|-------------|------------|
| `memory_remember` | Remember something about current person | `what`: what to remember |
| `memory_recall` | Recall previous interactions | `person`: name, `limit`: number |
| `memory_get_people` | Get list of known people | (none) |

**Example usage:**
```
memory_remember(what="Likes cats")     → "Added interaction with John: Likes cats"
memory_recall(person="John", limit=3) → "Interactions with John:
  - [2024-01-01T12:00] Likes cats"
memory_get_people()  → "['John', 'Alice']"
```
audio_input_get_transcriptions(limit=5)  → "Recent Transcriptions:
  - [12:30:15] Hello robot
  - [12:30:45] How are you?"

audio_input_is_listening()  → "True"
```

---

#### 7. Audio Output (`tools/audio_output.py`)

Play audio or generate speech.

| Tool | Description | Parameters |
|------|-------------|------------|
| `audio_output_play_file` | Play audio file | `filepath`: path to .wav/.mp3 |
| `audio_output_play_tts` | Generate and play TTS | `text`: text to speak, `voice`: voice name |
| `audio_output_queue` | Queue audio for later | `filepath`: path to audio file |
| `audio_output_get_queue` | Show queue status | (none) |
| `audio_output_stop` | Stop playback | (none) |

**Example usage:**
```
audio_output_play_file(filepath="data/audio/greeting.wav")  → "Playing: greeting.wav"
audio_output_play_tts(text="Hello! I am your robot assistant!")  → "TTS: Hello!..."
audio_output_get_queue()  → "Queue: 1. greeting.wav"
audio_output_stop()      → "Stopped"
```

---

### 6. Memory System

The agent has memory to remember things:

```python
memory:
├── short_term:    # Current tasks (immediate)
│   - "Check if person needs help"
│   - "Wave to the person"
├── long_term:     # Goals (persistent)
│   - "Learn to play a new game"
│   - "Remember John's birthday"
└── interactions:  # Per person (who said what)
    "John": [      # Conversations with John
        {"summary": "Taught me a joke", "mood": "happy"},
        {"summary": "Asked about the weather", "mood": "neutral"}
    ]
```

### 7. Vision System

The vision system provides what the robot sees:

```
┌──────────────────────────────────────────┐
│           Camera Frame                   │
│  ┌─────────┐           ┌─────────────┐  │
│  │  Face   │           │    Cup      │  │
│  │ [John]  │           │             │  │
│  └─────────┘           └─────────────┘  │
│                                          │
│  Output to Agent:                        │
│  - Objects: cup (30%-50% width)          │
│  - Faces: John (left side)               │
└──────────────────────────────────────────┘
```

## Data Flow

### Full Example: "Hello, who am I?"

```
1. User types: "Hello, who am I?"

2. Agent gathers context:
   - Vision: "Objects: 1, Faces: 1, Known people: John"
   - Mode: "Idle"
   - Memory: "Met John yesterday"

3. Build prompt:
   System: "You are a robot..."
   User:   "Hello, who am I?"
   Context: "Vision: Objects: 1, Faces: 1..."

4. Send to Ollama:
   Ollama: "The user appears to be John based on face recognition"

5. Execute any tools needed:
   (None needed for this question)

6. Return response:
   "Hello John! Nice to see you again!"
```

### Full Example: "Move forward"

```
1. User types: "Move forward and say hello"

2. Agent gathers context

3. Send to Ollama:
   Ollama: I'll move forward and greet
   tool_calls: [{"function": {"name": "move", "arguments": {"direction": "forward"}}}]

4. Execute tool:
   movements.move("forward") → "Moving forward"

5. Send result back to Ollama:
   "Now I should say hello with audio"

6. More tools:
   tool_calls: [{"function": {"name": "audio_output_play_tts", "arguments": {"text": "Hello!"}}}]

7. Execute and finish:
   audio_output.play_tts("Hello!") → "Playing: Hello!"

8. Final response:
   "I've moved forward and said hello!"
```

## Modes

The agent operates in different modes that change its behavior:

| Mode | Description | Behavior |
|------|-------------|----------|
| **Play** | Search for people, play | Makes jokes, finds toys |
| **Assist** | Help people | Takes notes, sets timers |
| **Explore** | Discover things | Drives around, catalogs |
| **Auto** | Experimental | Free will |
| **Idle** | Waiting | Listens, looks for people |

## Getting Started

### Prerequisites

```bash
# Install dependencies
pip install flask flask-socketio python-socketio opencv-python
pip install ultralytics face-recognition
pip install requests sounddevice soundfile

# Start Ollama (separate terminal)
ollama serve
ollama pull llama3.2
```

### Running the System

```bash
# Terminal 1: Start Robot Simulator
cd Balancing_Robot
python "ESP32P4/ESP32P4 Simulator.py"

# Terminal 2: Start Vision
cd Balancing_Robot/Agent
python vision_for_agent.py

# Terminal 3: Start Agent
cd Balancing_Robot/Agent
python agent.py
```

### Usage

```
🤖 Agent running in Idle mode
Type 'quit' to exit, 'mode <name>' to change mode

You: who am I?
🤖 Bot: Based on the vision system, you appear to be...

You: mode play
🤖 Mode changed to Play

You: quit
👋 Agent stopped
```

## Extending the Agent

### Adding a New Tool

1. Create a new file in `tools/`
2. Implement your tool class with:
   - `your_method()` - What the tool does
   - `get_tools()` - Returns tool definition for LLM
3. Import and add to `agent.py`

Example structure:

```python
# tools/my_new_tool.py
class MyNewTool:
    def __init__(self):
        self.setting = "default"
    
    def do_something(self, param: str) -> str:
        """Do something useful"""
        return f"Did something with: {param}"
    
    def get_tools(self) -> list:
        return [{
            "type": "function",
            "function": {
                "name": "do_something",
                "description": "Does something useful",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param": {"type": "string"}
                    },
                    "required": ["param"]
                }
            }
        }]
```

### Changing the LLM

Edit `llm.py` to use a different model:

```python
llm = OllamaLLM(model="llama3.2")  # Change to other model
# or
llm = OllamaLLM(model="mistral")
# or
llm = OllamaLLM(base_url="http://other-server:11434")  # Different server
```

## Troubleshooting

### Ollama not running
```
❌ LLM request failed: Connection refused
```
**Fix:** Start Ollama with `ollama serve`

### No camera
```
❌ Stream konnte nicht geöffnet werden
```
**Fix:** Check camera is connected and not used by another app

### Slow performance
**Fix:** Set `NO_STREAM = True` in simulator or `SHOW_WINDOW = False` in vision

## License

MIT License
