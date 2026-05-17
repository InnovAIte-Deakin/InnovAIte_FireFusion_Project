import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_HOST = os.getenv("SUPABASE_HOST")
DB_PORT = os.getenv("SUPABASE_PORT")
DB_NAME = os.getenv("SUPABASE_DB")
DB_USER = os.getenv("SUPABASE_USER")
DB_PASSWORD = os.getenv("SUPABASE_PASSWORD")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)

print("Supabase PostgreSQL connection created")