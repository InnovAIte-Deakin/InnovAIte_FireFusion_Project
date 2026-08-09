# FireFusion Historical Fire Data Pipeline

## Overview

This pipeline processes historical bushfire data from the Geoscience Australia Historical Bushfire Boundaries dataset for the FireFusion project.

The current workflow extracts Victorian historical bushfire records, prepares the geospatial data, and validates the processed dataset before database integration.

## Data Source

Source: Geoscience Australia — Historical Bushfire Boundaries

The source dataset is provided as an Esri File Geodatabase (`.gdb`) containing historical fire boundary polygons across Australia.

## Current Pipeline

The pipeline currently performs:

1. Geodatabase inspection
2. Dataset profiling
3. Victorian fire data profiling
4. Extraction of Victorian bushfire records
5. CRS conversion from EPSG:4283 to EPSG:4326
6. Addition of `record_type = HISTORICAL`
7. Output validation
8. Duplicate investigation

## Current Results

- National records: 310,640
- Victorian fire records: 77,463
- Victorian bushfire records extracted: 9,085
- Geometry type: MultiPolygon
- Missing geometries: 0
- Output CRS: EPSG:4326
- Record type: HISTORICAL

## Scripts

- `01_inspect_geodatabase.py` — inspects geodatabase layers and schema
- `02_profile_historical_data.py` — profiles the national historical dataset
- `03_profile_victoria.py` — analyses Victorian bushfire records
- `04_extract_historical_victoria.py` — extracts and transforms Victorian historical bushfires
- `05_validate_historical_output.py` — validates the processed dataset
- `06_investigate_duplicates.py` — investigates potential duplicate records

## Status

Historical fire extraction and validation are complete.

Database integration with the FireFusion PostgreSQL/Supabase architecture is the next stage.