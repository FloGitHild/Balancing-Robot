# ==============================================================================
# AGENT CONFIGURATION FILE
# ==============================================================================
# Edit these values to customize agent behavior. Changes take effect on next start.
# ==============================================================================

# ==============================================================================
# STARTUP SETTINGS
# ==============================================================================
DEFAULT_MODE = "Idle"          # Mode on startup: Idle, Play, Assist, Explore, Auto

# ==============================================================================
# LLM (Language Model) SETTINGS
# ==============================================================================
# GPU Settings for NVIDIA RTX 4050 (6GB VRAM)
LLM_MODEL = "llama3.2:latest"       # Model to use (1B params = fast, works with 6GB GPU)
LLM_TIMEOUT = 180               # Timeout in seconds for LLM responses
LLM_MAX_TOKENS = 512            # Max tokens in response
LLM_CONTEXT_WINDOW = 4096       # Context window size
LLM_TEMPERATURE = 0.7           # Creativity (0.0-1.0)
LLM_NUM_GPU = -1                # GPU layers: -1 = all layers (use GPU!) 0 = CPU only
LLM_THREADS = 12                 # CPU threads (half of 16 available)

# ==============================================================================
# AGENT BEHAVIOR SETTINGS
# ==============================================================================
AGENT_MAX_ITERATIONS = 10        # Max tool call loops per request (prevents infinite loops)
AGENT_MAX_TOOL_CALLS = 10        # Max tools per single LLM call
AGENT_VISION_UPDATE_EACH_ITER = True  # Request fresh vision after each tool

# ==============================================================================
# MODE-SPECIFIC HEARTBEAT (time between auto-actions in seconds)
# ==============================================================================
# None = no automatic actions, just wait for user input
# 0 = continuous loop, 30 = every 30 seconds, 60 = every minute, etc.
HEARTBEAT_IDLE = None           # Idle: wait for user (no automatic actions)
HEARTBEAT_PLAY = 30            # Play: every 30 seconds
HEARTBEAT_ASSIST = 30          # Assist: every 30 seconds
HEARTBEAT_EXPLORE = 20         # Explore: every 20 seconds
HEARTBEAT_AUTO = 10            # Auto: every 10 seconds (fast loop)

# ==============================================================================
# TTS (Text-to-Speech) SETTINGS
# ==============================================================================
TTS_MAX_CHARS = 300             # Max characters to speak (longer = truncated)
TTS_RATE = "+30%"               # Speech speed: "+0%" = normal, "+30%" = faster, "-20%" = slower
TTS_PITCH = "+50Hz"             # Pitch: "+0Hz" = normal, "+50Hz" = higher, "-20Hz" = lower
TTS_VOICE_DE = "de-DE-KatjaNeural"   # German voice
TTS_VOICE_EN = "en-US-JennyNeural"   # English voice

# ==============================================================================
# VISION SETTINGS
# ==============================================================================
VISION_DETECTION_INTERVAL = 0.5 # Seconds between detection runs
VISION_FACE_TOLERANCE = 0.6     # Face recognition tolerance (lower = stricter, 0.4-0.6 recommended)
VISION_OBJECT_CONFIDENCE = 0.6  # Object detection confidence threshold (0.0-1.0)
VISION_SHOW_WINDOW = False      # Show detection window (slower, for debugging)

# ==============================================================================
# TOOLS - ENABLE/DISABLE
# ==============================================================================
TOOLS_ENABLED = {
    "research": True,           # Wikipedia, search, weather
    "vision": True,            # Object/face detection
    "memory": True,            # Remember/recall interactions
    "scheduler": True,         # Timers, scheduled tasks
    "movement": True,          # move, speed, head, arm
    "mood": True,              # Mood detection
    "audio_input": True,       # Voice transcription
    "audio_output": True,      # Audio playback
}

# ==============================================================================
# ROBOT CONNECTION
# ==============================================================================
ROBOT_URL = "http://localhost:5000"    # Robot web server URL

# ==============================================================================
# DEBUG SETTINGS
# ==============================================================================
DEBUG_SHOW_PROMPTS = True      # Show prompts sent to LLM
DEBUG_SHOW_TOOL_RESULTS = True # Show tool execution results
DEBUG_VERBOSE = False          # Extra verbose logging

# ==============================================================================
# MODE DESCRIPTIONS (for system prompt)
# ==============================================================================
MODES = {
    "Idle": {"description": "Wait for faces to talk to, no automatic actions"},
    "Play": {"description": "Search for people, play games, make jokes"},
    "Assist": {"description": "Ask to help, make notes, set timers, research"},
    "Explore": {"description": "Drive around, search for new things"},
    "Auto": {"description": "Free decisions, experimental behavior"}
}