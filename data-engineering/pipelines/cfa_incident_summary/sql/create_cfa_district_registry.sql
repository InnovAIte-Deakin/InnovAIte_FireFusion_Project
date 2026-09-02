-- CFA District Registry (static dimension — Workflow A historical load)
-- Links CFA administrative districts to Location_Registry for hub-and-spoke joins.

CREATE TABLE IF NOT EXISTS CFA_District_Registry (
    district_no INTEGER PRIMARY KEY,
    cfa_region TEXT NOT NULL,
    headquarters_name TEXT,
    location_id INTEGER NOT NULL,
    reference_latitude REAL NOT NULL,
    reference_longitude REAL NOT NULL,
    source TEXT,
    CONSTRAINT cfa_district_registry_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id)
);

CREATE INDEX IF NOT EXISTS idx_cfa_district_registry_location_id
    ON CFA_District_Registry(location_id);
