# Data Lineage — Soil Moisture Pipeline (SMAP)

---

## Overview
This document describes the end-to-end data lineage for the soil moisture pipeline developed using NASA SMAP datasets. It outlines how raw satellite data is ingested, processed, validated, and transformed into structured outputs that support the FireFusion system.

The goal of this pipeline is to provide a reliable environmental dataset that can be used for bushfire risk modelling, backend storage, and future AI workflows.

---

## Data Source
- Source: NASA SMAP L4 Global Soil Moisture Dataset  
- Type: Satellite-derived environmental data  
- Format: .h5 (HDF5)  
- Frequency: 3-hourly  
- Coverage: Global (filtered to Australia region)

---

## Pipeline Stages

### 1. Raw Data Ingestion
- Input: SMAP .h5 files stored in /data  
- Description: Raw satellite files are downloaded and stored locally without modification  
- Example Files:
  - SMAP_L4_SM_gph_20231231T223000
  - SMAP_L4_SM_gph_20240101T133000

---

### 2. Data Extraction
- Process: Extract relevant variables from HDF5 files  
- Fields Extracted:
  - latitude  
  - longitude  
  - surface soil moisture  
  - root zone soil moisture  
- Tools Used: Python (h5py, numpy, pandas)  
- Output: Structured dataframe

---

### 3. Data Transformation
- Filtering: Applied geographic filtering to retain only Australia region (lat/lon bounds)  
- Combination: Merged multiple files into a single dataset  
- Enhancements:
  - Added timestamp column  
  - Added source file tracking for traceability  

---

### 4. Data Validation
To ensure data quality and reliability, the following validation checks were implemented:

- Duplicate detection  
- Null value checks  
- Soil moisture range validation  
- Geographic boundary validation  

Validation Results:
- Total Records: 485,510  
- Duplicate Records: 0  
- Null Values: 0  
- All values fall within valid ranges  
- All coordinates fall within Australia bounds  

---

### 5. Processed Outputs

#### 5.1 Validated Dataset
- File: /processed/validated_soil_moisture.csv  
- Description: Cleaned and validated dataset ready for downstream usage  

#### 5.2 Validation Report
- File: /reports/validation_report.json  
- Description: Summary of data quality checks for traceability and auditing  

#### 5.3 Database Schema
- File: /reports/postgresql_schema.sql  
- Description: SQL schema prepared for PostgreSQL integration  

---

## Data Flow Summary

text Raw SMAP HDF5 Files     ↓ Data Extraction (Notebook)     ↓ Combined Dataset     ↓ Validation Layer     ↓ Processed Outputs (CSV + JSON + SQL)     ↓ Backend Storage (PostgreSQL)     ↓ AI / Modelling Integration 

---

## Integration with FireFusion

This pipeline contributes to the FireFusion system by:

- Providing environmental features related to land dryness  
- Supporting bushfire risk modelling workflows  
- Enabling integration with weather and fire datasets  
- Preparing data for backend storage using PostgreSQL  
- Supporting future AI-based prediction and analysis  

---

## Data Schema

| Column Name            | Type      | Description |
|------------------------|----------|-------------|
| latitude               | float    | Geographic latitude (Australia filtered) |
| longitude              | float    | Geographic longitude (Australia filtered) |
| surface_soil_moisture  | float    | Surface-level soil moisture value |
| rootzone_soil_moisture | float    | Root zone soil moisture value |
| timestamp              | datetime | Observation timestamp |
| source_file            | string   | Original SMAP file reference |

---

## Data Quality Summary

- Total Records: 485,510  
- Duplicate Records: 0  
- Null Values: 0 across all columns  

Range Validation:
- Surface Soil Moisture: Valid (0 to ~0.73)  
- Root Zone Soil Moisture: Valid (0.01 to ~0.91)  

Geographic Validation:
- All records fall within Australia boundaries  

---

## Pipeline Usage Guide

1. Place raw SMAP .h5 files in the /data directory  
2. Open and run smap_analysis.ipynb  
3. The pipeline will:
   - extract and filter Australia-specific data  
   - combine multiple datasets  
   - apply validation checks  
4. Outputs are generated automatically:
   - /processed/validated_soil_moisture.csv  
   - /reports/validation_report.json  
   - /reports/postgresql_schema.sql  

---

## Reproducibility

- The pipeline is designed to run end-to-end  
- All file paths are standardised and relative  
- Outputs are deterministic based on input data  
- Folder structure ensures consistency across runs  

---

## Contribution Guidelines

- Maintain folder structure (data, notebooks, processed, reports)  
- Apply validation checks to all new datasets  
- Ensure schema consistency for integration  
- Keep outputs structured for downstream use  

---

## Dependencies

- Python (pandas, numpy, h5py)  
- NASA Earthdata SMAP datasets  
- Local file system for storage  
- Future: PostgreSQL database  

---

## Risks & Considerations

- Dataset is currently static (not real-time)  
- Integration with other datasets is required for full modelling  
- Large file sizes may impact storage and processing performance  

---

## Key Learnings

- Importance of validation in data pipelines  
- Need for reproducible and structured workflows  
- Aligning data engineering outputs with system-level architecture  
- Designing outputs for downstream usability  

---

## Future Improvements

- Automate pipeline execution (scheduled jobs)  
- Introduce real-time data ingestion  
- Integrate with weather and fire datasets  
- Extend lineage tracking across multiple data sources  
- Improve scalability and performance  

---

## Ownership

- Owner: Archit Chandna  
- Stream: Data Engineering  
- Component: Soil Moisture Pipeline (SMAP)