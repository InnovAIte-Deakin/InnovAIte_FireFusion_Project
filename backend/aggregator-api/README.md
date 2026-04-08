# Aggregator API

# Requirements

- Python 3.x
- PostgreSQL

# Setup

1. Create a virtual environment and activate it:
python3 -m venv venv
source venv/bin/activate

2. Install dependencies:
pip install fastapi uvicorn python-dotenv

3. Create a PostgreSQL database:
psql postgres
CREATE DATABASE aggregator;
\q

4. Create the items table:
psql aggregator
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR
);
\q

3. Create a `.env` file with your API key:

API_KEY=your-secret-key-here
DATABASE_URL=postgresql://your-username@localhost:5432/aggregator


# Running

uvicorn app.main:app --reload

# Testing

Add an `X-API-Key` header to all requests, or use the Swagger UI at `http://127.0.0.1:8000/docs`


