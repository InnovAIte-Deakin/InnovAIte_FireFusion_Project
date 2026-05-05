CREATE TABLE IF NOT EXISTS Fire_Events (
    event_id SERIAL PRIMARY KEY,
    weather_id INTEGER NULL,
    topo_id INTEGER NULL,
    fuel_id INTEGER NULL,
    facility_id INTEGER NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    event_date DATE NOT NULL,
    confidence_score INTEGER,
    source_system VARCHAR(100) NOT NULL
);