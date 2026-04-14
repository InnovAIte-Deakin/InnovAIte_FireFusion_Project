import pandas as pd
from sqlalchemy import create_engine, text
from math import sqrt

# Replace with your real password
DB_URL = "postgresql+psycopg2://postgres:password@localhost:5432/firefusion"

engine = create_engine(DB_URL)

# -----------------------------
# Load Fire_Events
# -----------------------------
fire_query = """
SELECT event_id, latitude, longitude, event_date
FROM Fire_Events
WHERE weather_id IS NULL
ORDER BY event_date;
"""

fire_df = pd.read_sql(fire_query, engine)

# -----------------------------
# Load Weather_Conditions
# -----------------------------
weather_query = """
SELECT weather_id, latitude, longitude, record_date
FROM Weather_Conditions
ORDER BY record_date;
"""

weather_df = pd.read_sql(weather_query, engine)

# Convert datetime/date fields
fire_df["event_date"] = pd.to_datetime(fire_df["event_date"]).dt.date
weather_df["record_date"] = pd.to_datetime(weather_df["record_date"])
weather_df["weather_date"] = weather_df["record_date"].dt.date

# -----------------------------
# Matching logic
# -----------------------------
matches = []

for _, fire_row in fire_df.iterrows():
    fire_lat = fire_row["latitude"]
    fire_lon = fire_row["longitude"]
    fire_date = fire_row["event_date"]

    # Keep only same-day weather rows
    same_day_weather = weather_df[weather_df["weather_date"] == fire_date].copy()

    if same_day_weather.empty:
        continue

    # Compute simple distance
    same_day_weather["distance"] = same_day_weather.apply(
        lambda row: sqrt((row["latitude"] - fire_lat) ** 2 + (row["longitude"] - fire_lon) ** 2),
        axis=1
    )

    # Pick nearest weather row
    best_match = same_day_weather.sort_values(by="distance").iloc[0]

    matches.append({
        "event_id": fire_row["event_id"],
        "weather_id": int(best_match["weather_id"])
    })

matches_df = pd.DataFrame(matches)

print("Matched rows:")
print(matches_df.head())
print(f"Total matches created: {len(matches_df)}")

# Save matches for evidence
matches_df.to_csv("data/validated/fire_weather_matches.csv", index=False)

# -----------------------------
# Update Fire_Events table
# -----------------------------
with engine.begin() as connection:
    for _, match_row in matches_df.iterrows():
        connection.execute(
            text("""
                UPDATE Fire_Events
                SET weather_id = :weather_id
                WHERE event_id = :event_id
            """),
            {
                "weather_id": int(match_row["weather_id"]),
                "event_id": int(match_row["event_id"])
            }
        )

print("Fire_Events.weather_id updated successfully.")