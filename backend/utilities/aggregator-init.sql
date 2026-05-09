--
-- PostgreSQL database dump
--
-- Dumped from database version 18.1 (Homebrew)
-- Dumped by pg_dump version 18.1 (Homebrew)
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', 'public', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';
SET default_table_access_method = heap;

-- =========================================
-- TABLES
-- =========================================

CREATE TABLE at_risk_infrastructure (
    facility_id   integer NOT NULL,
    facility_name text,
    category      text,
    latitude      real,
    longitude     real,
    lga           text,
    -- Ensure coordinates are valid for Victoria, Australia
    CONSTRAINT chk_infrastructure_lat CHECK (latitude BETWEEN -39.5 AND -34.0),
    CONSTRAINT chk_infrastructure_lon CHECK (longitude BETWEEN 140.0 AND 150.5)
);

CREATE TABLE fire_events (
    event_id         integer NOT NULL,
    weather_id       integer,
    topo_id          integer,
    fuel_id          integer,
    facility_id      integer,
    latitude         real,
    longitude        real,
    event_date       date,
    confidence_score integer,
    source_system    text,
    -- Confidence score must be between 0 and 100
    CONSTRAINT chk_confidence_score CHECK (confidence_score BETWEEN 0 AND 100),
    -- Ensure coordinates are valid for Victoria, Australia
    CONSTRAINT chk_fire_lat CHECK (latitude BETWEEN -39.5 AND -34.0),
    CONSTRAINT chk_fire_lon CHECK (longitude BETWEEN 140.0 AND 150.5)
);

CREATE TABLE fuel_and_vegetation (
    fuel_id          integer NOT NULL,
    latitude         real,
    longitude        real,
    record_date      date,
    vegetation_class text,
    dryness_index    real,
    soil_moisture    real,
    -- Dryness index and soil moisture must be between 0 and 1
    CONSTRAINT chk_dryness_index CHECK (dryness_index BETWEEN 0.0 AND 1.0),
    CONSTRAINT chk_soil_moisture CHECK (soil_moisture BETWEEN 0.0 AND 1.0)
);

CREATE TABLE topography (
    topo_id          integer NOT NULL,
    latitude         real,
    longitude        real,
    elevation_meters real,
    slope_angle      real,
    -- Elevation must be positive, slope between 0 and 90 degrees
    CONSTRAINT chk_elevation CHECK (elevation_meters >= 0),
    CONSTRAINT chk_slope     CHECK (slope_angle BETWEEN 0 AND 90)
);

CREATE TABLE weather_conditions (
    weather_id        integer NOT NULL,
    latitude          real,
    longitude         real,
    record_date       timestamp without time zone,
    temperature_c     real,
    wind_speed_kmh    real,
    relative_humidity real,
    -- Humidity must be between 0 and 100 percent, wind speed must be positive
    CONSTRAINT chk_humidity   CHECK (relative_humidity BETWEEN 0 AND 100),
    CONSTRAINT chk_wind_speed CHECK (wind_speed_kmh >= 0)
);

-- =========================================
-- PRIMARY KEYS
-- =========================================

ALTER TABLE ONLY at_risk_infrastructure
    ADD CONSTRAINT at_risk_infrastructure_pkey PRIMARY KEY (facility_id);

ALTER TABLE ONLY fire_events
    ADD CONSTRAINT fire_events_pkey PRIMARY KEY (event_id);

ALTER TABLE ONLY fuel_and_vegetation
    ADD CONSTRAINT fuel_and_vegetation_pkey PRIMARY KEY (fuel_id);

ALTER TABLE ONLY topography
    ADD CONSTRAINT topography_pkey PRIMARY KEY (topo_id);

ALTER TABLE ONLY weather_conditions
    ADD CONSTRAINT weather_conditions_pkey PRIMARY KEY (weather_id);

-- =========================================
-- FOREIGN KEYS
-- =========================================

ALTER TABLE ONLY fire_events
    ADD CONSTRAINT fire_events_facility_id_fkey FOREIGN KEY (facility_id)
    REFERENCES at_risk_infrastructure(facility_id);

ALTER TABLE ONLY fire_events
    ADD CONSTRAINT fire_events_fuel_id_fkey FOREIGN KEY (fuel_id)
    REFERENCES fuel_and_vegetation(fuel_id);

ALTER TABLE ONLY fire_events
    ADD CONSTRAINT fire_events_topo_id_fkey FOREIGN KEY (topo_id)
    REFERENCES topography(topo_id);

ALTER TABLE ONLY fire_events
    ADD CONSTRAINT fire_events_weather_id_fkey FOREIGN KEY (weather_id)
    REFERENCES weather_conditions(weather_id);

-- =========================================
-- VIEW
-- =========================================

CREATE VIEW fire_events_full AS
SELECT
    fire_events.event_id,
    fire_events.latitude,
    fire_events.longitude,
    fire_events.event_date,
    fire_events.confidence_score,
    weather_conditions.temperature_c,
    weather_conditions.wind_speed_kmh,
    weather_conditions.relative_humidity,
    topography.elevation_meters,
    topography.slope_angle,
    fuel_and_vegetation.vegetation_class,
    fuel_and_vegetation.dryness_index,
    fuel_and_vegetation.soil_moisture,
    at_risk_infrastructure.facility_name,
    at_risk_infrastructure.category
FROM fire_events
LEFT JOIN weather_conditions     ON fire_events.weather_id  = weather_conditions.weather_id
LEFT JOIN topography             ON fire_events.topo_id     = topography.topo_id
LEFT JOIN fuel_and_vegetation    ON fire_events.fuel_id     = fuel_and_vegetation.fuel_id
LEFT JOIN at_risk_infrastructure ON fire_events.facility_id = at_risk_infrastructure.facility_id;

-- =========================================
-- MOCK DATA
-- Sample rows for testing. Victorian locations.
-- Represents realistic bushfire-risk scenarios.
-- =========================================

-- At-risk infrastructure across Victoria
INSERT INTO at_risk_infrastructure (facility_id, facility_name, category, latitude, longitude, lga) VALUES
(1, 'Kyneton Hospital',           'Health',                  -37.2447, 144.4561, 'Macedon Ranges'),
(2, 'Traralgon Power Substation', 'Energy',                  -38.1954, 146.5401, 'Latrobe City'),
(3, 'Maryborough Primary School', 'Education',               -37.0557, 143.7334, 'Central Goldfields'),
(4, 'Wangaratta Aged Care',       'Vulnerable Population',   -36.3583, 146.3058, 'Rural City of Wangaratta'),
(5, 'Corryong Water Treatment',   'Critical Infrastructure', -36.1933, 147.9021, 'Towong'),
(6, 'Ballarat Base Hospital',     'Health',                  -37.5622, 143.8503, 'City of Ballarat'),
(7, 'Bendigo Electricity Depot',  'Energy',                  -36.7570, 144.2794, 'City of Greater Bendigo');

-- Weather conditions during high fire-risk periods
INSERT INTO weather_conditions (weather_id, latitude, longitude, record_date, temperature_c, wind_speed_kmh, relative_humidity) VALUES
(1, -37.2447, 144.4561, '2024-01-15 09:00:00', 38.5, 45.2, 12.0),
(2, -38.1954, 146.5401, '2024-01-15 09:00:00', 41.2, 60.8,  8.5),
(3, -37.0557, 143.7334, '2024-02-10 08:30:00', 35.0, 30.0, 20.0),
(4, -36.3583, 146.3058, '2024-02-10 08:30:00', 33.7, 22.5, 25.0),
(5, -36.1933, 147.9021, '2024-03-05 10:00:00', 29.4, 18.0, 30.5),
(6, -37.5622, 143.8503, '2024-01-20 11:00:00', 42.1, 55.0,  7.0),
(7, -36.7570, 144.2794, '2024-01-20 11:00:00', 39.8, 48.3,  9.5);

-- Topography data from ELVIS elevation datasets
INSERT INTO topography (topo_id, latitude, longitude, elevation_meters, slope_angle) VALUES
(1, -37.2447, 144.4561, 420.0,  5.2),
(2, -38.1954, 146.5401, 185.0,  3.1),
(3, -37.0557, 143.7334, 230.0,  6.4),
(4, -36.3583, 146.3058, 310.0,  8.7),
(5, -36.1933, 147.9021, 560.0, 12.3),
(6, -37.5622, 143.8503, 435.0,  4.8),
(7, -36.7570, 144.2794, 225.0,  3.9);

-- Vegetation and fuel conditions from satellite data
INSERT INTO fuel_and_vegetation (fuel_id, latitude, longitude, record_date, vegetation_class, dryness_index, soil_moisture) VALUES
(1, -37.2447, 144.4561, '2024-01-15', 'Dry Sclerophyll Forest', 0.82, 0.11),
(2, -38.1954, 146.5401, '2024-01-15', 'Wet Sclerophyll Forest', 0.45, 0.38),
(3, -37.0557, 143.7334, '2024-02-10', 'Mallee Scrub',           0.91, 0.07),
(4, -36.3583, 146.3058, '2024-02-10', 'Grassland',              0.60, 0.22),
(5, -36.1933, 147.9021, '2024-03-05', 'Riparian Woodland',      0.55, 0.30),
(6, -37.5622, 143.8503, '2024-01-20', 'Dry Sclerophyll Forest', 0.88, 0.08),
(7, -36.7570, 144.2794, '2024-01-20', 'Grassland',              0.78, 0.13);

-- Fire events linking all tables together
INSERT INTO fire_events (event_id, weather_id, topo_id, fuel_id, facility_id, latitude, longitude, event_date, confidence_score, source_system) VALUES
(1, 1, 1, 1, 1, -37.2447, 144.4561, '2024-01-15', 85, 'NASA FIRMS'),
(2, 2, 2, 2, 2, -38.1954, 146.5401, '2024-01-15', 92, 'NASA FIRMS'),
(3, 3, 3, 3, 3, -37.0557, 143.7334, '2024-02-10', 78, 'NASA FIRMS'),
(4, 4, 4, 4, 4, -36.3583, 146.3058, '2024-02-10', 65, 'NASA FIRMS'),
(5, 5, 5, 5, 5, -36.1933, 147.9021, '2024-03-05', 71, 'NASA FIRMS'),
(6, 6, 6, 6, 6, -37.5622, 143.8503, '2024-01-20', 88, 'NASA FIRMS'),
(7, 7, 7, 7, 7, -36.7570, 144.2794, '2024-01-20', 76, 'NASA FIRMS');

-- =========================================
-- PERFORMANCE INDEXES
-- Speeds up queries across all tables
-- =========================================

-- fire_events: indexes on all foreign keys and date
CREATE INDEX idx_fire_events_weather_id  ON fire_events(weather_id);
CREATE INDEX idx_fire_events_topo_id     ON fire_events(topo_id);
CREATE INDEX idx_fire_events_fuel_id     ON fire_events(fuel_id);
CREATE INDEX idx_fire_events_facility_id ON fire_events(facility_id);
CREATE INDEX idx_fire_events_event_date  ON fire_events(event_date);

-- weather_conditions: index on date and location for time-based queries
CREATE INDEX idx_weather_record_date     ON weather_conditions(record_date);
CREATE INDEX idx_weather_lat_lon         ON weather_conditions(latitude, longitude);

-- fuel_and_vegetation: index on date and vegetation class for filtering
CREATE INDEX idx_fuel_record_date        ON fuel_and_vegetation(record_date);
CREATE INDEX idx_fuel_vegetation_class   ON fuel_and_vegetation(vegetation_class);

-- topography: index on location for spatial lookups
CREATE INDEX idx_topo_lat_lon            ON topography(latitude, longitude);

-- at_risk_infrastructure: index on category for filtering by type
CREATE INDEX idx_infrastructure_category ON at_risk_infrastructure(category);
CREATE INDEX idx_infrastructure_lga      ON at_risk_infrastructure(lga);