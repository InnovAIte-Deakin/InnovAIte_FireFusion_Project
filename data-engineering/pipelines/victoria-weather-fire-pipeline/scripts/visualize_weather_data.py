import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sqlalchemy import create_engine

# Replace with your actual password
DB_URL = "postgresql+psycopg2://postgres:password@localhost:5432/firefusion"

engine = create_engine(DB_URL)

# Read data from PostgreSQL
query = """
SELECT latitude, longitude, record_date, temperature_c, wind_speed_kmh, relative_humidity
FROM Weather_Conditions
ORDER BY record_date;
"""

df = pd.read_sql(query, engine)

# Convert record_date properly
df["record_date"] = pd.to_datetime(df["record_date"])

# Optional: focus on one location first for clean charts
df = df[(df["latitude"] == -37.7) & (df["longitude"] == 148.46)].copy()

# Create output directory
output_dir = Path("visualizations")
output_dir.mkdir(exist_ok=True)

# -----------------------------
# 1. Temperature over time
# -----------------------------
plt.figure(figsize=(12, 5))
plt.plot(df["record_date"], df["temperature_c"])
plt.title("Temperature Over Time - East Gippsland")
plt.xlabel("Date")
plt.ylabel("Temperature (°C)")
plt.tight_layout()
plt.savefig(output_dir / "temperature_over_time.png")
plt.close()

# -----------------------------
# 2. Wind speed over time
# -----------------------------
plt.figure(figsize=(12, 5))
plt.plot(df["record_date"], df["wind_speed_kmh"])
plt.title("Wind Speed Over Time - East Gippsland")
plt.xlabel("Date")
plt.ylabel("Wind Speed (km/h)")
plt.tight_layout()
plt.savefig(output_dir / "wind_speed_over_time.png")
plt.close()

# -----------------------------
# 3. Relative humidity over time
# -----------------------------
plt.figure(figsize=(12, 5))
plt.plot(df["record_date"], df["relative_humidity"])
plt.title("Relative Humidity Over Time - East Gippsland")
plt.xlabel("Date")
plt.ylabel("Relative Humidity (%)")
plt.tight_layout()
plt.savefig(output_dir / "humidity_over_time.png")
plt.close()

# -----------------------------
# 4. Monthly average temperature
# -----------------------------
df["month"] = df["record_date"].dt.to_period("M").astype(str)
monthly_temp = df.groupby("month")["temperature_c"].mean().reset_index()

plt.figure(figsize=(14, 5))
plt.plot(monthly_temp["month"], monthly_temp["temperature_c"])
plt.xticks(rotation=90)
plt.title("Monthly Average Temperature - East Gippsland")
plt.xlabel("Month")
plt.ylabel("Average Temperature (°C)")
plt.tight_layout()
plt.savefig(output_dir / "monthly_avg_temperature.png")
plt.close()

print("Graphs saved in the 'visualizations' folder.")