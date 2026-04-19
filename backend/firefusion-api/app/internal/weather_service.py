import os
import httpx

API_KEY = os.getenv("OPENMETEO_API_KEY")

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(latitude: float, longitude: float):

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
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
