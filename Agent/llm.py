import requests
import json
import os
from typing import Optional, Dict, Any, List

class OllamaLLM:
    def __init__(self, model: str = "llama3.2:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
        self._check_connection()
    
    def _check_connection(self):
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                available = [m["name"] for m in response.json().get("models", [])]
                print(f"✅ Ollama connected. Available models: {available}")
                if self.model not in available:
                    print(f"⚠️ Model '{self.model}' not found. Using first available.")
                    self.model = available[0] if available else "llama3.2"
            else:
                print(f"⚠️ Ollama returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            print("💡 Make sure Ollama is running: ollama serve")
    
    def chat(self, messages: List[Dict[str, str]], tools: Optional[Any] = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": 4096,  # Reduced for speed
                "num_predict": 256,  # Limit response length
                "temperature": 0.7,
                "num_gpu": 0,  # Use CPU if no GPU
                "threads": 4  # Limit threads for faster response
            }
        }
        if tools:
            payload["tools"] = tools
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180  # Increased timeout for slower models
            )
            if response.status_code == 200:
                result = response.json()
                
                msg = result.get("message", {})
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])
                
                if tool_calls:
                    return {
                        "content": content,
                        "tool_calls": tool_calls
                    }
                return content
            else:
                print(f"❌ LLM error: {response.status_code} - {response.text}")
                return "Error: Could not get response from LLM"
        except requests.Timeout:
            print("❌ LLM request timed out")
            return "Error: LLM request timed out"
        except Exception as e:
            print(f"❌ LLM request failed: {e}")
            return "Error: LLM request failed"
    
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages)
    
    def list_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
        except:
            pass
        return []

if __name__ == "__main__":
    llm = OllamaLLM()
    print(llm.generate("Hello, how are you?"))
