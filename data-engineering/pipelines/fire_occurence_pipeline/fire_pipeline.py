import pandas as pd
import os
from sqlalchemy import create_engine
from scipy.spatial import cKDTree
from dotenv import load_dotenv

# -------------------------
# EXTRACT
# -------------------------
def extract():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(
        BASE_DIR,
        "..",
        "data",
        "fire_data_2024_2025_cleaned.csv"
    )

    df = pd.read_csv(file_path)

    print(f"[EXTRACT] Loaded data: {df.shape}")
    return df


# -------------------------
# TRANSFORM
# -------------------------
def transform(df):
    print("[TRANSFORM] Cleaning data...")

    # Keep required columns
    df = df[[
        'latitude',
        'longitude',
        'acq_date',
        'confidence',
        'brightness',
        'frp',
        'fire_occurred'
    ]]

    # Rename columns
    df = df.rename(columns={
        'latitude': 'lat',
        'longitude': 'lon',
        'acq_date': 'event_time',
        'brightness': 'fire_brightness',
        'frp': 'fire_radiative_power'
    })

    # Convert datetime
    df['event_time'] = pd.to_datetime(
        df['event_time'],
        errors='coerce'
    )

    # Remove invalid timestamps
    df = df.dropna(subset=['event_time'])

    # -------------------------
    # CONNECT TO SUPABASE
    # -------------------------
    load_dotenv()

    db_url = (
        f"postgresql://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}?sslmode=require"
    )

    engine = create_engine(db_url)

    # -------------------------
    # LOAD LOCATION REGISTRY
    # -------------------------
    registry_df = pd.read_sql(
        "SELECT * FROM location_registry",
        engine
    )

    print(registry_df.columns)
    print(registry_df.head(10))

    # -------------------------
    # KDTree Spatial Mapping
    # -------------------------
    registry_coords = registry_df[
        ['grid_latitude', 'grid_longitude']
    ].values

    tree = cKDTree(registry_coords)

    fire_coords = df[['lat', 'lon']].values

    distances, indices = tree.query(fire_coords)

    # Assign nearest location_id
    df['location_id'] = (
        registry_df.iloc[indices]['location_id'].values
    )

    # Check null mappings
    print(df['location_id'].isnull().sum())

    # -------------------------
    # FINAL FACT TABLE SCHEMA
    # -------------------------
    df = df[[
        'location_id',
        'event_time',
        'confidence',
        'fire_brightness',
        'fire_radiative_power',
        'fire_occurred'
    ]]

    # Remove duplicates
    df = df.drop_duplicates()

    print(f"[TRANSFORM] Cleaned data: {df.shape}")

    return df


# -------------------------
# LOAD (SUPABASE)
# -------------------------
def load(df):
    print("[LOAD] Connecting to database...")

    load_dotenv()

    db_url = (
        f"postgresql://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}?sslmode=require"
    )

    engine = create_engine(db_url)

    chunk_size = 5000

    for start in range(0, len(df), chunk_size):

        end = start + chunk_size

        chunk = df.iloc[start:end]

        chunk.to_sql(
            "fire_occurrence",
            engine,
            if_exists="append",
            index=False
        )

        print(f"[LOAD] Uploaded rows {start} to {end}")

    print("[LOAD] Data uploaded to Supabase!")


# -------------------------
# RUN PIPELINE
# -------------------------
def run_pipeline():

    print("🚀 Running pipeline...")

    df = extract()

    

    df = transform(df)

    print(df.head())
    print(df.shape)

    # TEMPORARILY DISABLED
    load(df)

    print("✅ Pipeline completed")


if __name__ == "__main__":
    run_pipeline()