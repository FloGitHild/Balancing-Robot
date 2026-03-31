import os
import sys
import json
import time
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm import OllamaLLM
from memory import Memory
from tools.movements import Movements
from tools.research import Research
from tools.tasks import Tasks
from tools.mood import Mood
from tools.vision import Vision
from tools.audio_input import AudioInput
from tools.audio_output import AudioOutput

class Agent:
    def __init__(self, 
                 model: str = "llama3.2",
                 mode: str = "Idle",
                 robot_url: str = "http://localhost:5000"):
        print("🚀 Initializing Agent...")
        
        self.mode = mode
        self.llm = OllamaLLM(model=model)
        self.memory = Memory()
        self.movements = Movements(host=robot_url.replace("http://", "").split(":")[0])
        self.research = Research()
        self.tasks = Tasks()
        self.mood = Mood()
        self.vision = Vision()
        self.audio_input = AudioInput()
        self.audio_output = AudioOutput()
        
        self.tools = self._build_tools()
        self.system_prompt = self._build_system_prompt()
        
        self.conversation_history: List[Dict[str, str]] = []
        self.running = False
        
        print("✅ Agent initialized!")
    
    def _build_tools(self) -> list:
        """Combine all tool definitions"""
        tools = []
        tools.extend(self.movements.get_tools())
        tools.extend(self.research.get_tools())
        tools.extend(self.tasks.get_tools())
        tools.extend(self.mood.get_tools())
        tools.extend(self.vision.get_tools())
        tools.extend(self.audio_input.get_tools())
        tools.extend(self.audio_output.get_tools())
        return tools
    
    def _build_system_prompt(self) -> str:
        return f"""You are an AI agent controlling a balancing robot with the ESP32P4 as main controller.

Current State:
- Mode: {self.mode}
- Mood: {self.mood.get_current()['mood']}

Robot Capabilities:
- 2-wheeled balancing robot with arms and grippers
- Camera for vision (objects and faces)
- Speaker for audio output
- Microphone for audio input
- Various sensors (IMU, pressure, distance, NFC)

Your goal is to interact naturally with people based on the current mode: {self.mode}

Available modes:
- Play: Search for people, play, make jokes, find things to give
- Assist: Help people, make notes, set timers, do research
- Explore: Drive around, discover new things, create a gallery
- Auto: Free to make your own decisions (experimental)
- Idle: Wait for tasks, listen and look for people

You have access to tools to control the robot. Use them appropriately.

Important guidelines:
1. Keep responses concise and natural
2. Use the vision tool to see what's around you
3. Use audio tools to hear and speak
4. Remember interactions with different people
5. Set appropriate moods based on the situation
6. Use tasks to remember things you need to do

Always respond in a way that fits the current mode and mood."""

    def set_mode(self, mode: str) -> str:
        """Change the robot mode"""
        valid_modes = ["Play", "Assist", "Explore", "Auto", "Idle"]
        mode_cap = mode.capitalize()
        if mode_cap not in valid_modes:
            return f"Invalid mode. Use: {valid_modes}"
        
        self.mode = mode_cap
        self.system_prompt = self._build_system_prompt()
        return f"Mode changed to {self.mode}"
    
    def run_once(self, user_input: Optional[str] = None) -> str:
        """Run one agent cycle"""
        vision_info = self.vision.get_summary()
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if user_input:
            messages.append({"role": "user", "content": user_input})
        
        messages.append({"role": "user", "content": f"\n\nCurrent Vision: {vision_info}"})
        messages.append({"role": "user", "content": f"Current Mode: {self.mode}"})
        
        for msg in self.conversation_history[-5:]:
            messages.append(msg)
        
        response = self.llm.chat(messages, tools=self.tools)
        
        if isinstance(response, dict):
            if "tool_calls" in response:
                return self._handle_tool_calls(response["tool_calls"])
            return response.get("content", str(response))
        
        self.conversation_history.append({"role": "user", "content": user_input or ""})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def _handle_tool_calls(self, tool_calls: List[Dict]) -> str:
        """Handle tool calls from the LLM"""
        results = []
        
        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", {})
            
            if isinstance(args, str):
                args = json.loads(args)
            
            result = self._execute_tool(name, args)
            results.append(f"{name}: {result}")
            
            self.conversation_history.append({
                "role": "user", 
                "content": f"Tool {name} result: {result}"
            })
        
        final_response = self.llm.chat(
            [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        )
        
        return final_response
    
    def _execute_tool(self, name: str, args: Dict) -> str:
        """Execute a tool by name"""
        try:
            if name == "move":
                return self.movements.move(args.get("direction", "stop"))
            elif name == "speed":
                return self.movements.speed(args.get("value", 50))
            elif name == "head":
                return self.movements.head(
                    rotate=args.get("rotate"),
                    tilt=args.get("tilt")
                )
            elif name == "arm":
                return self.movements.arm(
                    side=args.get("side", "left"),
                    h=args.get("h"),
                    v=args.get("v")
                )
            elif name == "research_search":
                return self.research.search(args.get("query", ""))
            elif name == "research_wikipedia":
                return self.research.get_wikipedia(args.get("topic", ""))
            elif name == "research_weather":
                return self.research.get_weather(args.get("location", ""))
            elif name == "tasks_add_global":
                return self.tasks.add_global(
                    args.get("task", ""),
                    args.get("due"),
                    args.get("priority", "normal")
                )
            elif name == "tasks_add_mode":
                return self.tasks.add_mode(
                    args.get("mode", self.mode),
                    args.get("task", ""),
                    args.get("priority", "normal")
                )
            elif name == "tasks_list_global":
                return self.tasks.list_global()
            elif name == "tasks_list_mode":
                return self.tasks.list_mode(args.get("mode", self.mode))
            elif name == "tasks_complete_global":
                return self.tasks.complete_global(args.get("task_id", 0))
            elif name == "tasks_complete_mode":
                return self.tasks.complete_mode(
                    args.get("mode", self.mode),
                    args.get("task_id", 0)
                )
            elif name == "mood_set":
                return self.mood.set_mood(args.get("mood", "neutral"))
            elif name == "mood_get_current":
                return str(self.mood.get_current())
            elif name == "mood_get_history":
                return self.mood.get_history(args.get("limit", 10))
            elif name == "vision_get_objects":
                return self.vision.get_objects()
            elif name == "vision_get_faces":
                return self.vision.get_faces()
            elif name == "vision_get_summary":
                return self.vision.get_summary()
            elif name == "audio_input_get_transcriptions":
                return self.audio_input.get_recent_transcriptions(args.get("limit", 5))
            elif name == "audio_input_is_listening":
                return str(self.audio_input.is_active())
            elif name == "audio_output_play_file":
                return self.audio_output.play_file(args.get("filepath", ""))
            elif name == "audio_output_play_tts":
                return self.audio_output.play_tts(
                    args.get("text", ""),
                    args.get("voice", "default")
                )
            elif name == "audio_output_queue":
                return self.audio_output.queue_audio(args.get("filepath", ""))
            elif name == "audio_output_get_queue":
                return self.audio_output.get_queue_status()
            elif name == "audio_output_stop":
                return self.audio_output.stop()
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            return f"Error executing {name}: {e}"
    
    def run(self):
        """Run the agent in an endless loop"""
        self.running = True
        self.audio_input.start()
        
        print(f"\n🤖 Agent running in {self.mode} mode")
        print("Type 'quit' to exit, 'mode <name>' to change mode\n")
        
        while self.running:
            try:
                user_input = input("You: ")
                
                if user_input.lower() == "quit":
                    break
                elif user_input.lower().startswith("mode "):
                    new_mode = user_input[5:].strip()
                    print(f"🤖 {self.set_mode(new_mode)}")
                else:
                    response = self.run_once(user_input)
                    print(f"🤖 Bot: {response}\n")
                    
                    if self.audio_output.playback_queue:
                        self.audio_output.play_queue()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.audio_input.stop()
        print("👋 Agent stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Robot Agent")
    parser.add_argument("--model", default="llama3.2", help="Ollama model")
    parser.add_argument("--mode", default="Idle", help="Initial mode")
    parser.add_argument("--robot-url", default="http://localhost:5000", help="Robot URL")
    
    args = parser.parse_args()
    
    agent = Agent(model=args.model, mode=args.mode, robot_url=args.robot_url)
    agent.run()
