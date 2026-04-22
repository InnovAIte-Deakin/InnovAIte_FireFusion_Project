import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from pathlib import Path

# Setup Open-Meteo client with cache and retry
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Victoria locations relevant to Black Summer / fire analysis
LOCATIONS = [
    {"name": "East_Gippsland", "latitude": -37.70, "longitude": 148.46},
    {"name": "Alpine", "latitude": -36.87, "longitude": 147.28},
    {"name": "North_East_Victoria", "latitude": -36.12, "longitude": 146.88},
]

START_DATE = "2019-11-01"
END_DATE = "2022-12-31"

url = "https://archive-api.open-meteo.com/v1/archive"

all_frames = []

for loc in LOCATIONS:
    params = {
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
        "timezone": "Australia/Sydney"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()

    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()

    hourly_data = {
        "record_date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
    }

    hourly_data["temperature_c"] = hourly_temperature_2m
    hourly_data["relative_humidity"] = hourly_relative_humidity_2m
    hourly_data["wind_speed_kmh"] = hourly_wind_speed_10m
    hourly_data["latitude"] = loc["latitude"]
    hourly_data["longitude"] = loc["longitude"]
    hourly_data["location_name"] = loc["name"]

    df = pd.DataFrame(hourly_data)
    all_frames.append(df)

weather_df = pd.concat(all_frames, ignore_index=True)

output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "victoria_black_summer_weather_raw.csv"
weather_df.to_csv(output_file, index=False)

print(f"Saved raw weather data to: {output_file}")
print(weather_df.head())