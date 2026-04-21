import pandas as pd
from pathlib import Path

input_file = Path("data/raw/firms_victoria_fire_events_raw.csv")
output_dir = Path("data/cleaned")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "firms_victoria_fire_events_cleaned.csv"

df = pd.read_csv(input_file)

print("Original columns:")
print(df.columns.tolist())

# Adjust these if your FIRMS CSV columns differ slightly
column_map = {
    "latitude": "latitude",
    "longitude": "longitude",
    "acq_date": "event_date",
    "confidence": "confidence_score"
}

df = df.rename(columns=column_map)

required_cols = ["latitude", "longitude", "event_date", "confidence_score"]
df = df[required_cols]

# Clean data
df = df.dropna()
df = df.drop_duplicates()
df["event_date"] = pd.to_datetime(df["event_date"]).dt.date

# Convert confidence score
df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(0).astype(int)

# Add constant source system
df["source_system"] = "NASA FIRMS"

# Add nullable foreign keys for now
df["weather_id"] = None
df["topo_id"] = None
df["fuel_id"] = None
df["facility_id"] = None

# Reorder columns to match architecture
df = df[
    [
        "weather_id",
        "topo_id",
        "fuel_id",
        "facility_id",
        "latitude",
        "longitude",
        "event_date",
        "confidence_score",
        "source_system"
    ]
]

df.to_csv(output_file, index=False)

print(f"Saved cleaned fire events to: {output_file}")
print(df.head())