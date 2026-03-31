import os
import io
import base64
import threading
from typing import Optional, List, Dict, Any

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    AUDIO_AVAILABLE = True
except OSError:
    AUDIO_AVAILABLE = False

class AudioOutput:
    def __init__(self, output_dir: str = "data/audio"):
        self.output_dir = output_dir
        self.playback_queue: List[Dict[str, Any]] = []
        self.is_playing = False
        self.current_file = None
        os.makedirs(output_dir, exist_ok=True)
        
        if not AUDIO_AVAILABLE:
            print("⚠️ Audio output not available (no sound device)")
    
    def play_file(self, filepath: str) -> str:
        """Play an audio file"""
        if not AUDIO_AVAILABLE:
            return "Audio not available"
        
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        
        try:
            audio_data, samplerate = sf.read(filepath, dtype='int16')
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1).astype(np.int16)
            
            sd.play(audio_data, samplerate=samplerate)
            self.is_playing = True
            self.current_file = filepath
            sd.wait()
            self.is_playing = False
            return f"Playing: {os.path.basename(filepath)}"
        except Exception as e:
            return f"Error playing file: {e}"
    
    def play_tts(self, text: str, voice: str = "default") -> str:
        """Generate and play TTS"""
        try:
            from gtts import gTTS
            import io
            
            tts = gTTS(text=text, lang='en')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            audio_data = audio_bytes.read()
            
            self.last_tts_audio = audio_bytes.getvalue()
            return f"TTS generated: {len(audio_data)} bytes"
        except Exception as e:
            return f"TTS error: {e}"
    
    def _save_tts_request(self, text: str, voice: str) -> str:
        """Save TTS request for later generation"""
        import json
        from datetime import datetime
        
        filename = f"tts_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                "text": text,
                "voice": voice,
                "created": datetime.now().isoformat()
            }, f)
        
        return filename
    
    def queue_audio(self, filepath: str) -> str:
        """Add an audio file to the playback queue"""
        if not os.path.exists(filepath):
            return f"File not found: {filepath}"
        
        self.playback_queue.append({"filepath": filepath, "type": "file"})
        return f"Queued: {os.path.basename(filepath)}"
    
    def queue_tts(self, text: str) -> str:
        """Queue TTS for playback"""
        self.playback_queue.append({"text": text, "type": "tts"})
        return f"Queued TTS: {text[:50]}..."
    
    def play_queue(self):
        """Process the playback queue"""
        while self.playback_queue:
            item = self.playback_queue.pop(0)
            if item["type"] == "file":
                self.play_file(item["filepath"])
            elif item["type"] == "tts":
                self._play_generated_tts(item["text"])
    
    def _play_generated_tts(self, text: str):
        """Play generated TTS audio"""
        # Placeholder - implement TTS generation
        print(f"[TTS] Would play: {text}")
    
    def save_audio(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to a file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        return filepath
    
    def get_queue_status(self) -> str:
        """Get current queue status"""
        if not self.playback_queue:
            return "Queue empty"
        
        result = "Playback Queue:\n"
        for i, item in enumerate(self.playback_queue):
            if item["type"] == "file":
                result += f"  {i+1}. {os.path.basename(item['filepath'])}\n"
            else:
                result += f"  {i+1}. TTS: {item['text'][:30]}...\n"
        return result.strip()
    
    def stop(self):
        """Stop current playback"""
        if self.is_playing:
            sd.stop()
            self.is_playing = False
        return "Playback stopped"
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "audio_output_play_file",
                    "description": "Play an audio file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to the audio file"}
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_output_play_tts",
                    "description": "Generate and play text-to-speech",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to speak"},
                            "voice": {"type": "string", "default": "default"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_output_queue",
                    "description": "Queue audio for playback",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {"type": "string", "description": "Path to audio file"}
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_output_get_queue",
                    "description": "Get the current playback queue",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_output_stop",
                    "description": "Stop current playback",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

if __name__ == "__main__":
    ao = AudioOutput()
    print(ao.play_tts("Hello, I am your robot assistant!"))
    print(ao.get_queue_status())
