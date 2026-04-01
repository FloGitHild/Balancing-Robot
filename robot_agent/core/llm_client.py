import json
import re
import requests
from typing import Dict, Any, List, Optional
import robot_agent.config as config


class LLMClient:
    """Ollama LLM client optimized for speed (<5s) and anti-hallucination."""

    def __init__(self, model: str = None, base_url: str = "http://localhost:11434"):
        self.model = model or config.LLM_MODEL
        self.base_url = base_url
        self.session = requests.Session()
        self._check_connection()

    def _check_connection(self):
        try:
            resp = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                available = [m["name"] for m in resp.json().get("models", [])]
                print(f"Ollama connected. Models: {available}")
                if self.model not in available:
                    print(f"Warning: Model '{self.model}' not found. Using first available.")
                    self.model = available[0] if available else "llama3.2"
            else:
                print(f"Warning: Ollama returned status {resp.status_code}")
        except Exception as e:
            print(f"Cannot connect to Ollama: {e}")

    def plan(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "tools": tools,
            "options": {
                "num_ctx": config.LLM_CONTEXT_WINDOW,
                "num_predict": config.LLM_MAX_TOKENS,
                "temperature": config.LLM_TEMPERATURE,
                "num_gpu": config.LLM_NUM_GPU,
                "threads": config.LLM_THREADS,
                "repeat_penalty": 1.1,
                "top_k": 40,
                "top_p": 0.9,
            },
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=config.LLM_TIMEOUT,
            )
            if resp.status_code != 200:
                return self._fallback_response("LLM error: " + resp.text)

            result = resp.json()
            msg = result.get("message", {})
            return self._parse_llm_output(msg)

        except requests.Timeout:
            return self._fallback_response("LLM timeout")
        except Exception as e:
            return self._fallback_response(f"LLM error: {e}")

    def _parse_llm_output(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])

        parsed_tools = []
        for tc in tool_calls:
            parsed = self._parse_tool_call(tc)
            if parsed:
                parsed_tools.append(parsed)

        parsed_tools = parsed_tools[:config.LLM_MAX_TOOL_CALLS_PER_TURN]

        mood = self._extract_mood(content)
        thought = content.strip()[:300] if content else ""

        return {
            "thought": thought,
            "tool_calls": parsed_tools,
            "response_text": "",
            "mood": mood,
        }

    def _parse_tool_call(self, tc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            func = tc.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", {})

            if isinstance(args, str):
                args = json.loads(args)

            if not name:
                return None

            allowed_tools = {
                "move", "turn", "set_head", "move_arm", "stop",
                "get_visible_objects", "get_visible_faces",
                "speak", "play_audio", "audio_search", "audio_play_category",
                "set_mood",
                "create_task", "list_tasks", "complete_task",
                "remember", "recall",
                "research", "read_local_file", "get_current_time", "get_weather", "get_fun_fact",
            }
            if name not in allowed_tools:
                return None

            return {"tool": name, "args": args}
        except (json.JSONDecodeError, KeyError):
            return None

    def _extract_mood(self, content: str) -> Dict[str, Any]:
        valid_emotions = ["happy", "sad", "thinking", "excited", "curious", "neutral", "surprised", "relaxed"]

        content_lower = content.lower()
        for emotion in valid_emotions:
            if emotion in content_lower:
                return {"emotion": emotion, "intensity": 0.6}

        return {"emotion": "neutral", "intensity": 0.5}

    def _fallback_response(self, error: str) -> Dict[str, Any]:
        return {
            "thought": error,
            "tool_calls": [],
            "response_text": "I encountered an error processing your request.",
            "mood": {"emotion": "neutral", "intensity": 0.5},
        }

    def respond_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": config.LLM_CONTEXT_WINDOW,
                "num_predict": config.LLM_MAX_TOKENS,
                "temperature": config.LLM_TEMPERATURE,
                "num_gpu": config.LLM_NUM_GPU,
                "threads": config.LLM_THREADS,
            },
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=config.LLM_TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "").strip()
            return "Error getting response."
        except Exception as e:
            return f"Error: {e}"
