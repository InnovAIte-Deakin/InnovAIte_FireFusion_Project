CREATE TABLE bushfire_black_summer (
    fire_id TEXT,
    fire_name TEXT,
    ignition_date DATE,
    capture_date DATE,
    extinguish_date DATE,
    fire_type TEXT,
    ignition_cause TEXT,
    area_ha FLOAT,
    perim_km FLOAT,
    state TEXT,
    agency TEXT,
    geometry GEOMETRY(MULTIPOLYGON, 4326)
);