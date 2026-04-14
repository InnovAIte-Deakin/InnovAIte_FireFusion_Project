import pandas as pd
from pathlib import Path

input_file = Path("data/raw/victoria_black_summer_weather_raw.csv")
output_dir = Path("data/cleaned")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "victoria_black_summer_weather_cleaned.csv"

df = pd.read_csv(input_file)

# Keep only columns needed by Weather_Conditions schema
df = df[[
    "latitude",
    "longitude",
    "record_date",
    "temperature_c",
    "wind_speed_kmh",
    "relative_humidity"
]]

# Clean data
df = df.dropna()
df = df.drop_duplicates()
df["record_date"] = pd.to_datetime(df["record_date"])

# Ensure correct types
df["latitude"] = df["latitude"].astype(float)
df["longitude"] = df["longitude"].astype(float)
df["temperature_c"] = df["temperature_c"].astype(float)
df["wind_speed_kmh"] = df["wind_speed_kmh"].astype(float)
df["relative_humidity"] = df["relative_humidity"].astype(float)

df.to_csv(output_file, index=False)

print(f"Saved cleaned weather data to: {output_file}")
print(df.head())