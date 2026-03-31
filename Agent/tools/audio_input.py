import threading
import queue
from typing import Optional, List, Dict, Any
import time
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except OSError:
    AUDIO_AVAILABLE = False

class AudioInput:
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 2.0):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_listening = False
        self.transcription_history: List[Dict[str, Any]] = []
        self.stream = None
        
        if AUDIO_AVAILABLE:
            try:
                self.stream = sd.InputStream(
                    samplerate=sample_rate,
                    channels=1,
                    dtype='int16',
                    callback=self._audio_callback
                )
            except Exception as e:
                print(f"⚠️ Audio input error: {e}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}")
        audio_data = indata.copy()
        self.audio_queue.put(audio_data)
    
    def start(self):
        """Start listening"""
        if self.stream:
            self.stream.start()
            self.is_listening = True
            print("🎤 Audio input started")
    
    def stop(self):
        """Stop listening"""
        if self.stream:
            self.stream.stop()
            self.is_listening = False
            print("🎤 Audio input stopped")
    
    def get_latest_audio(self) -> Optional[np.ndarray]:
        """Get the most recent audio chunk"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_recent_transcriptions(self, limit: int = 5) -> str:
        """Get recent transcription history"""
        if not self.transcription_history:
            return "No transcriptions yet"
        
        result = "Recent Transcriptions:\n"
        for t in self.transcription_history[-limit:]:
            result += f"  - [{t.get('timestamp', '')}] {t.get('text', '')}\n"
        return result.strip()
    
    def add_transcription(self, text: str):
        """Add a transcription (called by speech-to-text)"""
        self.transcription_history.append({
            "text": text,
            "timestamp": time.time()
        })
        # Keep only last 50
        if len(self.transcription_history) > 50:
            self.transcription_history = self.transcription_history[-50:]
    
    def is_active(self) -> bool:
        """Check if audio input is active"""
        return self.is_listening
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "audio_input_get_transcriptions",
                    "description": "Get recent transcriptions of what people have said",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 5}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "audio_input_is_listening",
                    "description": "Check if the robot is currently listening",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

if __name__ == "__main__":
    ai = AudioInput()
    ai.start()
    time.sleep(3)
    ai.stop()
    print(ai.get_recent_transcriptions())
