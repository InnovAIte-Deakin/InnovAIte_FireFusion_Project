import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

input_file = Path("data/cleaned/victoria_black_summer_weather_cleaned.csv")
df = pd.read_csv(input_file)

# Replace YOUR_PASSWORD with your actual postgres password
db_url = "postgresql+psycopg2://postgres:password@localhost:5432/firefusion"

engine = create_engine(db_url)

# Store only schema-aligned columns
df = df[[
    "latitude",
    "longitude",
    "record_date",
    "temperature_c",
    "wind_speed_kmh",
    "relative_humidity"
]]

df.to_sql("weather_conditions", engine, if_exists="append", index=False)

print("Weather data stored successfully in PostgreSQL table: Weather_Conditions")
print(df.head())