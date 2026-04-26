import pandas as pd
from sqlalchemy import text
from db_connection import get_db_engine

CSV_PATH = "../../data/processed/fire_events.csv"

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

CREATE_INDEXES_SQL = [
    'CREATE INDEX IF NOT EXISTS idx_fire_events_latitude ON "Fire_Events" (latitude);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_longitude ON "Fire_Events" (longitude);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_event_date ON "Fire_Events" (event_date);',
    'CREATE INDEX IF NOT EXISTS idx_fire_events_location_date ON "Fire_Events" (latitude, longitude, event_date);'
]

def load_fire_events():
    engine = get_db_engine()

    df = pd.read_csv(CSV_PATH)

    df["event_id"] = pd.to_numeric(df["event_id"], errors="coerce").astype("Int64")
    df["weather_id"] = pd.to_numeric(df["weather_id"], errors="coerce").astype("Int64")
    df["topo_id"] = pd.to_numeric(df["topo_id"], errors="coerce").astype("Int64")
    df["fuel_id"] = pd.to_numeric(df["fuel_id"], errors="coerce").astype("Int64")
    df["facility_id"] = pd.to_numeric(df["facility_id"], errors="coerce").astype("Int64")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce").dt.date
    df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce").astype("Int64")
    df["source_system"] = df["source_system"].fillna("NASA FIRMS")

    df = df.dropna(subset=["event_id", "latitude", "longitude", "event_date"])

    with engine.begin() as connection:
        connection.execute(text(CREATE_TABLE_SQL))

        connection.execute(text('TRUNCATE TABLE "Fire_Events";'))

        df.to_sql(
            "Fire_Events",
            con=connection,
            if_exists="append",
            index=False,
            method="multi"
        )

        for index_sql in CREATE_INDEXES_SQL:
            connection.execute(text(index_sql))

    print("Fire_Events table loaded successfully.")
    print(f"Rows inserted: {len(df)}")

if __name__ == "__main__":
    load_fire_events()