import os
import sys
import json
import time
import base64
import io
import threading
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False

try:
    import socketio
    import requests
    import soundfile as sf
    import numpy as np
    TTS_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    TTS_AVAILABLE = False

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
                 model: str = "llama3.2:latest",
                 mode: str = "Idle",
                 robot_url: str = "http://localhost:5000"):
        print("🚀 Initializing Agent...")
        
        self.mode = mode
        self.robot_url = robot_url
        self.llm = OllamaLLM(model=model)
        self.memory = Memory()
        self.movements = Movements(host=robot_url.replace("http://", "").split(":")[0])
        self.research = Research()
        self.tasks = Tasks()
        self.mood = Mood()
        self.vision = Vision()
        self.audio_input = AudioInput()
        self.audio_output = AudioOutput()
        
        self.sio = None
        self._setup_socket()
        
        self.tools = self._build_tools()
        self.system_prompt = self._build_system_prompt()
        
        self.conversation_history: List[Dict[str, str]] = []
        self.running = False
        
        print("✅ Agent initialized!")
    
    def _setup_socket(self):
        """Setup socket connection to robot for audio"""
        if SOCKETIO_AVAILABLE:
            try:
                self.sio = socketio.Client(logger=False, engineio_logger=False)
                
                @self.sio.event
                def connect():
                    print("✅ Connected to Robot for audio")
                
                @self.sio.event
                def connect_error(data):
                    print(f"❌ Socket connection error: {data}")
                
                self.sio.connect(self.robot_url, transports=['websocket'])
                
                @self.sio.on('vision_update')
                def on_vision_update(data):
                    """Receive vision updates from vision_for_agent"""
                    print(f"📥 Agent got vision: {data}")
                    self.vision.update_from_dict(data)
                
                @self.sio.on('agent_command')
                def on_agent_command(cmd):
                    """Receive commands from website"""
                    print(f"📥 Received command from website: {cmd}")
                    response = self.run_once(cmd)
                    self.speak(response)
                    
            except Exception as e:
                print(f"⚠️ Could not connect to robot: {e}")
                self.sio = None
        else:
            print("⚠️ socketio not installed - audio will not be sent to robot")
            self.sio = None
    
    def request_vision_update(self):
        """Request vision update from vision_for_agent"""
        if self.sio and self.sio.connected:
            self.sio.emit('request_vision')
    
    def _send_audio_to_robot(self, audio_data: bytes):
        """Send audio data to robot via socket"""
        if not self.sio or not self.sio.connected:
            return
        
        try:
            CHUNK_SIZE = 30000
            self.sio.emit("play_audio_start")
            
            for i in range(0, len(audio_data), CHUNK_SIZE):
                chunk = audio_data[i:i+CHUNK_SIZE]
                b64_chunk = base64.b64encode(chunk).decode('utf-8')
                self.sio.emit("play_audio_chunk", {'chunk': b64_chunk})
                time.sleep(0.01)
            
            self.sio.emit("play_audio_end")
            print("✅ Audio sent to robot")
        except Exception as e:
            print(f"❌ Error sending audio: {e}")
    
    def _send_mood_to_robot(self, mood: str):
        """Send mood to robot to update the emoji on website"""
        if not self.sio or not self.sio.connected:
            return
        try:
            # Map mood to emotion string that simulator expects
            mood_to_emotion = {
                "neutral": "Neutral",
                "happy": "Freudig",
                "sad": "Traurig",
                "curious": "Neugierig",
                "excited": "Freudig",
                "thinking": "Neutral",
                "surprised": "Neutral",
                "scared": "Traurig",
                "angry": "Traurig",
                "relaxed": "Entspannt"
            }
            emotion = mood_to_emotion.get(mood, "Neutral")
            self.sio.emit('cmd', f"__mood__{emotion}")
            print(f"✅ Mood sent to robot: {mood} -> {emotion}")
        except Exception as e:
            print(f"❌ Error sending mood: {e}")
    
    def _detect_language(self, text: str) -> str:
        """Improved language detection using character and word analysis"""
        text_lower = text.lower()
        
        german_chars = sum(1 for c in text_lower if c in 'äöüß')
        
        german_words = {'der', 'die', 'das', 'und', 'ist', 'ich', 'du', 'er', 'sie', 'hallo', 
                       'danke', 'bitte', 'ja', 'nein', 'guten', 'guten tag', 'wetter', 'wer', 
                       'was', 'wo', 'wann', 'warum', 'wie', 'welche', 'wen', 'wem', 'wieso', 
                       'weshalb', 'woher', 'es', 'wir', 'ihr', 'mir', 'dir', 'nicht', 'haben', 
                       'sein', 'werden', 'kann', 'möchte', 'will', 'soll', 'mag', 'heißt', 
                       'heiße', 'bin', 'bist', 'seid', 'sind', 'war', 'warst', 'waren',
                       'schön', 'gerne', 'vielleicht', 'heute', 'morgen', 'jetzt', 'hier',
                       'dort', 'sehr', 'viel', 'wenig', 'mehr', 'alle', 'jeder', 'kein',
                       'eine', 'einer', 'einem', 'einen', 'mit', 'nach', 'vor', 'auf', 
                       'unter', 'über', 'zwischen', 'bei', 'von', 'zu', 'aus', 'in', 'an'}
        
        german_word_count = sum(1 for word in text_lower.split() if word in german_words)
        
        english_words = {'the', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does',
                       'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
                       'hello', 'hi', 'hey', 'thanks', 'thank', 'please', 'yes', 'no', 'not',
                       'what', 'who', 'where', 'when', 'why', 'how', 'which', 'weather', 
                       'know', 'think', 'want', 'like', 'love', 'good', 'bad', 'great', 
                       'nice', 'today', 'tomorrow', 'now', 'here', 'there', 'very', 'much',
                       'all', 'some', 'any', 'can', 'me', 'you', 'he', 'she', 'it', 'we', 
                       'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 
                       'that', 'these', 'those', 'am', 'be', 'been', 'being', 'but', 'or',
                       'if', 'then', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
                       'for', 'with', 'about', 'between', 'into', 'through', 'during'}
        
        english_word_count = sum(1 for word in text_lower.split() if word in english_words)
        
        german_score = german_chars * 2 + german_word_count * 3
        english_score = english_word_count * 3
        
        if german_score > english_score:
            return "de"
        return "en"
    
    def _generate_tts(self, text: str) -> Optional[bytes]:
        """Generate TTS using edge-tts - child-like voice: fast & high pitch"""
        try:
            import edge_tts
            import asyncio
            
            max_chars = 500
            if len(text) > max_chars:
                text = text[:max_chars]
            
            lang = self._detect_language(text)
            
            # Edge TTS voices with child-like settings
            if lang == "de":
                voice = "de-DE-KatjaNeural"
            else:
                voice = "en-US-JennyNeural"
            
            # Fast (+20%) and higher pitch (+60Hz) for child-like voice
            mp3_file = '/tmp/tts_edge.mp3'
            
            async def generate():
                communicate = edge_tts.Communicate(text, voice, rate="+20%", pitch="+60Hz")
                await communicate.save(mp3_file)
            
            asyncio.run(generate())
            
            with open(mp3_file, 'rb') as f:
                return f.read()
                    
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    def speak(self, text: str):
        """Print and speak text to robot"""
        print(f"🤖 Bot: {text}")
        
        # Generate TTS and send to robot
        tts_audio = self._generate_tts(text)
        
        if tts_audio:
            self._send_audio_to_robot(tts_audio)
        else:
            print("🔊 (TTS not available)")
    
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
        tools.extend(self._get_memory_tools())
        return tools
    
    def _get_memory_tools(self) -> list:
        """Get memory tool definitions"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "memory_remember",
                    "description": "Remember something about the current person (name, preferences, topics discussed)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "what": {"type": "string", "description": "What to remember about the person"}
                        },
                        "required": ["what"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "memory_recall",
                    "description": "Recall previous interactions with a specific person",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "person": {"type": "string", "description": "Name of person to recall"},
                            "limit": {"type": "integer", "description": "Number of interactions to recall", "default": 5}
                        },
                        "required": ["person"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "memory_get_people",
                    "description": "Get list of all people the agent knows",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
    
    def _build_system_prompt(self) -> str:
        return f"""You are a SINGLE robot assistant (not multiple). 
You are one AI. Use "I", "me", "my" - NEVER "we", "us", "our".

IMPORTANT: 
1. You can answer in ANY language! Match the language the user is speaking.
2. Keep responses SHORT and CONCISE - maximum 1-2 sentences.
3. Don't use complicated descriptions or actions in your response.

Current State:
- Mode: {self.mode}
- Mood: {self.mood.get_current()['mood']}

CRITICAL RULES:
1. NEVER make up information about weather, facts, or current events
2. When asked about weather, ALWAYS use research_weather tool first
3. When asked for facts, ALWAYS use research_wikipedia or research_search tool first
4. When asked about WHO is in front of you, ALWAYS use vision_get_faces tool
5. The vision shows "Known people: NAME" = who is with you now
6. ALWAYS use vision_get_faces when someone asks "who am i?", "who is here?", "who is with me?"

IMPORTANT: If vision shows "Known people: Florian" and user asks "Who am I?" -> Answer: "You are Florian!"

You have tools: 
- research_weather, research_wikipedia, research_search 
- vision_get_summary
- memory_remember (remember something about current person), memory_recall (recall previous interactions)

Available modes: Play, Assist, Explore, Auto, Idle

Respond in short sentences using verified tool results."""

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
        """Run agent cycle - think first, then act"""
        vision_info = self.vision.get_summary()
        
        # Get memory context for current known people
        known_people = self.vision.get_faces()
        memory_context = ""
        if "No faces" not in known_people:
            import re
            names = re.findall(r'([A-Z][a-z]+):', known_people)
            for name in names:
                if name != "Unknown":
                    mem = self.memory.get_interactions(name)
                    if mem and "No interactions" not in mem:
                        memory_context += f"\nPrevious with {name}: {mem.split(chr(10), 2)[-1][:100]}"
        
        # Step 1: Ask LLM what to do (without tools)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input or ""},
            {"role": "user", "content": f"\nCurrent Vision: {vision_info}"},
            {"role": "user", "content": f"Current Mode: {self.mode}"},
            {"role": "user", "content": f"Memory Context: {memory_context}" if memory_context else ""}
        ]
        
        # Print prompt for debugging
        print("\n" + "="*50)
        print("📝 PROMPT TO LLM:")
        print("-"*50)
        for m in messages:
            print(f"{m['role']}: {m['content'][:200]}...")
        print("="*50 + "\n")
        
        # First, just get a response without tools forcing action
        response = self.llm.chat(messages, tools=self.tools)
        
        # Handle tool calls if LLM decides to use them
        if isinstance(response, dict):
            tool_calls = response.get("tool_calls", [])
            if tool_calls:
                result = self._handle_tool_calls(tool_calls)
                # Step 2: Ask for final response after tools
                final_messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"User asked: {user_input}"},
                    {"role": "user", "content": f"Tools executed. Result: {result}"},
                    {"role": "user", "content": f"Now provide a natural response to the user."}
                ]
                final_response = self.llm.chat(final_messages, tools=None)
                if isinstance(final_response, dict):
                    final_response = final_response.get("content", "")
                return final_response if final_response else result
        
        if isinstance(response, dict):
            response = response.get("content", "")
        
        # If no tools called, return the response
        return response if response else "I'm not sure how to respond. Could you try again?"
    
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
        
        # Ask LLM for final response after tools - include tool results in prompt
        tool_results_text = "\n".join(results)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Based on the user's question and the tool results below, provide a natural response.\n\nTool results:\n{tool_results_text}\n\nUser question: {self.conversation_history[-1].get('content', '') if self.conversation_history else ''}"}
        ]
        
        final_response = self.llm.chat(messages, tools=None)  # No tools on final response
        
        # Handle dict response
        if isinstance(final_response, dict):
            return final_response.get("content", "")
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
            elif name == "research_get_time":
                return self.research.get_current_time()
            elif name == "research_time_until":
                return self.research.get_time_until(args.get("target_time", ""))
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
                new_mood = args.get("mood", "neutral")
                current_mood = self.mood.get_current()["mood"]
                mood_result = self.mood.set_mood(new_mood)
                # Only send to robot if mood actually changed
                if new_mood != current_mood:
                    self._send_mood_to_robot(new_mood)
                return mood_result
            elif name == "mood_get_current":
                return str(self.mood.get_current())
            elif name == "mood_get_history":
                return self.mood.get_history(args.get("limit", 10))
            elif name == "vision_get_objects":
                # Just read cached data - vision runs continuously
                return self.vision.get_objects()
            elif name == "vision_get_faces":
                # Just read cached data - vision runs continuously
                return self.vision.get_faces()
            elif name == "vision_get_summary":
                # Just read cached data - vision runs continuously
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
            elif name == "memory_remember":
                known_people = self.vision.get_faces()
                import re
                names = re.findall(r'([A-Z][a-z]+):', known_people)
                names = [n for n in names if n != "Unknown"]
                person = names[0] if names else "Unknown"
                return self.memory.add_interaction(person, {"summary": args.get("what", "")})
            elif name == "memory_recall":
                return self.memory.get_interactions(args.get("person", ""), args.get("limit", 5))
            elif name == "memory_get_people":
                return str(self.memory.get_all_people())
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
                    self.speak(response)
                    
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
        if self.sio and self.sio.connected:
            self.sio.disconnect()
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
