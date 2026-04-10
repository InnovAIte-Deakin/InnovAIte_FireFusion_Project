import os
import httpx

API_KEY = os.getenv("OPENMETEO_API_KEY")

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(location: str):
    """
    Fetch weather data from Open-Meteo API
    """

 
    locations = {
        "melbourne": (-37.8136, 144.9631),
        "geelong": (-38.1499, 144.3617),
        "ballarat": (-37.5622, 143.8503),
    }

    location = location.lower()

    if location not in locations:
        return {"error": "Location not supported"}

    lat, lon = locations[location]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL, params=params)
        data = response.json()

    return {
        "location": location,
        "temperature": data["current_weather"]["temperature"],
        "windspeed": data["current_weather"]["windspeed"],
    }
