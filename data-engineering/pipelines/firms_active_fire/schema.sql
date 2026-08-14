-- =====================================================================
-- FireFusion Data Pipeline — Schema (Fire-Only Scope)
-- Hub and Spoke Spatial-Temporal Architecture
-- Tables: Location_Registry, Time_Registry, Fire_Incident_Record
-- (Weather, Vegetation, Topography, Infrastructure intentionally excluded)
-- =====================================================================

DROP TABLE IF EXISTS Fire_Incident_Record CASCADE;
DROP TABLE IF EXISTS Location_Registry CASCADE;
DROP TABLE IF EXISTS Time_Registry CASCADE;

-- ---------------------------------------------------------------------
-- HUB: Location_Registry
-- Universal spatial grid. All observation tables snap to this grid
-- so different sources stack on identical coordinates.
-- ---------------------------------------------------------------------
CREATE TABLE Location_Registry (
    location_id     SERIAL PRIMARY KEY,
    grid_latitude    DOUBLE PRECISION NOT NULL,
    grid_longitude   DOUBLE PRECISION NOT NULL,
    region_name      VARCHAR(255),
    CONSTRAINT uq_location_grid UNIQUE (grid_latitude, grid_longitude)
);

CREATE INDEX idx_location_grid_coords ON Location_Registry (grid_latitude, grid_longitude);

-- ---------------------------------------------------------------------
-- HUB: Time_Registry
-- Universal calendar. All observation tables snap to this grid
-- so timestamps from different sources align exactly.
-- ---------------------------------------------------------------------
CREATE TABLE Time_Registry (
    time_id          SERIAL PRIMARY KEY,
    datetime_record  TIMESTAMPTZ NOT NULL UNIQUE,
    season           VARCHAR(20)
);

CREATE INDEX idx_time_datetime ON Time_Registry (datetime_record);

-- ---------------------------------------------------------------------
-- SPOKE: Fire_Incident_Record
-- Covers BOTH:
--   (a) Active Fire Records — NASA FIRMS satellite hotspots (daily batch)
--   (b) Historical Fire Records — GeoScience Australia / CFA (one-time bulk)
-- distinguished by the `source` and `record_type` columns below.
-- Strict lineage rule: original_latitude / original_longitude are the
-- untouched, un-snapped coordinates as received from the source API.
-- ---------------------------------------------------------------------
CREATE TABLE Fire_Incident_Record (
    incident_id        SERIAL PRIMARY KEY,
    location_id         INTEGER NOT NULL REFERENCES Location_Registry(location_id),
    time_id              INTEGER NOT NULL REFERENCES Time_Registry(time_id),
    original_latitude    DOUBLE PRECISION NOT NULL,
    original_longitude   DOUBLE PRECISION NOT NULL,

    -- Distinguishes pipeline A (historical) vs pipeline B (active/live)
    record_type          VARCHAR(20) NOT NULL CHECK (record_type IN ('HISTORICAL', 'ACTIVE')),
    source                VARCHAR(50) NOT NULL,          -- e.g. 'NASA_FIRMS', 'GEOSCIENCE_AU', 'CFA'

    -- NASA FIRMS-specific satellite hotspot attributes
    satellite             VARCHAR(20),                    -- e.g. 'VIIRS_NOAA20', 'MODIS_Aqua'
    instrument             VARCHAR(20),                    -- e.g. 'VIIRS', 'MODIS'
    acq_date               DATE,
    acq_time                VARCHAR(4),                    -- FIRMS format HHMM (UTC), stored raw
    brightness_ti4          DOUBLE PRECISION,                -- brightness temp channel (Kelvin)
    brightness_ti5           DOUBLE PRECISION,
    frp                       DOUBLE PRECISION,                -- Fire Radiative Power (MW) — intensity proxy
    scan                      DOUBLE PRECISION,                -- pixel size along scan (km)
    track                      DOUBLE PRECISION,                -- pixel size along track (km)
    confidence                 VARCHAR(10),                    -- 'low' / 'nominal' / 'high' (VIIRS) or 0-100 (MODIS)
    daynight                    CHAR(1),                        -- 'D' or 'N'
    version                      VARCHAR(20),

    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_firms_pixel UNIQUE (original_latitude, original_longitude, acq_date, acq_time, satellite)
);

CREATE INDEX idx_fire_location ON Fire_Incident_Record (location_id);
CREATE INDEX idx_fire_time ON Fire_Incident_Record (time_id);
CREATE INDEX idx_fire_acq_date ON Fire_Incident_Record (acq_date);
CREATE INDEX idx_fire_record_type ON Fire_Incident_Record (record_type);

-- ---------------------------------------------------------------------
-- SUPPORT: Pipeline_Run_Log
-- Audit trail for every pipeline execution (manual or scheduled).
-- Lets the team see run history, catch silent failures, and track
-- which satellite sources were pulled per run without digging through
-- console output or GitHub Actions logs.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Pipeline_Run_Log (
    run_id           SERIAL PRIMARY KEY,
    pipeline_name     VARCHAR(50) NOT NULL,        -- e.g. 'firms_active_fire'
    started_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    status               VARCHAR(20) NOT NULL DEFAULT 'RUNNING', -- RUNNING / SUCCESS / FAILED / PARTIAL
    sources_attempted     TEXT,                       -- comma-separated, e.g. 'VIIRS_SNPP_NRT,MODIS_NRT'
    sources_succeeded      TEXT,
    rows_fetched              INTEGER DEFAULT 0,
    rows_inserted              INTEGER DEFAULT 0,
    rows_skipped                INTEGER DEFAULT 0,
    error_message                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_log_pipeline ON Pipeline_Run_Log (pipeline_name, started_at);
