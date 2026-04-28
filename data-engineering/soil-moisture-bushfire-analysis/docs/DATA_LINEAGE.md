# Data Lineage — Soil Moisture Pipeline (SMAP)

## Overview
This document describes the end-to-end data lineage for the soil moisture pipeline developed using NASA SMAP datasets. It explains how raw data is transformed into validated outputs and how it supports the FireFusion system.

---

## Data Source
- Source: NASA SMAP L4 HDF5 files
- Type: Satellite-based soil moisture data
- Format: `.h5`
- Frequency: 3-hourly
- Coverage: Global (filtered to Australia)

---

## Pipeline Stages

### 1. Raw Data Ingestion
- Input: SMAP `.h5` files stored in `/data`
- Description: Raw satellite files downloaded and stored locally
- Example Files:
  - SMAP_L4_SM_gph_20231231T223000
  - SMAP_L4_SM_gph_20240101T133000

---

### 2. Data Extraction
- Process: Extract latitude, longitude, surface soil moisture, root zone soil moisture
- Tool: Python (h5py, numpy, pandas)
- Output: Structured dataframe

---

### 3. Data Transformation
- Filter: Australia region (lat/lon bounds)
- Combine: Multiple files into a single dataset
- Add: Timestamp and source tracking

---

### 4. Data Validation
Validation checks implemented:
- Duplicate check
- Null value check
- Soil moisture range validation
- Geographic boundary validation

Result:
- 485,510 records
- 0 duplicates
- 0 null values
- All values within valid ranges

---

### 5. Processed Outputs

#### 5.1 Validated Dataset
- File: `/processed/validated_soil_moisture.csv`
- Description: Cleaned dataset ready for downstream use

#### 5.2 Validation Report
- File: `/reports/validation_report.json`
- Description: Summary of data quality checks

#### 5.3 Database Schema
- File: `/reports/postgresql_schema.sql`
- Description: SQL schema for PostgreSQL integration

---

## Data Flow Summary

Raw SMAP HDF5 Files  
→ Extraction (Notebook)  
→ Combined Dataset  
→ Validation Layer  
→ Processed CSV + Reports  
→ PostgreSQL Schema  
→ Future Integration (Backend / AI Models)

---

## Integration with FireFusion

This pipeline supports:
- Environmental feature generation for bushfire risk modelling
- Integration with weather and fire datasets
- Backend storage using PostgreSQL
- Future AI modelling workflows

---

## Key Learnings

- Importance of data validation in ETL pipelines
- Structuring pipelines for reproducibility
- Aligning data engineering work with system architecture
- Ensuring outputs are usable by other teams

---

## Next Steps

- Integrate with weather and fire datasets
- Automate pipeline execution
- Improve data lineage tracking across all datasets
- Support real-time data ingestion in future

---

## Data Schema Details

| Column Name              | Type        | Description |
|--------------------------|------------|-------------|
| latitude                 | float      | Geographic latitude (Australia filtered) |
| longitude                | float      | Geographic longitude (Australia filtered) |
| surface_soil_moisture    | float      | Surface-level soil moisture value |
| rootzone_soil_moisture   | float      | Root zone soil moisture value |
| timestamp                | datetime   | Observation timestamp |
| source_file              | string     | Original SMAP file reference |

---

## Data Quality Summary

- Total Records: 485,510
- Duplicate Records: 0
- Null Values: 0 across all columns
- Range Checks:
  - Surface Soil Moisture: Valid (0 to ~0.73)
  - Root Zone Soil Moisture: Valid (0.01 to ~0.91)
- Geographic Validation:
  - All data points fall within Australia bounds

---

## Lineage Ownership

- Owner: Archit Chandna  
- Stream: Data Engineering  
- Component: Soil Moisture Pipeline (SMAP)  

---

## Dependencies

- Python (pandas, numpy, h5py)
- NASA Earthdata SMAP datasets
- Local file storage
- Future: PostgreSQL database integration

---

## Risks & Considerations

- Static dataset (not yet real-time)
- Needs integration with weather and fire datasets
- Large file sizes may impact storage and performance

---

## Future Improvements

- Automate ingestion pipeline (scheduled jobs)
- Add real-time data support
- Integrate with unified spatial-temporal framework
- Extend lineage tracking across all datasets in FireFusion