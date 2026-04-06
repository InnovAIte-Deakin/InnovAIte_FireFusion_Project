SELECT setseed(0.42);

TRUNCATE fire_events, at_risk_infrastructure, fuel_and_vegetation, topography, weather_conditions CASCADE;

INSERT INTO weather_conditions (weather_id, latitude, longitude, record_date, temperature_c, wind_speed_kmh, relative_humidity)
SELECT
    i AS weather_id,
    -(34 + random() * 5)::real AS latitude,           -- Victoria region: -34 to -39
    (140 + random() * 10)::real AS longitude,          -- 140 to 150
    '2023-01-01'::timestamp + (floor(random() * 730) || ' days')::interval
        + (floor(random() * 24) || ' hours')::interval AS record_date,
    (15 + random() * 30)::real AS temperature_c,       -- 15–45°C
    (5 + random() * 80)::real AS wind_speed_kmh,       -- 5–85 km/h
    (5 + random() * 70)::real AS relative_humidity     -- 5–75%
FROM generate_series(1, 50) AS i;

INSERT INTO topography (topo_id, latitude, longitude, elevation_meters, slope_angle)
SELECT
    i AS topo_id,
    -(34 + random() * 5)::real AS latitude,
    (140 + random() * 10)::real AS longitude,
    (50 + random() * 1500)::real AS elevation_meters,  -- 50–1550m
    (random() * 45)::real AS slope_angle               -- 0–45°
FROM generate_series(1, 50) AS i;

INSERT INTO fuel_and_vegetation (fuel_id, latitude, longitude, record_date, vegetation_class, dyrness_index, soil_moisture)
SELECT
    i AS fuel_id,
    -(34 + random() * 5)::real AS latitude,
    (140 + random() * 10)::real AS longitude,
    '2023-01-01'::date + floor(random() * 730)::int AS record_date,
    CASE floor(random() * 5)::int
        WHEN 0 THEN 'Grassland'
        WHEN 1 THEN 'Eucalypt Forest'
        WHEN 2 THEN 'Shrubland'
        WHEN 3 THEN 'Woodland'
        ELSE 'Heathland'
    END AS vegetation_class,
    (random() * 800)::real AS dyrness_index,           -- 0–800
    (random() * 100)::real AS soil_moisture             -- 0–100%
FROM generate_series(1, 50) AS i;

INSERT INTO at_risk_infrastructure (facility_id, facility_name, category, latitude, longitude, lga)
SELECT
    i AS facility_id,
    CASE floor(random() * 5)::int
        WHEN 0 THEN 'Hospital'
        WHEN 1 THEN 'School'
        WHEN 2 THEN 'Aged Care'
        WHEN 3 THEN 'Fire Station'
        ELSE 'Community Centre'
    END || ' ' || chr(65 + (i % 26)::int) || '-' || i AS facility_name,
    CASE floor(random() * 5)::int
        WHEN 0 THEN 'Health'
        WHEN 1 THEN 'Education'
        WHEN 2 THEN 'Aged Care'
        WHEN 3 THEN 'Emergency Services'
        ELSE 'Community'
    END AS category,
    -(34 + random() * 5)::real AS latitude,
    (140 + random() * 10)::real AS longitude,
    CASE floor(random() * 6)::int
        WHEN 0 THEN 'Yarra Ranges'
        WHEN 1 THEN 'East Gippsland'
        WHEN 2 THEN 'Alpine'
        WHEN 3 THEN 'Hepburn'
        WHEN 4 THEN 'Mitchell'
        ELSE 'Wellington'
    END AS lga
FROM generate_series(1, 50) AS i;

INSERT INTO fire_events (event_id, weather_id, topo_id, fuel_id, facility_id, latitude, longitude, event_date, confidence_score, source_system)
SELECT
    i AS event_id,
    floor(random() * 50 + 1)::int AS weather_id,      -- random FK 1–50
    floor(random() * 50 + 1)::int AS topo_id,
    floor(random() * 50 + 1)::int AS fuel_id,
    floor(random() * 50 + 1)::int AS facility_id,
    -(34 + random() * 5)::real AS latitude,
    (140 + random() * 10)::real AS longitude,
    '2023-01-01'::date + floor(random() * 730)::int AS event_date,
    (50 + floor(random() * 51))::int AS confidence_score, -- 50–100
    CASE floor(random() * 3)::int
        WHEN 0 THEN 'MODIS'
        WHEN 1 THEN 'VIIRS'
        ELSE 'Sentinel-2'
    END AS source_system
FROM generate_series(1, 50) AS i;

SELECT 'weather_conditions' AS tbl, count(*) FROM weather_conditions
UNION ALL SELECT 'topography', count(*) FROM topography
UNION ALL SELECT 'fuel_and_vegetation', count(*) FROM fuel_and_vegetation
UNION ALL SELECT 'at_risk_infrastructure', count(*) FROM at_risk_infrastructure
UNION ALL SELECT 'fire_events', count(*) FROM fire_events;
