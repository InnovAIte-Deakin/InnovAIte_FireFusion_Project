import geopandas as gpd
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_ROOT = os.getenv("DATA_ROOT")

gpd.options.io_engine = "pyogrio"

gdb_path = os.path.join(DATA_ROOT, "raw", "Bushfire.gdb")
layer_name = "Bushfire_Boundaries_Historical_V3"

filtered_csv = os.path.join(DATA_ROOT, "processed", "black_summer.csv")
output_path = os.path.join(DATA_ROOT, "processed", "black_summer.geojson")

print("Loading filtered fire IDs...")
df = pd.read_csv(filtered_csv)

fire_ids = set(df['fire_id'].dropna())

print("Total filtered fire IDs:", len(fire_ids))

print("\nLoading dataset in chunks...")

chunk_size = 5000
start = 0
final_gdf = []

while True:
    print(f"Processing rows {start} to {start + chunk_size}...")

    chunk = gpd.read_file(
        gdb_path,
        layer=layer_name,
        rows=slice(start, start + chunk_size)
    )

    if chunk.empty:
        break

    filtered_chunk = chunk[chunk['fire_id'].isin(fire_ids)]
    final_gdf.append(filtered_chunk)

    start += chunk_size

print("\nCombining filtered chunks...")

result = gpd.GeoDataFrame(pd.concat(final_gdf, ignore_index=True))

print("Final rows:", len(result))

print("\nSaving GeoJSON...")

result.to_file(output_path, driver="GeoJSON")

print("\nBlack Summer GeoJSON created successfully")