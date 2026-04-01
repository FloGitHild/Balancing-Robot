# Robot Agent - Task-Based Autonomous System
# ==============================================================================

# ==============================================================================
# STARTUP
# ==============================================================================
DEFAULT_MODE = "Idle"

# ==============================================================================
# LLM
# ==============================================================================
LLM_MODEL = "llama3.2:latest"
LLM_TIMEOUT = 180
LLM_MAX_TOKENS = 256
LLM_CONTEXT_WINDOW = 4096
LLM_TEMPERATURE = 0.2
LLM_NUM_GPU = -1
LLM_THREADS = 12

# Anti-hallucination
LLM_FORCE_JSON = True
LLM_MAX_TOOL_CALLS_PER_TURN = 3
LLM_MAX_TURNS = 5

# ==============================================================================
# AGENT LOOP
# ==============================================================================
LOOP_DELAY = 1.0
AGENT_MAX_ITERATIONS = 10

# ==============================================================================
# MODE HEARTBEAT (seconds between auto-cycles)
# ==============================================================================
HEARTBEAT_IDLE = None
HEARTBEAT_PLAY = 30
HEARTBEAT_ASSIST = 60
HEARTBEAT_EXPLORE = 15
HEARTBEAT_AUTO = 20

# ==============================================================================
# TTS
# ==============================================================================
TTS_MAX_CHARS = 300
TTS_RATE = "+30%"
TTS_PITCH = "+50Hz"
TTS_VOICE_DE = "de-DE-KatjaNeural"
TTS_VOICE_EN = "en-US-JennyNeural"

# ==============================================================================
# VISION
# ==============================================================================
VISION_DETECTION_INTERVAL = 0.5
VISION_FACE_TOLERANCE = 0.6
VISION_OBJECT_CONFIDENCE = 0.6
VISION_SHOW_WINDOW = False

# ==============================================================================
# TOOLS ENABLE/DISABLE
# ==============================================================================
TOOLS_ENABLED = {
    "movement": True,
    "vision": True,
    "audio": True,
    "mood": True,
    "memory": True,
    "tasks": True,
    "research": True,
}

# ==============================================================================
# ROBOT CONNECTION
# ==============================================================================
ROBOT_URL = "http://localhost:5000"

# ==============================================================================
# MODE DESCRIPTIONS
# ==============================================================================
MODES = {
    "Idle": {"description": "Wait for triggers, no automatic actions", "goal": "observe"},
    "Play": {"description": "Search for people, play games, make jokes", "goal": "interact"},
    "Assist": {"description": "Ask to help, make notes, set timers, research", "goal": "help"},
    "Explore": {"description": "Drive around, search for new things, build gallery", "goal": "discover"},
    "Auto": {"description": "Free decisions, experimental behavior", "goal": "decide"},
}

# ==============================================================================
# DEBUG
# ==============================================================================
DEBUG_SHOW_PROMPTS = True
DEBUG_SHOW_TOOL_RESULTS = True
DEBUG_VERBOSE = False
