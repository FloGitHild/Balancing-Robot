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

### 5. Memory System

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

### 6. Vision System

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
