import os
from typing import Dict, Any, Optional

import requests
from agents.mcp import MCPServer

# Get API key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


class CheckWeatherServer(MCPServer):
    """MCP server for checking weather information using OpenWeather One Call API 3.0."""

    def __init__(self):
        super().__init__("check_weather")
        self.api_key = OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall"
        self.geocoding_url = "https://api.openweathermap.org/geo/1.0/direct"
        # Fallback to 2.5 API if 3.0 is not available
        self.fallback_url = "https://api.openweathermap.org/data/2.5/weather"

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the weather check request."""
        try:
            # Extract parameters from the request
            location = request.get("location")
            lat = request.get("lat")
            lon = request.get("lon")
            exclude = request.get("exclude", "")
            units = request.get("units", "metric")
            lang = request.get("lang", "en")

            # If lat/lon are not provided, try to get them from location name
            if not lat or not lon:
                if not location:
                    return {
                        "success": False,
                        "error": "Either location name or lat/lon coordinates are required"
                    }

                # Get coordinates from location name
                coords = self._get_coordinates(location)
                if not coords:
                    return {
                        "success": False,
                        "error": f"Could not find coordinates for location: {location}"
                    }

                lat, lon = coords

            # Get weather data
            weather_data = self._get_weather(lat, lon, exclude, units, lang)

            if not weather_data:
                return {
                    "success": False,
                    "error": f"Failed to get weather data for coordinates: {lat}, {lon}"
                }

            # Add location name to the response if provided
            if location:
                weather_data["location_name"] = location

            return {
                "success": True,
                "data": weather_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error checking weather: {str(e)}"
            }

    def _get_coordinates(self, location: str) -> Optional[tuple]:
        """Get coordinates from location name using OpenWeather Geocoding API."""
        if not self.api_key:
            raise ValueError("OpenWeather API key is not set")

        params = {
            "q": location,
            "limit": 1,
            "appid": self.api_key
        }

        response = requests.get(self.geocoding_url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0].get("lat"), data[0].get("lon")

        return None

    def _get_weather(self, lat: float, lon: float, exclude: str, units: str, lang: str) -> Optional[Dict[str, Any]]:
        """Get weather data from OpenWeather One Call API 3.0."""
        if not self.api_key:
            raise ValueError("OpenWeather API key is not set")

        # Try the One Call API 3.0 first
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": units,
            "lang": lang
        }

        if exclude:
            params["exclude"] = exclude

        response = requests.get(self.base_url, params=params)

        # If the 3.0 API fails (e.g., subscription required), fall back to 2.5 API
        if response.status_code != 200:
            # Try the fallback API
            fallback_params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units,
                "lang": lang
            }

            fallback_response = requests.get(self.fallback_url, params=fallback_params)

            if fallback_response.status_code == 200:
                return fallback_response.json()
            else:
                # If both APIs fail, return None
                return None

        return response.json()
