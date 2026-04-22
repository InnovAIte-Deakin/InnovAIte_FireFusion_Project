CREATE TABLE IF NOT EXISTS Weather_Conditions (
    weather_id SERIAL PRIMARY KEY,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    record_date TIMESTAMP NOT NULL,
    temperature_c FLOAT,
    wind_speed_kmh FLOAT,
    relative_humidity FLOAT
);