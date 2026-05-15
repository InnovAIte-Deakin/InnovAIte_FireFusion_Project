"""
FireFusion - Vic Emergency Bushfire Realtime Pipeline by Thai Ha NGUYEN
========================================================

Pipeline steps
--------------
1. Fetch and extract bushfire/fire incident data from Vic Emergency.
2. Validate the Supabase target table schema.
3. Check duplicates against vic_emercency_bushfire_incident_realtime.
4. Add FireFusion location_id by snapping each incident coordinate to the
   nearest EXISTING approved grid row in public.location_registry.
   Approved grid range: location_id 1 to 463807 only.
5. Insert new records into Supabase.

Important change in v4
----------------------
This version does NOT use Dhruv's GridSnapper class because that tool can create
new location_registry rows when a snapped coordinate does not already exist.
For the realtime Vic Emergency pipeline, location_registry should be treated as
our source of truth. Therefore, this pipeline only reads from location_registry
and assigns the nearest existing approved location_id.

This version also restricts all grid snapping queries to the original registry
range: location_id BETWEEN 1 AND 463807. It will not use any later rows that may
have been accidentally created by previous snapping tests.

Required .env variables
-----------------------
DB_HOST=...
DB_PORT=5432
DB_NAME=postgres
DB_USER=...
DB_PASSWORD=...

Optional .env variables
-----------------------
MAX_SNAP_DISTANCE_KM=20
DEBUG_LOCATION_MATCHES=false
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://emergency.vic.gov.au/public/events-geojson.json"
TABLE_SCHEMA = "public"
TABLE_NAME = "vic_emercency_bushfire_incident_realtime"
FULL_TABLE_NAME = f"{TABLE_SCHEMA}.{TABLE_NAME}"
LOCATION_REGISTRY_TABLE = "public.location_registry"

# Only use the approved/original location_registry range.
# This prevents the pipeline from using rows accidentally created after the
# original grid load, for example by an older GridSnapper implementation.
LOCATION_ID_MIN = 1
LOCATION_ID_MAX = 463807

BUSHFIRE_CATEGORIES = {"Fire", "Planned Burn", "Bushfire"}

# Victoria bounding box used only as a quick sanity check.
# Final location_id assignment is based on the nearest existing location_registry row.
VICTORIA_BOUNDS = {
    "lat_min": -39.2,
    "lat_max": -34.0,
    "lon_min": 140.96,
    "lon_max": 150.0,
}

# Search progressively wider windows around the incident coordinate.
# This avoids scanning the full location_registry table for every record.
SEARCH_WINDOWS_DEG = (0.02, 0.05, 0.1, 0.25, 0.5, 1.0)

MAX_SNAP_DISTANCE_KM = float(os.getenv("MAX_SNAP_DISTANCE_KM", "20"))
DEBUG_LOCATION_MATCHES = os.getenv("DEBUG_LOCATION_MATCHES", "false").lower() == "true"

INSERT_COLUMNS = [
    "id",
    "feed_type",
    "category1",
    "category2",
    "status",
    "name",
    "action",
    "location",
    "created",
    "updated",
    "size",
    "source_org",
    "source_title",
    "latitude",
    "longitude",
    "location_id",
]


def get_db_connection():
    """Create a PostgreSQL/Supabase connection using .env credentials."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def parse_vic_timestamp(value: Optional[str]):
    """
    Convert Vic Emergency timestamp strings into Python datetime objects.

    Vic Emergency can provide 7 fractional second digits, while Python datetime
    supports microseconds with 6 digits. This trims the extra digit safely.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip().replace("Z", "+00:00")
    text = re.sub(r"(\.\d{6})\d+", r"\1", text)

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        # Let PostgreSQL attempt to parse it if Python cannot.
        return value


def extract_point(geometry: Optional[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract latitude and longitude from Vic Emergency GeoJSON geometry.

    Supports:
    - Point
    - GeometryCollection containing a Point
    """
    if not geometry:
        return None, None

    if geometry.get("type") == "Point":
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) >= 2:
            lon, lat = coordinates[:2]
            return float(lat), float(lon)

    if geometry.get("type") == "GeometryCollection":
        for item in geometry.get("geometries", []):
            if item.get("type") == "Point":
                coordinates = item.get("coordinates") or []
                if len(coordinates) >= 2:
                    lon, lat = coordinates[:2]
                    return float(lat), float(lon)

    return None, None


def fetch_vic_emergency() -> Dict[str, Any]:
    """Fetch realtime incidents from Vic Emergency public GeoJSON endpoint."""
    response = requests.get(
        API_URL,
        headers={"User-Agent": "Mozilla/5.0 FireFusion-DE-Pipeline"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def is_bushfire_incident(record: Dict[str, Any]) -> bool:
    """Return True if the record is an incident and belongs to fire-related categories."""
    feed_type = (record.get("feed_type") or "").lower()
    if feed_type != "incident":
        return False

    return (
        record.get("category1") in BUSHFIRE_CATEGORIES
        or record.get("category2") in BUSHFIRE_CATEGORIES
    )


def normalise_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    """Convert one Vic Emergency GeoJSON feature into the Supabase table format."""
    props = feature.get("properties", {})
    latitude, longitude = extract_point(feature.get("geometry"))

    incident_id = props.get("id")
    if incident_id is not None:
        incident_id = str(incident_id)

    return {
        "id": incident_id,
        "feed_type": props.get("feedType"),
        "category1": props.get("category1"),
        "category2": props.get("category2"),
        "status": props.get("status"),
        "name": props.get("name"),
        "action": props.get("action"),
        "location": props.get("location"),
        "created": parse_vic_timestamp(props.get("created")),
        "updated": parse_vic_timestamp(props.get("updated")),
        "size": props.get("sizeFmt"),
        "source_org": props.get("sourceOrg"),
        "source_title": props.get("sourceTitle"),
        "latitude": latitude,
        "longitude": longitude,
        "location_id": None,
    }


def extract_bushfire_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and filter Vic Emergency bushfire/fire incident records."""
    records: List[Dict[str, Any]] = []

    for feature in data.get("features", []):
        record = normalise_feature(feature)

        if not record.get("id"):
            continue

        if is_bushfire_incident(record):
            records.append(record)

    records.sort(key=lambda x: x.get("created") or datetime.min, reverse=True)
    return records


def validate_target_schema(conn) -> None:
    """Validate required target table and location_registry columns before insert."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = 'id'
            """,
            (TABLE_SCHEMA, TABLE_NAME),
        )
        row = cursor.fetchone()

    if not row:
        raise RuntimeError(
            f"Cannot find column '{FULL_TABLE_NAME}.id'. Check the table name/schema."
        )

    id_type = row[0]
    if id_type not in {"character varying", "text"}:
        raise RuntimeError(
            "Schema mismatch: Vic Emergency incident IDs are strings, but "
            f"{FULL_TABLE_NAME}.id is currently {id_type}.\n\n"
            "Fix in Supabase SQL editor:\n"
            f"ALTER TABLE {FULL_TABLE_NAME}\n"
            "ALTER COLUMN id TYPE character varying USING id::character varying;"
        )

    required_registry_columns = {"location_id", "grid_latitude", "grid_longitude"}
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'location_registry'
              AND column_name = ANY(%s)
            """,
            (list(required_registry_columns),),
        )
        found_columns = {row[0] for row in cursor.fetchall()}

    missing = required_registry_columns - found_columns
    if missing:
        raise RuntimeError(
            "location_registry is missing required column(s): "
            + ", ".join(sorted(missing))
        )

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {LOCATION_REGISTRY_TABLE}
            WHERE location_id BETWEEN %s AND %s
            """,
            (LOCATION_ID_MIN, LOCATION_ID_MAX),
        )
        approved_count = cursor.fetchone()[0]

    if approved_count == 0:
        raise RuntimeError(
            "No approved location_registry rows found. Expected existing rows with "
            f"location_id between {LOCATION_ID_MIN} and {LOCATION_ID_MAX}."
        )


def get_existing_ids(conn, record_ids: Iterable[str]) -> set:
    """Check which Vic Emergency IDs already exist in Supabase."""
    ids = [str(record_id) for record_id in record_ids if record_id]
    if not ids:
        return set()

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id::text
            FROM {FULL_TABLE_NAME}
            WHERE id::text = ANY(%s::text[])
            """,
            (ids,),
        )
        return {row[0] for row in cursor.fetchall()}


def is_valid_victoria(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """Quick coordinate sanity check for Victoria bounding box."""
    if latitude is None or longitude is None:
        return False

    return (
        VICTORIA_BOUNDS["lat_min"] <= latitude <= VICTORIA_BOUNDS["lat_max"]
        and VICTORIA_BOUNDS["lon_min"] <= longitude <= VICTORIA_BOUNDS["lon_max"]
    )


def find_nearest_location_id(conn, latitude: Optional[float], longitude: Optional[float]) -> Optional[int]:
    """
    Find the nearest approved existing location_id from public.location_registry.

    This function does not create new location_registry rows. It progressively
    searches wider bounding boxes, then assigns the nearest existing grid point
    from location_id 1 to 463807 only.
    Distance is approximated in kilometres, which is accurate enough for snapping
    incidents to a Victorian grid.
    """
    if not is_valid_victoria(latitude, longitude):
        print(f"⚠️  No location_id: ({latitude}, {longitude}) is missing or outside Victoria bounds")
        return None

    nearest = None

    with conn.cursor() as cursor:
        for window in SEARCH_WINDOWS_DEG:
            cursor.execute(
                f"""
                SELECT
                    location_id,
                    grid_latitude,
                    grid_longitude,
                    SQRT(
                        POWER((grid_latitude - %s) * 111.32, 2) +
                        POWER((grid_longitude - %s) * 111.32 * COS(RADIANS(%s)), 2)
                    ) AS distance_km
                FROM {LOCATION_REGISTRY_TABLE}
                WHERE location_id BETWEEN %s AND %s
                  AND grid_latitude BETWEEN %s AND %s
                  AND grid_longitude BETWEEN %s AND %s
                ORDER BY distance_km ASC, location_id ASC
                LIMIT 1
                """,
                (
                    latitude,
                    longitude,
                    latitude,
                    LOCATION_ID_MIN,
                    LOCATION_ID_MAX,
                    latitude - window,
                    latitude + window,
                    longitude - window,
                    longitude + window,
                ),
            )
            nearest = cursor.fetchone()
            if nearest:
                break

        # Fallback: if no candidates are found in nearby windows, search the whole registry.
        # This should rarely happen if location_registry covers Victoria.
        if not nearest:
            cursor.execute(
                f"""
                SELECT
                    location_id,
                    grid_latitude,
                    grid_longitude,
                    SQRT(
                        POWER((grid_latitude - %s) * 111.32, 2) +
                        POWER((grid_longitude - %s) * 111.32 * COS(RADIANS(%s)), 2)
                    ) AS distance_km
                FROM {LOCATION_REGISTRY_TABLE}
                WHERE location_id BETWEEN %s AND %s
                ORDER BY distance_km ASC, location_id ASC
                LIMIT 1
                """,
                (latitude, longitude, latitude, LOCATION_ID_MIN, LOCATION_ID_MAX),
            )
            nearest = cursor.fetchone()

    if not nearest:
        print("⚠️  No location_id: no approved location_registry row found in location_id range 1-463807")
        return None

    location_id, grid_lat, grid_lon, distance_km = nearest

    if distance_km is not None and distance_km > MAX_SNAP_DISTANCE_KM:
        print(
            "⚠️  No location_id: nearest registry cell is too far "
            f"({distance_km:.2f} km > {MAX_SNAP_DISTANCE_KM:.2f} km) "
            f"for coordinate ({latitude}, {longitude})"
        )
        return None

    if DEBUG_LOCATION_MATCHES:
        print(
            f"Matched ({latitude}, {longitude}) -> location_id={location_id} "
            f"grid=({grid_lat}, {grid_lon}) distance={distance_km:.3f} km"
        )

    return int(location_id)


def add_location_ids_from_registry(conn, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
    """Add location_id to each record using nearest approved existing location_registry row."""
    matched = 0
    unmatched = 0

    for record in records:
        location_id = find_nearest_location_id(
            conn,
            record.get("latitude"),
            record.get("longitude"),
        )
        record["location_id"] = location_id

        if location_id is None:
            unmatched += 1
        else:
            matched += 1

    return records, matched, unmatched


def insert_new_records(conn, records: List[Dict[str, Any]]) -> int:
    """Insert new records into Supabase with ON CONFLICT protection."""
    if not records:
        return 0

    values = [tuple(record.get(column) for column in INSERT_COLUMNS) for record in records]
    column_sql = ", ".join(INSERT_COLUMNS)

    query = f"""
        INSERT INTO {FULL_TABLE_NAME} ({column_sql})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        RETURNING id
    """

    with conn.cursor() as cursor:
        inserted_rows = execute_values(cursor, query, values, fetch=True)

    conn.commit()
    return len(inserted_rows)


def run_pipeline() -> Dict[str, int]:
    """Run the full Vic Emergency realtime bushfire incident pipeline."""
    conn = None

    try:
        print("Step 1: Fetching data from Vic Emergency...")
        raw_data = fetch_vic_emergency()
        records = extract_bushfire_records(raw_data)
        print(f"Extracted bushfire/fire incident records: {len(records)}")

        print("Step 2: Connecting to Supabase and validating schemas...")
        conn = get_db_connection()
        validate_target_schema(conn)

        print("Step 3: Checking duplicates in Supabase...")
        existing_ids = get_existing_ids(conn, [record["id"] for record in records])
        new_records = [record for record in records if str(record["id"]) not in existing_ids]
        duplicates_skipped = len(records) - len(new_records)
        print(f"Existing records skipped: {duplicates_skipped}")
        print(f"New records to insert: {len(new_records)}")

        print("Step 4: Adding location_id from approved location_registry rows 1-463807...")
        new_records, matched_locations, unmatched_locations = add_location_ids_from_registry(
            conn,
            new_records,
        )
        print(f"location_id matched: {matched_locations}")
        print(f"location_id unmatched/null: {unmatched_locations}")

        print("Step 5: Inserting new records into Supabase...")
        inserted_count = insert_new_records(conn, new_records)
        print(f"Inserted records: {inserted_count}")

        return {
            "fetched_filtered_records": len(records),
            "duplicates_skipped": duplicates_skipped,
            "new_records_after_duplicate_check": len(new_records),
            "location_id_matched": matched_locations,
            "location_id_unmatched": unmatched_locations,
            "inserted_records": inserted_count,
        }

    except Exception as error:
        if conn:
            conn.rollback()
        print(f"Pipeline failed: {error}")
        raise

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    summary = run_pipeline()
    print("Pipeline summary:", summary)
