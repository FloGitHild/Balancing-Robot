import requests
from typing import Optional, Dict, Any, List
from urllib.parse import quote

class Research:
    def __init__(self, preferred_sources: Optional[List[str]] = None):
        self.preferred_sources = preferred_sources or [
            "https://en.wikipedia.org/wiki/",
            "https://www.wetter.de/"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; RobotAgent/1.0)"
        })
    
    def search(self, query: str, num_results: int = 5) -> str:
        """Search the internet for information"""
        if not query:
            return "No query provided"
        
        try:
            # Try DuckDuckGo for general search
            url = f"https://duckduckgo.com/?q={quote(query)}&format=json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Return search results summary
                return f"Search completed for: {query}. Found {num_results} results (simulated - add real search API for production)"
            else:
                return f"Search failed with status: {response.status_code}"
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_wikipedia(self, topic: str) -> str:
        """Get information from Wikipedia"""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return f"📖 {data.get('title', topic)}\n{data.get('extract', 'No summary available')}"
            else:
                return f"Wikipedia error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_weather(self, location: str = "") -> str:
        """Get weather information (Germany focused)"""
        try:
            # Using Open-Meteo (free, no API key needed)
            if location:
                # Simple geocoding would be needed for actual location
                return f"Weather for {location}: (Configure with actual weather API)"
            return "No location provided"
        except Exception as e:
            return f"Weather error: {str(e)}"
    
    def get_tools(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "research_search",
                    "description": "Search the internet for information. Use when you need facts or current information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "research_wikipedia",
                    "description": "Get a summary from Wikipedia",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "The topic to look up"}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "research_weather",
                    "description": "Get current weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City or location"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

if __name__ == "__main__":
    r = Research()
    print(r.search("Python programming"))
    print(r.get_wikipedia("Python_(programming_language)"))
    print(r.get_weather("Berlin"))
