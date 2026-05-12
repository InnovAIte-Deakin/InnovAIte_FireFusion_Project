import pandas as pd
import numpy as np
from pathlib import Path

from app.internal.services.forecasting_service import ForecastingService


FEATURES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]


csv_path = Path("app/data/forecaster_test_data.csv")

df = pd.read_csv(csv_path)

df["datetime"] = pd.to_datetime(
    df["datetime"],
    dayfirst=True
)
df = df.sort_values("datetime").reset_index(drop=True)

data = df[FEATURES].tail(60).values.astype(np.float32)

print("Input shape before batch:", data.shape)

x = np.expand_dims(data, axis=0)

print("Input shape to model:", x.shape)

service = ForecastingService()

forecast = service.predict(x)

print("Forecast shape:", forecast.shape)
print("Next 2 timestep forecast:")
print(forecast)