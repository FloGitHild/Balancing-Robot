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
LLM_MODEL = "llama3.2:1b"       # Model to use (run 'ollama list' to see available)
LLM_TIMEOUT = 180               # Timeout in seconds for LLM responses
LLM_MAX_TOKENS = 256            # Max tokens in response
LLM_CONTEXT_WINDOW = 4096       # Context window size
LLM_TEMPERATURE = 0.7           # Creativity (0.0-1.0, higher = more creative)
LLM_NUM_GPU = 0                 # GPU layers (0 = CPU only)
LLM_THREADS = 4                 # CPU threads for inference

# ==============================================================================
# AGENT BEHAVIOR SETTINGS
# ==============================================================================
AGENT_MAX_ITERATIONS = 3        # Max tool call loops per request (prevents infinite loops)
AGENT_MAX_TOOL_CALLS = 2        # Max tools per single LLM call
AGENT_VISION_UPDATE_EACH_ITER = True  # Request fresh vision after each tool

# ==============================================================================
# MODE-SPECIFIC HEARTBEAT (time between auto-actions in seconds)
# ==============================================================================
# None = no automatic actions, just wait for user input
# 0 = continuous loop, 30 = every 30 seconds, 60 = every minute, etc.
HEARTBEAT_IDLE = None           # Idle: wait for user
HEARTBEAT_PLAY = 120            # Play: every 2 minutes
HEARTBEAT_ASSIST = 120          # Assist: every 2 minutes
HEARTBEAT_EXPLORE = 60          # Explore: every 1 minute
HEARTBEAT_AUTO = 30             # Auto: every 30 seconds

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
VISION_SHOW_WINDOW = True      # Show detection window (slower, for debugging)

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