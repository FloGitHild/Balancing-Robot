import requests
from typing import Optional, Dict, Any, List
from urllib.parse import quote
import re
from datetime import datetime

class Research:
    def __init__(self, preferred_sources: Optional[List[str]] = None):
        self.preferred_sources = preferred_sources or [
            "https://en.wikipedia.org/wiki/",
            "https://www.wetter.de/"
        ]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"
        })
    
    def get_current_time(self) -> str:
        """Get current date and time"""
        now = datetime.now()
        return f"📅 {now.strftime('%A, %d. %B %Y')}\n⏰ {now.strftime('%H:%M:%S')}"
    
    def get_time_until(self, target_time: str) -> str:
        """Calculate time until a target time (format: HH:MM)"""
        try:
            now = datetime.now()
            target = datetime.strptime(target_time, "%H:%M")
            target = target.replace(year=now.year, month=now.month, day=now.day)
            
            if target < now:
                target = target.replace(day=now.day + 1)
            
            diff = target - now
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"Noch {hours}h {minutes}m bis {target_time}"
        except:
            return "Invalid time format. Use HH:MM"
    
    def search(self, query: str, num_results: int = 3) -> str:
        """Search using Wikipedia as primary source"""
        if not query:
            return "No query provided"
        
        # Try Wikipedia first
        wiki_result = self.get_wikipedia(query.replace(" ", "_"))
        if not "error" in wiki_result.lower() and "not found" not in wiki_result.lower():
            return wiki_result
        
        # Try Wikipedia API search
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(query)}&limit={num_results}&format=json"
        try:
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                titles = data.get(1, [])
                if titles:
                    results = []
                    for title in titles[:num_results]:
                        results.append(self.get_wikipedia(title))
                    return "Search results for '" + query + "'.\n\n" + "\n\n---\n\n".join(results)
        except:
            pass
        
        return f"I couldn't find information about '{query}'. Try being more specific."
    
    def get_wikipedia(self, topic: str) -> str:
        """Get information from Wikipedia"""
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return f"📖 {data.get('title', topic)}\n{data.get('extract', 'No summary available')}"
            elif response.status_code == 404:
                return f"Topic '{topic}' not found on Wikipedia"
            else:
                return f"Wikipedia error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_weather(self, location: str = "") -> str:
        """Get weather using wetter.com (primary) with Open-Meteo as fallback"""
        # If no location or vague location, try to get from IP
        if not location or location.lower() in ["my location", "current location", "here", "当前位置"]:
            ip_location = self._get_location_from_ip()
            if ip_location:
                location = ip_location
                print(f"📍 Detected location from IP: {location}")
        
        if not location:
            return "No location provided. Please specify a city."
        
        wetter_result = self._get_wetter_com(location)
        if wetter_result:
            return wetter_result
        
        openmeteo_result = self._get_open_meteo(location)
        return openmeteo_result if openmeteo_result else f"Could not get weather for {location}"
    
    def _get_location_from_ip(self) -> Optional[str]:
        """Get current location from IP address"""
        try:
            response = self.session.get("http://ip-api.com/json/?fields=status,country,city", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    city = data.get("city", "")
                    country = data.get("country", "")
                    return f"{city}, {country}" if city and country else city
        except:
            pass
        return None
    
    def _get_wetter_com(self, location: str) -> Optional[str]:
        """Scrape weather from wetter.com"""
        try:
            search_url = f"https://www.wetter.de/suche?q={quote(location)}"
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            match = re.search(r'href="(/weltwetter/[^"]+)"', response.text)
            if not match:
                match = re.search(r'data-city="([^"]+)"', response.text)
            
            city_url = match.group(1) if match else None
            if not city_url:
                return None
            
            city_url = f"https://www.wetter.de{city_url}" if not city_url.startswith("http") else city_url
            
            weather_response = self.session.get(city_url, timeout=15)
            if weather_response.status_code != 200:
                return None
            
            html = weather_response.text
            
            temp_match = re.search(r'class="temperature"\s*>(\d+)', html)
            condition_match = re.search(r'class="weather-state-label"[^>]*>([^<]+)', html)
            
            temp = temp_match.group(1) if temp_match else "?"
            condition = condition_match.group(1).strip() if condition_match else "Unbekannt"
            
            humidity_match = re.search(r'Luftfeuchtigkeit.*?(\d+)%', html)
            humidity = f"{humidity_match.group(1)}%" if humidity_match else ""
            
            wind_match = re.search(r'Wind.*?(\d+)\s*km/h', html)
            wind = f"{wind_match.group(1)} km/h" if wind_match else ""
            
            parts = [f"🌡️ {temp}°C {condition}"]
            if humidity:
                parts.append(f"💧 {humidity}")
            if wind:
                parts.append(f"💨 {wind}")
            
            return f"Wetter in {location.title()}: {' | '.join(parts)}"
            
        except Exception as e:
            print(f"wetter.com error: {e}")
            return None
    
    def _get_open_meteo(self, location: str) -> Optional[str]:
        """Fallback: Get weather using Open-Meteo API"""
        try:
            geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(location)}&count=1"
            geo_response = self.session.get(geocode_url, timeout=10)
            
            if geo_response.status_code != 200:
                return f"Could not find location: {location}"
            
            geo_data = geo_response.json()
            if not geo_data.get('results'):
                return f"Location '{location}' not found"
            
            lat = geo_data['results'][0]['latitude']
            lon = geo_data['results'][0]['longitude']
            name = geo_data['results'][0]['name']
            
            # Get weather data
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
            weather_response = self.session.get(weather_url, timeout=10)
            
            if weather_response.status_code == 200:
                data = weather_response.json()
                current = data.get('current', {})
                temp = current.get('temperature_2m', 'N/A')
                wind = current.get('wind_speed_10m', 'N/A')
                code = current.get('weather_code', 0)
                
                # Simple weather description
                weather_desc = self._weather_code_to_desc(code)
                
                return f"🌤️ Weather in {name}: {temp}°C, {weather_desc}, Wind: {wind} km/h"
            else:
                return f"Weather API error: {weather_response.status_code}"
                
        except Exception as e:
            return f"Weather error: {str(e)}"
    
    def _weather_code_to_desc(self, code: int) -> str:
        """Convert Open-Meteo weather code to description"""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            95: "Thunderstorm"
        }
        return codes.get(code, f"Code {code}")
    
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
            },
            {
                "type": "function",
                "function": {
                    "name": "research_get_time",
                    "description": "Get the current date and time",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "research_time_until",
                    "description": "Calculate time until a target time (format HH:MM)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_time": {"type": "string", "description": "Target time in HH:MM format"}
                        },
                        "required": ["target_time"]
                    }
                }
            }
        ]

if __name__ == "__main__":
    r = Research()
    print(r.get_current_time())
    print(r.search("Python programming"))
    print(r.get_wikipedia("Python_(programming_language)"))
    print(r.get_weather("Berlin"))
