# Agent Configuration - Mode-specific settings

# Default mode on startup
DEFAULT_MODE = "Idle"

# Mode configurations: heartbeat_interval_seconds (0 = continuous loop)
MODES = {
    "Idle": {
        "heartbeat_interval": None,  # No automatic missions - just wait for user input
        "description": "Wait for faces to talk to, no automatic actions"
    },
    "Play": {
        "heartbeat_interval": 120,  # 2 minutes
        "description": "Search for people, play games, make jokes"
    },
    "Assist": {
        "heartbeat_interval": 120,  # 2 minutes
        "description": "Ask to help, make notes, set timers, research"
    },
    "Explore": {
        "heartbeat_interval": 60,   # 1 minute
        "description": "Drive around, search for new things"
    },
    "Auto": {
        "heartbeat_interval": 30,   # 30 seconds - continuous
        "description": "Free decisions, experimental behavior"
    }
}

# LLM settings
LLM_CONFIG = {
    "default_model": "llama3.2:1b",  # Fast model
    "fallback_model": "qwen3.5:latest",
    "timeout": 180,
    "max_tokens": 256,
    "context_window": 4096,
    "temperature": 0.7
}

# Vision settings
VISION_CONFIG = {
    "detection_interval": 0.5,
    "face_tolerance": 0.6,
    "object_confidence": 0.6
}

# TTS settings
TTS_CONFIG = {
    "max_chars": 300,
    "rate": "+30%",
    "pitch": "+50Hz"
}

# Agent iteration settings
AGENT_CONFIG = {
    "max_iterations": 5,  # Reduced from 10 to prevent infinite loops
    "vision_update_each_iteration": True
}