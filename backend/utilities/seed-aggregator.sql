-- Seed data for bushfire risk database

INSERT INTO topography (topo_id, latitude, longitude, elevation_meters, slope_angle) VALUES
(1, -37.81, 144.96, 31.0, 2.5),
(2, -37.68, 145.73, 520.0, 18.3),
(3, -37.75, 145.14, 120.0, 8.7),
(4, -38.15, 146.43, 85.0, 5.1),
(5, -36.76, 144.28, 225.0, 12.4),
(6, -37.05, 145.95, 680.0, 22.6),
(7, -38.34, 145.18, 45.0, 3.2),
(8, -36.36, 146.32, 310.0, 15.8),
(9, -37.56, 143.85, 440.0, 19.1),
(10, -38.68, 146.05, 60.0, 4.6);

INSERT INTO weather_conditions (weather_id, latitude, longitude, record_date, temperature_c, wind_speed_kmh, relative_humidity) VALUES
(1, -37.68, 145.73, '2025-01-15 14:00:00', 42.3, 65.0, 8.0),
(2, -37.75, 145.14, '2025-01-15 13:30:00', 39.8, 48.0, 12.5),
(3, -36.76, 144.28, '2025-02-03 15:00:00', 44.1, 72.0, 6.0),
(4, -37.05, 145.95, '2025-02-03 14:00:00', 38.5, 55.0, 10.2),
(5, -38.34, 145.18, '2025-01-28 12:00:00', 36.2, 40.0, 18.0),
(6, -36.36, 146.32, '2025-02-10 14:30:00', 41.0, 68.0, 7.5),
(7, -37.56, 143.85, '2025-12-20 13:00:00', 40.7, 58.0, 9.8),
(8, -38.68, 146.05, '2025-01-05 11:00:00', 33.0, 30.0, 22.0),
(9, -37.68, 145.73, '2025-02-14 15:00:00', 43.6, 80.0, 5.5),
(10, -37.81, 144.96, '2025-03-01 14:00:00', 37.0, 35.0, 15.0);

INSERT INTO fuel_and_vegetation (fuel_id, latitude, longitude, record_date, vegetation_class, dryness_index, soil_moisture) VALUES
(1, -37.68, 145.73, '2025-01-10', 'Wet Sclerophyll Forest', 8.5, 0.08),
(2, -37.75, 145.14, '2025-01-10', 'Dry Sclerophyll Forest', 7.2, 0.12),
(3, -36.76, 144.28, '2025-02-01', 'Grassland', 9.1, 0.05),
(4, -37.05, 145.95, '2025-02-01', 'Alpine Ash Forest', 6.8, 0.15),
(5, -38.34, 145.18, '2025-01-25', 'Heathland', 7.9, 0.10),
(6, -36.36, 146.32, '2025-02-08', 'Dry Sclerophyll Forest', 8.8, 0.06),
(7, -37.56, 143.85, '2025-12-18', 'Grassy Woodland', 8.0, 0.09),
(8, -38.68, 146.05, '2025-01-03', 'Wet Sclerophyll Forest', 5.5, 0.20),
(9, -37.68, 145.73, '2025-02-12', 'Wet Sclerophyll Forest', 9.0, 0.06),
(10, -37.81, 144.96, '2025-02-28', 'Urban Grassland', 6.0, 0.14);

INSERT INTO at_risk_infrastructure (facility_id, facility_name, category, latitude, longitude, lga) VALUES
(1, 'Healesville Primary School', 'School', -37.65, 145.52, 'Yarra Ranges'),
(2, 'Upper Yarra Reservoir', 'Water Supply', -37.68, 145.92, 'Yarra Ranges'),
(3, 'Bendigo Hospital', 'Hospital', -36.76, 144.28, 'Greater Bendigo'),
(4, 'Mt Buller Alpine Village', 'Tourism', -37.15, 146.44, 'Mansfield'),
(5, 'Mornington Community Centre', 'Community Facility', -38.22, 145.04, 'Mornington Peninsula'),
(6, 'Wangaratta Substation', 'Power Infrastructure', -36.36, 146.31, 'Wangaratta'),
(7, 'Ballarat Aged Care Home', 'Aged Care', -37.56, 143.86, 'Ballarat'),
(8, 'Warragul CFA Station', 'Emergency Services', -38.16, 145.93, 'Baw Baw'),
(9, 'Yarra Glen Kindergarten', 'Childcare', -37.66, 145.37, 'Yarra Ranges'),
(10, 'Lilydale Rail Hub', 'Transport', -37.76, 145.35, 'Yarra Ranges');

INSERT INTO fire_events (event_id, weather_id, topo_id, fuel_id, facility_id, latitude, longitude, event_date, confidence_score, source_system) VALUES
(1, 1, 2, 1, 1, -37.67, 145.70, '2025-01-15', 92, 'MODIS'),
(2, 2, 3, 2, NULL, -37.74, 145.12, '2025-01-15', 78, 'VIIRS'),
(3, 3, 5, 3, 3, -36.77, 144.30, '2025-02-03', 95, 'MODIS'),
(4, 4, 6, 4, 4, -37.06, 145.96, '2025-02-03', 85, 'VIIRS'),
(5, 5, 7, 5, 5, -38.33, 145.17, '2025-01-28', 60, 'Sentinel-2'),
(6, 6, 8, 6, 6, -36.35, 146.33, '2025-02-10', 91, 'MODIS'),
(7, 7, 9, 7, 7, -37.55, 143.84, '2025-12-20', 88, 'VIIRS'),
(8, 8, 10, 8, NULL, -38.67, 146.04, '2025-01-05', 55, 'Sentinel-2'),
(9, 9, 2, 9, 2, -37.69, 145.74, '2025-02-14', 97, 'MODIS'),
(10, 10, 1, 10, 10, -37.80, 144.95, '2025-03-01', 45, 'CFA Report'),
(11, 1, 2, 1, 9, -37.66, 145.40, '2025-01-15', 70, 'VIIRS'),
(12, 3, 5, 3, NULL, -36.78, 144.25, '2025-02-03', 82, 'MODIS'),
(13, 6, 8, 6, NULL, -36.34, 146.30, '2025-02-10', 76, 'Sentinel-2'),
(14, 9, 2, 9, 1, -37.66, 145.55, '2025-02-14', 93, 'MODIS'),
(15, 7, 9, 7, NULL, -37.58, 143.88, '2025-12-20', 65, 'CFA Report');
