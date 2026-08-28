# ERA5 Weather Integration Pipeline

## Source Information

- **Source:** ERA5 Reanalysis Dataset
- **Provider:** ECMWF / Copernicus Climate Data Store
- **Collected By:** Shubham Sharma
- **Date Collected:** May 2026
- **Refresh Frequency:** Historical weather dataset
- **File Format:** NetCDF (.nc) converted to CSV
- **Region:** Victoria, Australia
- **Time Range:** January 2020
- **Planner Task:** ERA5 Weather Data Integration Pipeline

---

## Description

This pipeline processes ERA5 weather reanalysis data for the FireFusion project. The objective of the pipeline is to prepare weather observations for integration into the shared `weather_observation` schema used across the project.

The workflow standardises weather data, aligns records with the shared spatial-temporal framework, and generates integration-ready outputs using the project’s `location_registry` and `time_registry`.

The processed dataset supports downstream analytics, machine learning, and bushfire prediction modelling.

---

## Variables Used

| Column Name | Description |
|---|---|
| datetime | Observation timestamp |
| original_latitude | Original latitude from ERA5 |
| original_longitude | Original longitude from ERA5 |
| temperature_C | Air temperature in Celsius |
| wind_speed | Calculated wind speed magnitude |
| location_id | Shared spatial identifier from Location Registry |
| time_id | Shared temporal identifier from Time Registry |

---

## Transformations Applied

### 1. ERA5 Data Preparation
- Loaded processed ERA5 weather CSV dataset
- Renamed columns to align with project schema
- Selected required weather variables for integration

### 2. Datetime Standardisation
- Converted datetime fields into consistent datetime format
- Preserved hourly timestamp precision for registry matching

### 3. Victoria Spatial Filtering
- Filtered records using Victoria geographic bounds:
  - Latitude: -39.2 to -34.0
  - Longitude: 140.96 to 150.0

### 4. Spatial Integration
- Exported `location_registry` from Supabase
- Implemented nearest-neighbour coordinate matching using KD-tree
- Generated `location_id` for all ERA5 records

### 5. Temporal Integration
- Exported January 2020 subset of `time_registry`
- Matched ERA5 timestamps to `time_id`
- Successfully aligned all hourly ERA5 observations with the shared time registry

---

## Data Quality Checks

| Validation Check | Result |
|---|---|
| Missing location_id values | 0 |
| Missing time_id values | 0 |
| Missing temperature values | 0 |
| Missing wind_speed values | 0 |
| Victoria-filtered records | 578,088 |

---

## Final Output

### Output File
`era5_weather_integrated.csv`

### Final Schema
- location_id
- time_id
- original_latitude
- original_longitude
- temperature_C
- wind_speed

---

## Spatial-Temporal Framework

This pipeline aligns ERA5 weather observations with the project’s shared spatial-temporal architecture using:
- `location_registry`
- `time_registry`

This enables seamless joins between:
- weather datasets
- fire event datasets
- vegetation datasets
- topography datasets

through common `location_id` and `time_id` keys.

---

## Contributor Information

| Field | Details |
|---|---|
| Contributor | Shubham Sharma |
| Stream | Data Engineering |
| Project | FireFusion |
| Contribution | ERA5 Weather Integration Pipeline |
| Technologies Used | Python, Pandas, SciPy, Supabase |