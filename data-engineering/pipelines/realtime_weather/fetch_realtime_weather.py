import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("data-engineering/pipelines/realtime_weather/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VICTORIA_LOCATIONS = [
    {"location_id": 1, "name": "Melbourne", "latitude": -37.8136, "longitude": 144.9631},
    {"location_id": 2, "name": "East Gippsland", "latitude": -37.7000, "longitude": 148.4600},
    {"location_id": 3, "name": "Bendigo", "latitude": -36.7570, "longitude": 144.2794},
    {"location_id": 4, "name": "Ballarat", "latitude": -37.5622, "longitude": 143.8503},
    {"location_id": 5, "name": "Shepparton", "latitude": -36.3833, "longitude": 145.4000},
]

def fetch_weather(location):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m"
        ],
        "timezone": "Australia/Melbourne"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    current = data.get("current", {})

    return {
        "location_id": location["location_id"],
        "location_name": location["name"],
        "time_id": int(datetime.now().strftime("%Y%m%d%H")),
        "original_latitude": location["latitude"],
        "original_longitude": location["longitude"],
        "temperature_c": current.get("temperature_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "relative_humidity": current.get("relative_humidity_2m"),
        "source_system": "Open-Meteo",
        "ingestion_time": datetime.now().isoformat()
    }

def main():
    records = []

    for location in VICTORIA_LOCATIONS:
        try:
            record = fetch_weather(location)
            records.append(record)
            print(f"Fetched weather for {location['name']}")
        except Exception as error:
            print(f"Failed to fetch weather for {location['name']}: {error}")

    df = pd.DataFrame(records)

    output_file = OUTPUT_DIR / "realtime_weather_raw.csv"
    df.to_csv(output_file, index=False)

    print(f"\nSaved real-time weather data to: {output_file}")
    print(df)

if __name__ == "__main__":
    main()
