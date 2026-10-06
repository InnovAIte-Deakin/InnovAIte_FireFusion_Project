"""
FireFusion - Time ID Matching
==============================
Matches fire incident ignition dates to the nearest time_id
in the Time_Registry.

Can be used as a standalone script or imported into other pipelines.

Note: Records with ignition dates before 2018 will have a null time_id
as the Time_Registry only covers from 2018 onwards.
"""

import pandas as pd

TIME_REGISTRY = "time_registry_rows.csv"


def match_time_ids(fire_incidents, time_registry):
    """
    Match each fire incident to a time_id based on ignition date.

    Args:
        fire_incidents (pd.DataFrame): DataFrame with ignition_date column.
        time_registry (str or pd.DataFrame): Path to time_registry CSV or loaded DataFrame.

    Returns:
        pd.DataFrame: fire_incidents with time_id column filled.
    """

    # Load from file if a path string is passed
    if isinstance(time_registry, str):
        print("Loading time registry...")
        time_registry = pd.read_csv(time_registry)
        print(f"Time registry loaded: {len(time_registry)} records")

    # Convert datetime_record to date only for matching
    time_registry['date'] = pd.to_datetime(
        time_registry['datetime_record']
    ).dt.date

    # Get one time_id per unique date (first record of each day)
    daily_time = time_registry.groupby('date').first().reset_index()

    # Convert fire ignition dates to date type
    fire_incidents['ignition_date_only'] = pd.to_datetime(
        fire_incidents['ignition_date'], utc=True
    ).dt.date

    # Match on date
    print("Matching dates to time_id...")
    fire_incidents = fire_incidents.merge(
        daily_time[['date', 'time_id']],
        left_on='ignition_date_only',
        right_on='date',
        how='left'
    )

    # Update time_id column and clean up temp columns
    fire_incidents['time_id'] = fire_incidents['time_id_y'].combine_first(
        fire_incidents['time_id_x']
    )
    fire_incidents = fire_incidents.drop(
        columns=['time_id_x', 'time_id_y', 'date', 'ignition_date_only']
    )

    matched = fire_incidents['time_id'].notna().sum()
    unmatched = fire_incidents['time_id'].isna().sum()
    print(f"Matched: {matched}, Unmatched: {unmatched} (pre-2018 records have no time_id)")

    return fire_incidents


if __name__ == "__main__":
    fire_incidents = pd.read_csv("victoria_fire_incident_record.csv")
    fire_incidents = match_time_ids(fire_incidents, TIME_REGISTRY)
    fire_incidents[['incident_id', 'location_id', 'time_id',
                    'original_latitude', 'original_longitude']].to_csv(
        "victoria_fire_incident_record.csv", index=False
    )
    print("Saved: victoria_fire_incident_record.csv")
