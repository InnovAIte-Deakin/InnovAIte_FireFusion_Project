import os
from io import StringIO
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import text

from db_connection import get_db_engine


# Bounding boxes use: west,south,east,north
AUSTRALIA_BBOX = "112.0,-44.0,154.0,-10.0"
VICTORIA_BBOX = "140.9,-39.2,150.0,-33.9"

DEFAULT_SOURCE = "VIIRS_SNPP_NRT"
DEFAULT_DAY_RANGE = 1

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "Fire_Events" (
    event_id INTEGER PRIMARY KEY,
    weather_id INTEGER NULL,
    topo_id INTEGER NULL,
    fuel_id INTEGER NULL,
    facility_id INTEGER NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    event_date DATE NOT NULL,
    confidence_score INTEGER,
    source_system VARCHAR(100) NOT NULL
);
"""


CREATE_UNIQUE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_fire_events_realtime
ON "Fire_Events" (latitude, longitude, event_date, confidence_score, source_system);
"""


CREATE_PERFORMANCE_INDEXES_SQL = [
    'CREATE INDEX IF NOT EXISTS idx_fire_events_latitude ON "Fire_Events" (latitude);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_longitude ON "Fire_Events" (longitude);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_event_date ON "Fire_Events" (event_date);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_location_date ON "Fire_Events" (latitude, longitude, event_date);'
]


def fetch_firms_live_data(
    area_coordinates: str = VICTORIA_BBOX,
    source: str = DEFAULT_SOURCE,
    day_range: int = DEFAULT_DAY_RANGE
) -> pd.DataFrame:
    load_dotenv()

    map_key = os.getenv("FIRMS_MAP_KEY")

    if not map_key:
        raise ValueError("FIRMS_MAP_KEY is missing. Please add it to your .env file.")

    if day_range < 1 or day_range > 5:
        raise ValueError("NASA FIRMS day_range must be between 1 and 5.")

    url = f"{BASE_URL}/{map_key}/{source}/{area_coordinates}/{day_range}"

    print(f"Fetching live FIRMS data from source: {source}")
    print(f"Area: {area_coordinates}")
    print(f"Day range: {day_range}")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    if not response.text.strip():
        print("No data returned from NASA FIRMS.")
        return pd.DataFrame()

    df = pd.read_csv(StringIO(response.text))

    print(f"Rows fetched from FIRMS: {len(df)}")

    return df


def transform_live_firms_data(
    df: pd.DataFrame,
    source: str = DEFAULT_SOURCE
) -> pd.DataFrame:
    output_columns = [
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

    if df.empty:
        return pd.DataFrame(columns=output_columns)

    required_columns = ["latitude", "longitude", "acq_date", "confidence"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required FIRMS columns: {missing_columns}")

    df = df.copy()

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["event_date"] = pd.to_datetime(df["acq_date"], errors="coerce").dt.date

    confidence_mapping = {
        "l": 30,
        "low": 30,
        "n": 60,
        "nominal": 60,
        "h": 90,
        "high": 90
    }

    df["confidence_score"] = (
        df["confidence"]
        .astype(str)
        .str.lower()
        .map(confidence_mapping)
        .fillna(pd.to_numeric(df["confidence"], errors="coerce"))
    )

    fire_df = pd.DataFrame()

    fire_df["weather_id"] = pd.Series([None] * len(df), dtype="Int64")
    fire_df["topo_id"] = pd.Series([None] * len(df), dtype="Int64")
    fire_df["fuel_id"] = pd.Series([None] * len(df), dtype="Int64")
    fire_df["facility_id"] = pd.Series([None] * len(df), dtype="Int64")

    fire_df["latitude"] = df["latitude"]
    fire_df["longitude"] = df["longitude"]
    fire_df["event_date"] = df["event_date"]
    fire_df["confidence_score"] = pd.to_numeric(
        df["confidence_score"],
        errors="coerce"
    ).astype("Int64")

    fire_df["source_system"] = f"NASA FIRMS {source}"

    fire_df = fire_df.dropna(
        subset=["latitude", "longitude", "event_date", "confidence_score"]
    )

    fire_df = fire_df[output_columns]

    # Remove duplicate rows inside the API response before loading.
    fire_df = fire_df.drop_duplicates(
        subset=[
            "latitude",
            "longitude",
            "event_date",
            "confidence_score",
            "source_system"
        ]
    )

    print(f"Rows after transformation: {len(fire_df)}")

    return fire_df


def insert_live_fire_events(fire_df: pd.DataFrame) -> None:
    if fire_df.empty:
        print("No records to insert.")
        return

    engine = get_db_engine()

    with engine.begin() as connection:
        connection.execute(text(CREATE_TABLE_SQL))

        # Remove duplicate records already in the table so the unique index can be created.
        deduplicate_sql = """
        DELETE FROM "Fire_Events" a
        USING "Fire_Events" b
        WHERE a.event_id > b.event_id
        AND a.latitude = b.latitude
        AND a.longitude = b.longitude
        AND a.event_date = b.event_date
        AND COALESCE(a.confidence_score, -1) = COALESCE(b.confidence_score, -1)
        AND a.source_system = b.source_system;
        """

        connection.execute(text(deduplicate_sql))

        connection.execute(text(CREATE_UNIQUE_INDEX_SQL))

        for index_sql in CREATE_PERFORMANCE_INDEXES_SQL:
            connection.execute(text(index_sql))

        staging_table = "fire_events_staging"

        fire_df.to_sql(
            staging_table,
            con=connection,
            if_exists="replace",
            index=False,
            method="multi"
        )

        insert_sql = """
        INSERT INTO "Fire_Events" (
            event_id,
            weather_id,
            topo_id,
            fuel_id,
            facility_id,
            latitude,
            longitude,
            event_date,
            confidence_score,
            source_system
        )
        SELECT
            (
                SELECT COALESCE(MAX(event_id), 0)
                FROM "Fire_Events"
            ) + ROW_NUMBER() OVER () AS event_id,
            NULL::INTEGER AS weather_id,
            NULL::INTEGER AS topo_id,
            NULL::INTEGER AS fuel_id,
            NULL::INTEGER AS facility_id,
            latitude,
            longitude,
            event_date,
            confidence_score,
            source_system
        FROM fire_events_staging
        ON CONFLICT (
            latitude,
            longitude,
            event_date,
            confidence_score,
            source_system
        )
        DO NOTHING;
        """

        connection.execute(text(insert_sql))
        connection.execute(text("DROP TABLE IF EXISTS fire_events_staging;"))

    print("Live FIRMS data inserted into PostgreSQL successfully.")


def run_realtime_ingestion(
    area_coordinates: str = VICTORIA_BBOX,
    source: str = DEFAULT_SOURCE,
    day_range: int = DEFAULT_DAY_RANGE
) -> None:
    print("=" * 60)
    print("Starting NASA FIRMS real-time ingestion")
    print(f"Run time UTC: {datetime.now(timezone.utc)}")
    print("=" * 60)

    raw_df = fetch_firms_live_data(
        area_coordinates=area_coordinates,
        source=source,
        day_range=day_range
    )

    fire_df = transform_live_firms_data(
        raw_df,
        source=source
    )

    insert_live_fire_events(fire_df)

    print("=" * 60)
    print("NASA FIRMS real-time ingestion completed")
    print("=" * 60)


if __name__ == "__main__":
    run_realtime_ingestion(
        area_coordinates=VICTORIA_BBOX,
        source=DEFAULT_SOURCE,
        day_range=1
    )