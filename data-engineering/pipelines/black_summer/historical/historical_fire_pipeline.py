import pandas as pd
import geopandas as gpd
import os
from dotenv import load_dotenv

# =========================
# LOAD ENV VARIABLES
# =========================

load_dotenv()

DATA_ROOT = os.getenv("DATA_ROOT")

# =========================
# LOAD BLACK SUMMER CSV
# =========================

csv_file = os.path.join(
    DATA_ROOT,
    "processed",
    "black_summer.csv"
)

print("Loading Black Summer dataset...")

df = pd.read_csv(csv_file)

# Show columns
print("\nCSV Columns:")
print(df.columns)

# Preview CSV
print("\nCSV Preview:")
print(df.head())

# =========================
# LOAD GEOJSON
# =========================

geo_file = os.path.join(
    DATA_ROOT,
    "processed",
    "black_summer.geojson"
)

print("\nLoading GeoJSON...")

gdf = gpd.read_file(geo_file)

# Preview GeoJSON
print("\nGeoJSON Preview:")
print(gdf.head())

# =========================
# EXTRACT CENTROID COORDINATES
# =========================

print("\nExtracting centroid coordinates...")

# Convert polygons to center points
gdf['latitude'] = gdf.geometry.centroid.y
gdf['longitude'] = gdf.geometry.centroid.x

# Preview coordinates
print("\nCoordinates Preview:")
print(gdf[['latitude', 'longitude']].head())

# =========================
# GRID SNAPPING
# =========================

print("\nApplying grid snapping...")

gdf['grid_latitude'] = gdf['latitude'].round(2)
gdf['grid_longitude'] = gdf['longitude'].round(2)

# Preview snapped grid
print("\nGrid Snapped Coordinates:")
print(
    gdf[
        [
            'latitude',
            'longitude',
            'grid_latitude',
            'grid_longitude'
        ]
    ].head()
)

# =========================
# CREATE LOCATION REGISTRY
# =========================

print("\nCreating location registry...")

locations = gdf[
    [
        'grid_latitude',
        'grid_longitude'
    ]
].drop_duplicates()

print("\nLocation Registry Preview:")
print(locations.head())

print("\nTotal Unique Locations:")
print(len(locations))

# =========================
# DATE PROCESSING
# =========================

print("\nProcessing ignition dates...")

gdf['ignition_date'] = pd.to_datetime(
    gdf['ignition_date'],
    errors='coerce'
)

# =========================
# CREATE SEASON FUNCTION
# =========================

def get_season(month):

    if month in [12, 1, 2]:
        return "Summer"

    elif month in [3, 4, 5]:
        return "Autumn"

    elif month in [6, 7, 8]:
        return "Winter"

    else:
        return "Spring"

# =========================
# CREATE TIME REGISTRY
# =========================

print("\nCreating time registry...")

time_df = gdf[
    ['ignition_date']
].drop_duplicates()

time_df['season'] = time_df[
    'ignition_date'
].dt.month.apply(get_season)

time_df.rename(
    columns={
        'ignition_date': 'datetime_record'
    },
    inplace=True
)

print("\nTime Registry Preview:")
print(time_df.head())

print("\nTotal Unique Time Records:")
print(len(time_df))

# =========================
# SAVE PROCESSED FILES
# =========================

output_location = os.path.join(
    DATA_ROOT,
    "processed",
    "location_registry.csv"
)

output_time = os.path.join(
    DATA_ROOT,
    "processed",
    "time_registry.csv"
)

locations.to_csv(output_location, index=False)

time_df.to_csv(output_time, index=False)

print("\nLocation registry saved")
print("Time registry saved")

print("\nSprint 2 Spatial-Temporal preprocessing complete")