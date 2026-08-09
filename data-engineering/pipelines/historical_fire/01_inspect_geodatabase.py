from pathlib import Path
import pyogrio
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GDB_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Bushfire_Boundaries_Historical"
    / "Bushfire_Boundaries_Historical.gdb"
)

print("=" * 60)
print("GEOSCIENCE AUSTRALIA HISTORICAL FIRE DATA INSPECTION")
print("=" * 60)

# Check that the geodatabase exists
if not GDB_PATH.exists():
    raise FileNotFoundError(f"Geodatabase not found: {GDB_PATH}")

# List all layers inside the geodatabase
layers = pyogrio.list_layers(GDB_PATH)

print("\nAvailable layers:")
for layer in layers:
    print(layer)

# Read the first available layer
layer_name = layers[0][0]

print(f"\nInspecting layer: {layer_name}")

gdf = gpd.read_file(
    GDB_PATH,
    layer=layer_name,
    rows=10
)

print("\nColumns:")
for column in gdf.columns:
    print(f"- {column}")

print("\nCoordinate Reference System:")
print(gdf.crs)

print("\nGeometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\nSample records:")
print(gdf.head().to_string())

print("\nInspection completed successfully.")