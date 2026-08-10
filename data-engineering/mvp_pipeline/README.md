FireFusion Data Engineering - MVP ETL Pipeline Documentation
============================================================

Overview
--------

The FireFusion MVP ETL pipeline transforms raw Victoria fire, weather, and environmental data into a normalized **Hub & Spoke** schema. This alignment enables heterogeneous data sources to be used for AI model training.

### Problem

Raw data sources often have misaligned coordinates, temporal resolutions, and geographic coverage. Standard relational joins fail because the data points don't perfectly align.

### Solution

We use a Hub & Spoke schema. We snap data to common grid and time buckets.

-   **Hub tables**: `location_registry` (snapped grid cells) and `time_registry` (hourly batches).

-   **Spoke tables**: `fire`, `weather`, and `vegetation` reference the hubs via foreign keys. All data aligns on `(location_id, time_id)`.

Architecture
------------

### Data Model

-   **Hub Tables:** `location_registry`, `time_registry`

-   **Spoke Tables (Observations):** `fire_incident_record`, `weather_observation`, `vegetation_condition`

-   **Static Tables (Location only):** `topography_profile`, `infrastructure_asset`

### Why This Design?

-   **Hub tables** act as a single source of truth for spatial and temporal alignment.

-   **Foreign keys** enforce referential integrity.

-   **Raw coordinates** are preserved for auditing or re-snapping.

-   **Spoke tables** allow new data sources to be joined without changing the core schema.

How It Works
------------

1.  **Load Raw Data:** The pipeline reads 5 input CSV files from the `input/` folder.

2.  **Grid Snap:** Coordinates are checked against Victoria's bounds and snapped to the nearest 0.1° cell to get a `location_id`.

3.  **Time Register:** Timestamps are parsed and batched to the nearest hour to get a `time_id`.

4.  **Align Tables:** Original data columns are combined with their new `location_id` and `time_id`. (Static tables skip `time_id`).

5.  **Validate:** Checks ensure there are no nulls in critical fields, primary keys are unique, and foreign keys reference valid hub records.

6.  **Save:** Outputs 7 aligned CSV files to the `output/` folder and generates a `pipeline_report.json`.

Files & Usage
-------------

### Core Files

-   `mvp_pipeline.py`: The main ETL orchestrator containing the `GridSnapper`, `TimeRegistry`, and `MVPPipeline` logic.

-   `generate_datasets.py`: Generates synthetic Black Summer (2019-2020) data for testing.

### Usage

```
# 1. Generate test data
python generate_datasets.py

# 2. Run the pipeline
python mvp_pipeline.py

```

### Checking Results

Aligned data is saved as CSV files in the `output/` folder. You can view the `pipeline_report.json` to see a summary of the records processed.

Core Components
---------------

### Grid Snapper

Aligns coordinates from different sources to common 0.1° grid cells (~11km). Out-of-bounds coordinates are dropped.

### Time Registry

Batches timestamps to an hourly resolution, enabling temporal joins across different observation frequencies. It also maps timestamps to seasons.

Next Steps
----------

1.  **Load to Supabase:** Copy the output CSVs to PostgreSQL.

2.  **AI/ML Integration:** Use the aligned data for LSTM fire forecasting models.

3.  **Dashboard:** Build a frontend to visualize fire risk by location and time.

4.  **Real Data:** Replace the synthetic input datasets with actual data.