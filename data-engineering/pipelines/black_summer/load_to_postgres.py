import os
import geopandas as gpd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATA_ROOT = os.getenv("DATA_ROOT")

os.environ["OGR_GEOJSON_MAX_OBJ_SIZE"] = "0"
gpd.options.io_engine = "fiona"

file = os.path.join(DATA_ROOT, "processed", "black_summer.geojson")

print("Loading GeoJSON...")
gdf = gpd.read_file(file)

gdf = gdf.rename_geometry("geom")

print("Connecting to PostgreSQL...")

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

print("Dropping existing table...")

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS bushfire_black_summer;"))

print("Uploading in chunks...")

chunk_size = 100

for i in range(0, len(gdf), chunk_size):
    print(f"Processing chunk {i} to {i+chunk_size}")

    chunk = gdf.iloc[i:i+chunk_size].copy()
    chunk = chunk.to_crs(epsg=4326)

    if i == 0:
        chunk.to_postgis(
            "bushfire_black_summer",
            engine,
            if_exists="replace",
            index=False
        )
    else:
        chunk.to_postgis(
            "bushfire_black_summer",
            engine,
            if_exists="append",
            index=False
        )

print("Data successfully loaded into PostgreSQL")