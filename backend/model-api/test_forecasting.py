import os
import numpy as np
from dotenv import load_dotenv
from supabase import create_client

from app.internal.services.forecasting_service import ForecastingService


load_dotenv()

FEATURES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]
MODEL_FEATURE_MAPPING = {
    "skin_temperature_c": "skin_temperature_c",
    "soil_temperature_level_1_c": "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards": "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards": "surface_thermal_radiation_downwards",
    "temperature_2m_c": "temperature_2m_c",
    "u_component_of_wind_10m": "u_component_of_wind_10m",
    "v_component_of_wind_10m": "v_component_of_wind_10m",
}


def translate_database_row(row: dict) -> list[float]:
    return [
        float(row[db_column])
        for model_feature, db_column in MODEL_FEATURE_MAPPING.items()
    ]

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

response = (
    supabase
    .table("forecaster_data")
    .select(",".join(["datetime"] + FEATURES))
    .order("datetime", desc=True)
    .limit(60)
    .execute()
)

rows = response.data

if len(rows) < 60:
    raise ValueError(f"Expected at least 60 rows, got {len(rows)}")

# Supabase returns latest first, reverse back into chronological order
rows = list(reversed(rows))

data = np.array(
    [translate_database_row(row) for row in rows],
    dtype=np.float32
)

print("Input shape before batch:", data.shape)

x = np.expand_dims(data, axis=0)

print("Input shape to model:", x.shape)

service = ForecastingService()

forecast = service.predict(x)

print("Forecast shape:", forecast.shape)
print("Next 2 timestep forecast:")
print(forecast)