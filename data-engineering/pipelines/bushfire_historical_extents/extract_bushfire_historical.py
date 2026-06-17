"""
FireFusion - Bushfire Historical Extents Pipeline
==================================================
Extracts and transforms historical bushfire extent data for Victoria
from the Australian Digital Atlas Geodatabase.

Source: https://digital.atlas.gov.au/datasets/524e2962bd8b4968b8df9f9774345926/about
Author: Joshua Jose
"""

import geopandas as gpd
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from match_location_id import match_location_ids
from match_time_id import match_time_ids


def extract():
    """Load the raw Geodatabase file."""
    print("Loading dataset...")
    gdf = gpd.read_file(
        "Bushfire Extents - Historical (2025).gdb",
        layer="National_Historical_Bushfire_Extents_v4"
    )
    print(f"Total records loaded: {len(gdf)}")
    return gdf


def transform(gdf):
    """Filter to Victoria, extract centroids, and align to Fire_Incident_Record schema."""

    # Filter to Victoria
    print("Filtering to Victoria...")
    vic = gdf[gdf['state'] == 'VIC (Victoria)'].copy()
    print(f"Victorian records: {len(vic)}")

    # Extract lat/lon from geometry centroid (reprojected for accuracy)
    vic_projected = vic.to_crs(epsg=3111)
    centroids = vic_projected.geometry.centroid.to_crs(epsg=4326)
    vic['original_latitude'] = centroids.y
    vic['original_longitude'] = centroids.x

    # Convert ignition date
    vic['ignition_date'] = pd.to_datetime(vic['ignition_date'], utc=True)

    # Add schema columns
    vic['incident_id'] = range(1, len(vic) + 1)
    vic['location_id'] = None
    vic['time_id'] = None

    # Black Summer subset mask
    black_summer_mask = vic['ignition_date'].dt.year.isin([2019, 2020])

    # Select schema columns plus ignition_date (temporarily for time matching)
    fire_incidents = vic[['incident_id', 'location_id', 'time_id',
                           'original_latitude', 'original_longitude',
                           'ignition_date']].copy()

    black_summer = fire_incidents[black_summer_mask.values].copy()
    print(f"Black Summer records (2019-2020): {len(black_summer)}")

    return fire_incidents, black_summer


def load(fire_incidents, black_summer):
    """Save final outputs as CSV."""
    print("Saving files...")
    fire_incidents.to_csv("victoria_fire_incident_record.csv", index=False)
    black_summer.to_csv("victoria_fire_incident_black_summer.csv", index=False)
    print("Done!")
    print("  - victoria_fire_incident_record.csv")
    print("  - victoria_fire_incident_black_summer.csv")


if __name__ == "__main__":
    gdf = extract()
    fire_incidents, black_summer = transform(gdf)

    # Match location IDs
    fire_incidents = match_location_ids(fire_incidents, location_registry="location_registry.csv")
    black_summer = match_location_ids(black_summer, location_registry="location_registry.csv")

    # Match time IDs
    fire_incidents = match_time_ids(fire_incidents, time_registry="time_registry_rows.csv")
    black_summer = match_time_ids(black_summer, time_registry="time_registry_rows.csv")

    # Drop ignition_date before saving (not part of schema)
    fire_incidents = fire_incidents.drop(columns=['ignition_date'])
    black_summer = black_summer.drop(columns=['ignition_date'])

    load(fire_incidents, black_summer)
