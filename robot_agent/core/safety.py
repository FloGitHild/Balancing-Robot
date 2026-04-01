from typing import Dict, Any, Optional


class SafetyLayer:
    """Validates all actions before execution to prevent unsafe behavior."""

    def __init__(self, min_distance_cm: float = 30.0, max_speed: int = 80):
        self.min_distance_cm = min_distance_cm
        self.max_speed = max_speed

    def validate(self, action: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
        tool = action.get("tool", "")
        args = action.get("args", {})

        if tool in ("move", "turn"):
            return self._validate_movement(action, state)
        elif tool == "speed":
            return self._validate_speed(action, state)
        elif tool in ("set_head", "move_arm"):
            return self._validate_servo(action, state)

        return None

    def _to_number(self, val, default=0):
        """Safely convert to number."""
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def _validate_movement(self, action: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
        distance = state.get("environment", {}).get("distance_cm", 999)
        direction = action.get("args", {}).get("direction", "")

        if direction == "forward" and distance < self.min_distance_cm:
            return f"BLOCKED: Cannot move forward. Distance is {distance:.0f}cm (min: {self.min_distance_cm:.0f}cm)"

        args = action.get("args", {})
        speed = self._to_number(args.get("speed", 50), 50)
        if speed > self.max_speed:
            return f"CLAMPED: Speed reduced from {speed:.0f} to {self.max_speed}"

        return None

    def _validate_speed(self, action: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
        speed = self._to_number(action.get("args", {}).get("value", 50), 50)
        if speed > self.max_speed:
            return f"CLAMPED: Speed reduced from {speed:.0f} to {self.max_speed}"
        if speed < 0:
            return "BLOCKED: Speed cannot be negative"
        return None

    def _validate_servo(self, action: Dict[str, Any], state: Dict[str, Any]) -> Optional[str]:
        args = action.get("args", {})
        for key in ("rotate", "tilt", "position", "h", "v"):
            val = self._to_number(args.get(key), None)
            if val is not None and not (-90 <= val <= 90):
                return f"CLAMPED: {key} value {val:.0f} clamped to valid range [-90, 90]"
        return None
