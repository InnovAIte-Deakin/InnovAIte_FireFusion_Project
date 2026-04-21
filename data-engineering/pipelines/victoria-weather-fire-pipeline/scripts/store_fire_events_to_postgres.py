import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

input_file = Path("data/cleaned/firms_victoria_fire_events_cleaned.csv")
df = pd.read_csv(input_file)

# Replace with your actual postgres password
db_url = "postgresql+psycopg2://postgres:password@localhost:5432/firefusion"

engine = create_engine(db_url)

df.to_sql("fire_events", engine, if_exists="append", index=False)

print("Fire events stored successfully in PostgreSQL table: Fire_Events")
print(df.head())