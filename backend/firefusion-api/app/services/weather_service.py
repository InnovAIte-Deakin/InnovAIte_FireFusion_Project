import requests

WEATHERAPI_KEY = "de1eb935c7ec4262a9230218260704"


def get_lat_lon(city):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city, "format": "json", "limit": 1}
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        return None, None



def get_weather_weatherapi(city="Melbourne"):
    try:
        url = "http://api.weatherapi.com/v1/current.json"
        params = {"key": WEATHERAPI_KEY, "q": city}
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        current = data.get("current", {})
        condition = current.get("condition", {}).get("text")

        return {
            "temperature": current.get("temp_c"),
            "humidity": current.get("humidity"),
            "wind_speed": current.get("wind_kph"),
            "condition": condition,
            "source": "WeatherAPI"
        }
    except:
        return None



def get_weather_openmeteo(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "relativehumidity_2m,windspeed_10m,weathercode"
        }
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        current = data.get("current_weather", {})

        humidity_list = data.get("hourly", {}).get("relativehumidity_2m", [])
        humidity = humidity_list[0] if humidity_list else None

        weather_code_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Drizzle light",
            53: "Drizzle moderate",
            55: "Drizzle dense",
            61: "Rain slight",
            63: "Rain moderate",
            65: "Rain heavy",
            71: "Snow slight",
            73: "Snow moderate",
            75: "Snow heavy",
            80: "Rain showers slight",
            81: "Rain showers moderate",
            82: "Rain showers violent",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        weather_code = current.get("weathercode", 0)
        condition = weather_code_map.get(weather_code, "Unknown")

        return {
            "temperature": current.get("temperature"),
            "humidity": humidity,
            "wind_speed": current.get("windspeed"),
            "condition": condition,
            "source": "Open-Meteo"
        }
    except:
        return {"error": "Weather unavailable from Open-Meteo"}



def get_weather(city="Melbourne"):
   
    weather = get_weather_weatherapi(city)
    if weather:
        return weather

    
    lat, lon = get_lat_lon(city)
    if lat is None or lon is None:
        return {"error": "Could not find city coordinates"}

    return get_weather_openmeteo(lat, lon)