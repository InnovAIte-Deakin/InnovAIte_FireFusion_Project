# FireFusion Data Pipeline Architecture

## Overview

This repository contains the data extraction pipelines and database architecture for the FireFusion bushfire prediction system.

We utilize a **Spatial-Temporal Database Architecture (Hub and Spoke model)**. Instead of a rigid schema tied to specific fire events, all environmental observations (weather, soil, fire) act as independent events connected by a universal map and calendar. This ensures high scalability and allows the Machine Learning team to easily query the exact conditions for any location at any given time.

---

## System Architecture

### Central Hub Tables

#### Location_Registry

| Column | Type | Key |
|---|---|---|
| location_id | int | PK |
| grid_latitude | float | |
| grid_longitude | float | |
| region_name | string | |

#### Time_Registry

| Column | Type | Key |
|---|---|---|
| time_id | int | PK |
| datetime_record | datetime | |
| season | string | |

---

### Observation Tables (Daily Batching)

#### Weather_Observation

| Column | Type | Key |
|---|---|---|
| weather_id | int | PK |
| location_id | int | FK → Location_Registry |
| time_id | int | FK → Time_Registry |
| original_latitude | float | |
| original_longitude | float | |

#### Fire_Incident_Record

| Column | Type | Key |
|---|---|---|
| incident_id | int | PK |
| location_id | int | FK → Location_Registry |
| time_id | int | FK → Time_Registry |
| original_latitude | float | |
| original_longitude | float | |

#### Vegetation_Condition

| Column | Type | Key |
|---|---|---|
| veg_condition_id | int | PK |
| location_id | int | FK → Location_Registry |
| time_id | int | FK → Time_Registry |
| original_latitude | float | |
| original_longitude | float | |

---

### Static Tables (Historical One-Time)

#### Topography_Profile

| Column | Type | Key |
|---|---|---|
| topo_id | int | PK |
| location_id | int | FK → Location_Registry |
| original_latitude | float | |
| original_longitude | float | |

#### Infrastructure_Asset

| Column | Type | Key |
|---|---|---|
| asset_id | int | PK |
| location_id | int | FK → Location_Registry |
| original_latitude | float | |
| original_longitude | float | |

---

## Core Principles

### 1. Data Alignment (The Universal Grid)

Data from different sources (NASA, Open-Meteo, ELVIS) use different coordinate systems and time formats.

- All extraction scripts must "snap" or round their raw latitude, longitude, and timestamps to match our universal `Location_Registry` and `Time_Registry`.
- This ensures that weather, soil, and fire data stack perfectly on top of each other for the AI model to process.

### 2. Data Lineage (Preserving Raw Data)

Because we are modifying the data to fit our grid, we must keep a permanent record of the truth.

> **Strict Rule:** Every observation table must include `original_latitude` and `original_longitude` columns. Do not discard the exact, untouched coordinates provided by the original API or satellite.

---

## Data Extraction Pipelines

Our pipeline system is divided into two distinct workflows:

### A. Historical Data (One-Time Bulk Load)

Static data that builds the permanent foundation of our map. These scripts are run **once**.

- **Topography Profile:** ELVIS Elevation and Depth.
- **Infrastructure Asset:** At-Risk Registers and Fire Management Zones.
- **Static Vegetation:** National Vegetation Information System (NVIS).
- **Historical Fire Records:** GeoScience Australia and CFA logs *(used exclusively for initial AI model training)*.

### B. Batching Data (Daily Scheduled Updates)

Dynamic data that updates continuously. These scripts run on a scheduled batch process to provide the live prediction system with current numbers.

- **Weather Observation:** Open-Meteo API (current temperature, wind, humidity).
- **Vegetation Condition:** SMAP Satellite (current soil moisture and dryness).
- **Active Fire Records:** NASA FIRMS (newly detected satellite hotspots).

---

## Developer Instructions

When creating a new Python extraction script or submitting a Pull Request, please ensure you meet the following criteria:

1. **Source Documentation:** Clearly list the API endpoint or download URL in your code comments.
2. **Implement Grid Snapping:** Convert raw coordinates to our standard `location_id` and `time_id`.
3. **Save Raw Data:** Map the untouched coordinates to the `original_latitude` and `original_longitude` columns.
4. **Data Typing:** Ensure your pandas DataFrame outputs match the exact PostgreSQL column types defined in the schema before loading.
