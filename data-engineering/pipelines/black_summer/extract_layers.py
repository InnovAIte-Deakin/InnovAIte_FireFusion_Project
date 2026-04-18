import geopandas as gpd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_ROOT = os.getenv("DATA_ROOT")

gdb_path = os.path.join(DATA_ROOT, "raw", "Bushfire.gdb")
layer_name = "Bushfire_Boundaries_Historical_V3"

output_folder = os.path.join(DATA_ROOT, "processed")
os.makedirs(output_folder, exist_ok=True)

print("Loading Bushfire dataset...")

gdf = gpd.read_file(
    gdb_path,
    layer=layer_name,
    ignore_geometry=True
)

print("\nColumns:")
print(gdf.columns)

print("\nPreview:")
print(gdf.head())

output_file = os.path.join(output_folder, "bushfire_metadata.csv")

gdf.to_csv(output_file, index=False)

print("\nMetadata saved successfully")