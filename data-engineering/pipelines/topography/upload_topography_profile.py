import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from grid_snapper import GridSnapper

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

csv_path = r"C:\Users\bansa\InnovAIte_FireFusion_Project\data-engineering\data\topography_data.csv"

print("CSV path:", os.path.abspath(csv_path))
print("CSV exists:", os.path.exists(csv_path))
print("URL found:", bool(SUPABASE_URL))
print("KEY found:", bool(SUPABASE_KEY))

df = pd.read_csv(csv_path)

required_columns = [
    "latitude",
    "longitude",
    "elevation_meters",
    "slope_angle"
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df = df.dropna(subset=required_columns)
df = df.drop_duplicates(subset=["latitude", "longitude"])

records = []

snapper = GridSnapper()

try:
    for _, row in df.iterrows():
        location_id = snapper.get_location_id(
            float(row["latitude"]),
            float(row["longitude"])
        )

        if location_id is None:
            print(f"Skipping outside/invalid location: {row['latitude']}, {row['longitude']}")
            continue

        records.append({
            "location_id": location_id,
            "original_latitude": float(row["latitude"]),
            "original_longitude": float(row["longitude"]),
            "elevation_meters": float(row["elevation_meters"]),
            "slope_angle": float(row["slope_angle"])
        })
finally:
    snapper.close()

print(f"Prepared {len(records)} records before location_id deduplication")

deduped = {}

for record in records:
    deduped[record["location_id"]] = record

records = list(deduped.values())

print(f"Prepared {len(records)} unique location records for upload to topography_profile")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Supabase API details not found. Upload skipped.")
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    batch_size = 1000
    uploaded_count = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        supabase.table("topography_profile").upsert(
            batch,
            on_conflict="location_id"
        ).execute()

        uploaded_count += len(batch)
        print(f"Uploaded batch {i // batch_size + 1}: {len(batch)} records")

    print("Upload completed successfully")
    print(f"Uploaded/updated {uploaded_count} records")