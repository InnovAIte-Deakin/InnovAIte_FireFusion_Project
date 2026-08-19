# FireFusion Historical Fire Data Pipeline

## Overview

This pipeline processes historical bushfire boundary data for the FireFusion project using the Geoscience Australia Historical Bushfire Boundaries dataset.

The workflow focuses on Victorian bushfires and provides a structured process for inspecting, profiling, extracting, validating and preparing historical fire records for future integration with the FireFusion database.

The pipeline was developed as part of the Data Engineering stream to provide reliable historical fire data that can later support other components of the FireFusion system.

## Contributor

- **Name:** Shubham Sharma
- **Project:** FireFusion
- **Stream:** Data Engineering
- **Role:** Data Engineering Team Member
- **Dataset:** Historical Bushfire Boundaries
- **Provider:** Geoscience Australia

## Data Source

**Source:** Geoscience Australia — Historical Bushfire Boundaries

The source dataset is provided as an Esri File Geodatabase (`.gdb`) containing historical fire boundary polygons across Australia.

The national dataset contains more than 310,000 records covering multiple Australian states and different fire types, including bushfires and prescribed burns.

For the FireFusion historical fire pipeline, the data is filtered to:

- State: Victoria
- Fire type: Bushfire
- Record classification: Historical

## Pipeline Workflow

The pipeline is separated into a series of Python scripts so that each stage of the processing can be inspected and executed independently.

The workflow currently performs:

1. Inspection of the source geodatabase and available layers
2. Profiling of the national historical fire dataset
3. Profiling of Victorian fire records
4. Filtering and extraction of Victorian bushfire records
5. Selection of fields required for the project
6. Validation of the expected source coordinate reference system
7. Conversion of spatial data for downstream use
8. Addition of `record_type = HISTORICAL`
9. Investigation and removal of exact duplicate records
10. Validation of the final processed dataset
11. Export of the processed data as GeoJSON

## Data Quality and Duplicate Handling

Data quality checks were performed during both the profiling and validation stages.

The source data contains repeated fire IDs and records with similar attributes. These records were investigated rather than automatically removed because records with the same or similar metadata can represent different fire boundaries.

The duplicate investigation identified **one exact duplicate record** with identical attributes and geometry. This record is removed during extraction before the final GeoJSON is generated.

Records with repeated IDs or similar attributes but different geometries are retained.

## Validation

The processed output is validated before it is considered complete.

The validation script checks that:

- the output dataset is not empty;
- the expected output coordinate reference system is present;
- all records are classified as `HISTORICAL`;
- all records contain valid fire boundary geometry;
- the expected geometry type is maintained; and
- no exact duplicate records remain.

These checks are implemented using assertions so that the validation process fails clearly if an expected condition is not met.

## Current Results

| Metric | Result |
| --- | --- |
| National source records | 310,640 |
| Victorian fire records | 77,463 |
| Victorian bushfires initially extracted | 9,085 |
| Exact duplicate records removed | 1 |
| Final historical bushfire records | 9,084 |
| Geometry type | MultiPolygon |
| Missing geometries | 0 |
| Record type | HISTORICAL |
| Validation status | Passed |

## Scripts

| Script | Purpose |
| --- | --- |
| `01_inspect_geodatabase.py` | Inspects the source geodatabase, layers and schema |
| `02_profile_historical_data.py` | Profiles the national historical fire dataset |
| `03_profile_victoria.py` | Profiles Victorian fire and bushfire records |
| `04_extract_historical_victoria.py` | Extracts, transforms and prepares Victorian historical bushfires |
| `05_validate_historical_output.py` | Runs validation checks against the processed dataset |
| `06_investigate_duplicates.py` | Investigates potential duplicate historical fire records |

## Output

The pipeline produces:

`victoria_historical_bushfires.geojson`

The final output contains the processed Victorian historical bushfire boundaries and associated attributes required for future FireFusion integration.

## Technologies

The pipeline is implemented in Python using:

- GeoPandas
- Pandas
- Pyogrio
- Shapely
- PyProj

Dependencies and package versions are documented in `requirements.txt`.

## Status

Historical fire extraction, duplicate handling and output validation are complete.

The current validated dataset contains **9,084 Victorian historical bushfire records**.

The next stage of the work is integration of the processed historical fire data with the FireFusion PostgreSQL/Supabase database architecture.