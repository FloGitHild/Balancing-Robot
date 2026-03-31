import requests
import json
import os
from typing import Optional, Dict, Any, List

class OllamaLLM:
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._check_connection()
    
    def _check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
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
            "stream": False
        }
        if tools:
            payload["tools"] = tools
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                print(f"❌ LLM error: {response.status_code}")
                return "Error: Could not get response from LLM"
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
