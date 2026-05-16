# Contributor Information

- **Name:** Shubham Sharma
- **Role:** Data Engineering Stream Member
- **Planner Task:** ERA5 Weather Data Pipeline Development and Integration

---

# ERA5 Data Processing Pipeline – FireFusion

## Overview
This notebook implements a preprocessing pipeline for ERA5 weather data to support bushfire risk modelling as part of the FireFusion capstone project.

# Data Source

- **Dataset:** ERA5 Reanalysis Weather Data
- **Provider:** ECMWF / Copernicus Climate Data Store
- **Region:** Victoria, Australia
- **Date Range:** January – February 2020 (Black Summer Bushfires)
- **Variables Used:**
  - 2m Temperature
  - 10m u-component of wind
  - 10m v-component of wind
  - Total Precipitation

---

# Contribution Summary

- Developed preprocessing pipeline for ERA5 weather dataset using Python
- Processed NetCDF weather data into structured tabular format
- Applied data cleaning, transformation, and unit conversions
- Engineered wind speed feature from wind vector components
- Conducted exploratory data analysis (EDA) and validation
- Prepared schema-aligned dataset for Supabase integration
- Updated repository structure and documentation according to team feedback

## Data Coverage
- Region: Victoria, Australia  
- Period: January – February 2020 (Black Summer bushfires)

## Variables Used
- 2m Temperature  
- 10m u-component of wind  
- 10m v-component of wind  
- Total precipitation  

## Pipeline Steps
1. Load ERA5 NetCDF files (accumulated + instantaneous)
2. Merge datasets
3. Convert multidimensional data into tabular format
4. Clean and rename columns
5. Convert units:
   - Temperature: Kelvin → Celsius  
   - Precipitation: meters → millimeters  
6. Create wind speed feature
7. Save processed dataset

## Output
Processed dataset includes:
- datetime  
- latitude, longitude  
- temperature (°C)  
- precipitation (mm)  
- wind_speed (m/s)  

## Notes
- Raw (.nc) and processed (.csv) data files are not included in this repository due to storage limitations.
- This notebook demonstrates the full pipeline logic for reproducibility.

## Future Work
- Integrate NDVI (vegetation data)
- Store processed data in PostgreSQL
- Automate ingestion using ERA5 API