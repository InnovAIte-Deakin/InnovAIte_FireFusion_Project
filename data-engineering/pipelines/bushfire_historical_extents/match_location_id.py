"""
FireFusion - Location ID Matching
==================================
Matches fire incident coordinates to the nearest grid point
in the Location_Registry using a KD-tree spatial index.

Can be used as a standalone script or imported into other pipelines.
"""

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

LOCATION_REGISTRY = "location_registry.csv"


def match_location_ids(fire_incidents, location_registry):
    """
    Match each fire incident to the nearest location_id in the Location_Registry.

    Args:
        fire_incidents (pd.DataFrame): DataFrame with original_latitude and original_longitude columns.
        location_registry (str or pd.DataFrame): Path to location_registry CSV or loaded DataFrame.

    Returns:
        pd.DataFrame: fire_incidents with location_id column filled.
    """

    # Load from file if a path string is passed
    if isinstance(location_registry, str):
        print("Loading location registry...")
        location_registry = pd.read_csv(location_registry)
        print(f"Location registry loaded: {len(location_registry)} records")

    # Build KD-tree index from grid coordinates
    print("Building location index...")
    grid_coords_rad = np.radians(
        location_registry[['grid_latitude', 'grid_longitude']].values
    )
    tree = cKDTree(grid_coords_rad)

    # Find nearest grid point for each fire centroid
    print("Matching coordinates to location_id...")
    fire_coords_rad = np.radians(
        fire_incidents[['original_latitude', 'original_longitude']].values
    )
    _, indices = tree.query(fire_coords_rad)

    fire_incidents = fire_incidents.copy()
    fire_incidents['location_id'] = location_registry.iloc[indices]['location_id'].values

    print(f"Matching complete! {fire_incidents['location_id'].notna().sum()} records matched.")
    return fire_incidents


if __name__ == "__main__":
    fire_incidents, location_registry = (
        pd.read_csv("victoria_fire_incident_record.csv"),
        pd.read_csv(LOCATION_REGISTRY)
    )
    fire_incidents = match_location_ids(fire_incidents, location_registry)
    fire_incidents[['incident_id', 'location_id', 'time_id',
                    'original_latitude', 'original_longitude']].to_csv(
        "victoria_fire_incident_record.csv", index=False
    )
    print("Saved: victoria_fire_incident_record.csv")
