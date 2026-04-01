from typing import Dict, Any, List


class MemoryTool:
    """Tools for storing and recalling memories."""

    def __init__(self, memory_system):
        self.mem = memory_system

    def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "remember":
            return self.mem.remember(
                key=args.get("key", ""),
                value=args.get("value", ""),
            )
        elif tool_name == "recall":
            return self.mem.recall(args.get("query", ""))
        return f"Unknown memory tool: {tool_name}"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "remember",
                    "description": "Store a fact in long-term memory. Use key-value pairs. Example: key='Florian_preference', value='likes robotics'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Memory key (e.g. 'person_name_fact', 'preference_topic')"},
                            "value": {"type": "string", "description": "The fact or information to remember"},
                        },
                        "required": ["key", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recall",
                    "description": "Search memory for information matching a query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "What to search for in memory"},
                        },
                        "required": ["query"],
                    },
                },
            },
        ]
