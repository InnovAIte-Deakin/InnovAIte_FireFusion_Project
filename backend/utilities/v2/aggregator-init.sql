--
-- PostgreSQL database dump
--
-- Dumped from database version 18.1 (Homebrew)
-- Dumped by pg_dump version 18.1 (Homebrew)

-- FireFusion database setup
-- This file creates the tables used by the backend.
-- The table names and relationships match the data engineering schema data-engineering\architecture\database_architecture.md

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

-- Remove old objects/tables first so the script can run cleanly again.
-- Remove old objects/tables first so the script can run cleanly again.
DROP VIEW IF EXISTS fire_event_full;

DROP TABLE IF EXISTS Weather_Observation CASCADE;
DROP TABLE IF EXISTS Fire_Incident_Record CASCADE;
DROP TABLE IF EXISTS Vegetation_Condition CASCADE;
DROP TABLE IF EXISTS Topography_Profile CASCADE;
DROP TABLE IF EXISTS Infrastructure_Asset CASCADE;
DROP TABLE IF EXISTS Time_Registry CASCADE;
DROP TABLE IF EXISTS Location_Registry CASCADE;


-- Shared location table.
-- Stores the standard location used by multiple observations.
CREATE TABLE Location_Registry (
    location_id INTEGER PRIMARY KEY,
    grid_latitude REAL,
    grid_longitude REAL,
    region_name TEXT
);

-- Shared time table.
-- Stores the standard time values used by observation tables.
CREATE TABLE Time_Registry (
    time_id INTEGER PRIMARY KEY,
    datetime_record TIMESTAMP,
    season TEXT
);

-- Weather data for a location and time.
CREATE TABLE Weather_Observation (
    weather_id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL, -- Foreign Key Location_Registry
    time_id INTEGER NOT NULL, -- Foreign Key Time_Registry
    original_latitude REAL,
    original_longitude REAL,
    temperature_c REAL,
    wind_speed_kmh REAL,
    relative_humidity REAL,
    source_system TEXT,
    CONSTRAINT weather_observation_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id),
    CONSTRAINT weather_observation_time_id_fkey
        FOREIGN KEY (time_id) REFERENCES Time_Registry(time_id)
);

-- Fire incident data for a location and time.
CREATE TABLE Fire_Incident_Record (
    incident_id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL, -- Foreign Key Location_Registry
    time_id INTEGER NOT NULL, -- Foreign Key Time_Registry
    original_latitude REAL,
    original_longitude REAL,
    confidence_score INTEGER,
    source_system TEXT,
    CONSTRAINT fire_incident_record_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id),
    CONSTRAINT fire_incident_record_time_id_fkey
        FOREIGN KEY (time_id) REFERENCES Time_Registry(time_id)
);

-- Vegetation data for a location and time.
CREATE TABLE Vegetation_Condition (
    veg_condition_id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL, -- Foreign Key Location_Registry
    time_id INTEGER NOT NULL, -- Foreign Key Time_Registry
    original_latitude REAL,
    original_longitude REAL,
    vegetation_class TEXT,
    dryness_index REAL,
    soil_moisture REAL,
    source_system TEXT,
    CONSTRAINT vegetation_condition_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id),
    CONSTRAINT vegetation_condition_time_id_fkey
        FOREIGN KEY (time_id) REFERENCES Time_Registry(time_id)
);

-- Static topography data for a location.
CREATE TABLE Topography_Profile (
    topo_id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL, -- Foreign Key Location_Registry
    original_latitude REAL,
    original_longitude REAL,
    elevation_meters REAL,
    slope_angle REAL,
    CONSTRAINT topography_profile_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id)
);

-- Static infrastructure data for a location.
CREATE TABLE Infrastructure_Asset (
    asset_id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL, -- Foreign Key Location_Registry
    original_latitude REAL,
    original_longitude REAL,
    facility_name TEXT,
    risk_category TEXT,
    CONSTRAINT infrastructure_asset_location_id_fkey
        FOREIGN KEY (location_id) REFERENCES Location_Registry(location_id)
);


-- Consolidated view for backend/API use.
-- Flattens the normalised tables into one easier result.
CREATE VIEW fire_event_full AS
SELECT
    fir.incident_id,
    fir.location_id,
    fir.time_id,
    fir.original_latitude AS fire_original_latitude,
    fir.original_longitude AS fire_original_longitude,
    lr.grid_latitude,
    lr.grid_longitude,
    lr.region_name,
    tr.datetime_record,
    tr.season,
    wo.weather_id,
    wo.original_latitude AS weather_original_latitude,
    wo.original_longitude AS weather_original_longitude,
    vc.veg_condition_id,
    vc.original_latitude AS vegetation_original_latitude,
    vc.original_longitude AS vegetation_original_longitude,
    tp.topo_id,
    tp.original_latitude AS topography_original_latitude,
    tp.original_longitude AS topography_original_longitude,
    ia.asset_id,
    ia.original_latitude AS infrastructure_original_latitude,
    ia.original_longitude AS infrastructure_original_longitude
FROM Fire_Incident_Record fir
LEFT JOIN Location_Registry lr
    ON fir.location_id = lr.location_id
LEFT JOIN Time_Registry tr
    ON fir.time_id = tr.time_id
LEFT JOIN Weather_Observation wo
    ON fir.location_id = wo.location_id
   AND fir.time_id = wo.time_id
LEFT JOIN Vegetation_Condition vc
    ON fir.location_id = vc.location_id
   AND fir.time_id = vc.time_id
LEFT JOIN Topography_Profile tp
    ON fir.location_id = tp.location_id
LEFT JOIN Infrastructure_Asset ia
    ON fir.location_id = ia.location_id;