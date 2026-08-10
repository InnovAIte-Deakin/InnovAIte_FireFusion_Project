import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import BallTree


FACILITY_JSON_FILE = "facilities_fire_risk_google_geocoded.json"
LOCATION_REGISTRY_CSV = "location_registry.csv"

OUTPUT_JSON_FILE = "facilities_fire_risk_with_location_id.json"
OUTPUT_CSV_FILE = "facilities_fire_risk_with_location_id.csv"

EARTH_RADIUS_M = 6371000


def load_facilities(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        data = [data]

    return pd.DataFrame(data)


def save_facilities_json(df, path):
    records = df.replace({np.nan: None}).to_dict(orient="records")

    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def match_to_nearest_grid(facilities_df, location_df):
    # Make sure coordinates are numeric
    facilities_df["latitude"] = pd.to_numeric(
        facilities_df["latitude"], errors="coerce"
    )
    facilities_df["longitude"] = pd.to_numeric(
        facilities_df["longitude"], errors="coerce"
    )

    location_df["grid_latitude"] = pd.to_numeric(
        location_df["grid_latitude"], errors="coerce"
    )
    location_df["grid_longitude"] = pd.to_numeric(
        location_df["grid_longitude"], errors="coerce"
    )

    # Remove invalid grid rows
    location_df = location_df.dropna(
        subset=["grid_latitude", "grid_longitude"]
    ).copy()

    # BallTree with haversine needs radians
    grid_coordinates_rad = np.radians(
        location_df[["grid_latitude", "grid_longitude"]].to_numpy()
    )

    tree = BallTree(grid_coordinates_rad, metric="haversine")

    # Prepare output columns
    facilities_df["location_id"] = None
    facilities_df["matched_grid_latitude"] = None
    facilities_df["matched_grid_longitude"] = None
    facilities_df["distance_to_grid_m"] = None
    facilities_df["grid_match_status"] = "no_facility_lat_lon"

    valid_facilities_mask = facilities_df["latitude"].notna() & facilities_df["longitude"].notna()

    valid_facilities = facilities_df.loc[
        valid_facilities_mask, ["latitude", "longitude"]
    ]

    if valid_facilities.empty:
        print("No facilities with latitude/longitude found.")
        return facilities_df

    facility_coordinates_rad = np.radians(valid_facilities.to_numpy())

    # Query nearest grid point
    distances_rad, indices = tree.query(facility_coordinates_rad, k=1)

    distances_m = distances_rad.flatten() * EARTH_RADIUS_M
    nearest_indices = indices.flatten()

    matched_location_rows = location_df.iloc[nearest_indices].reset_index(drop=True)

    valid_index = facilities_df.loc[valid_facilities_mask].index

    facilities_df.loc[valid_index, "location_id"] = matched_location_rows["location_id"].to_numpy()
    facilities_df.loc[valid_index, "matched_grid_latitude"] = matched_location_rows["grid_latitude"].to_numpy()
    facilities_df.loc[valid_index, "matched_grid_longitude"] = matched_location_rows["grid_longitude"].to_numpy()
    facilities_df.loc[valid_index, "distance_to_grid_m"] = distances_m.round(2)

    # Because your grid is 1km x 1km, nearest-centroid distance should usually be below ~707m.
    # We use 1000m as a safe threshold because address/geocoder coordinates may not be perfect.
    facilities_df.loc[valid_index, "grid_match_status"] = np.where(
        distances_m <= 1000,
        "matched",
        "matched_far_check_needed"
    )

    return facilities_df


def main():
    facilities_df = load_facilities(FACILITY_JSON_FILE)

    location_df = pd.read_csv(LOCATION_REGISTRY_CSV)

    print(f"Facilities loaded: {len(facilities_df)}")
    print(f"Grid locations loaded: {len(location_df)}")

    result_df = match_to_nearest_grid(facilities_df, location_df)

    save_facilities_json(result_df, OUTPUT_JSON_FILE)
    result_df.to_csv(OUTPUT_CSV_FILE, index=False)

    print("Finished matching facilities to location registry.")
    print(f"Output JSON: {OUTPUT_JSON_FILE}")
    print(f"Output CSV: {OUTPUT_CSV_FILE}")

    print()
    print("Match status summary:")
    print(result_df["grid_match_status"].value_counts(dropna=False))


if __name__ == "__main__":
    main()