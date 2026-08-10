# Bushfire Data Processing Module

## Overview

This folder contains the environmental data extraction, preprocessing, and transformation pipelines used for the FireFusion bushfire forecasting project.

The module is responsible for:
- Collecting climate and atmospheric datasets from Google Earth Engine (GEE)
- Processing ERA5 and CAMS environmental datasets
- Aggregating weather data into model-ready temporal intervals
- Generating spatially aligned 5 km grid datasets
- Cleaning and transforming datasets for machine learning workflows
- Preparing structured inputs for LSTM and deep learning models

The pipelines in this folder support the FireFusion AI modelling workflow by creating consistent environmental datasets aligned by:
- `grid_id`
- `timestamp`
- `12-hour temporal intervals`
- `5 km spatial grids`

---

# Folder Structure

| File | Purpose |
|---|---|
| `README.md` | Main overview and onboarding guide for the bushfire data module |
| `climate_dataset.py` | Loads TerraClimate environmental data from Google Earth Engine |
| `CLIMATE_DATASET_README.md` | Documentation for the TerraClimate dataset loader |
| `gee_api.py` | Core Earth Engine API wrapper for extracting environmental datasets |
| `preprocessing.py` | Generic reusable data cleaning and preprocessing utilities |
| `transforms.py` | Time-series interpolation and feature scaling utilities |
| `data_processing.py` | LSTM/GRU preprocessing utilities and temperature conversion helpers |
| `era5_dataset.py` | ERA5 weather dataset extraction pipeline |
| `era5_land_dataset_extraction.js` | ERA5-Land extraction pipeline written for Google Earth Engine |
| `cams-dataset.py` | CAMS atmospheric dataset extraction pipeline |
| `GEE-API-USAGE.md` | Usage documentation for the Earth Engine API module |
| `DATA_HANDLING_USAGE.md` | Documentation for preprocessing and transformation utilities |
| `CAMS-DATASET-README.md` | Detailed CAMS dataset documentation |
| `ERA5_LAND_README.md` | ERA5-Land dataset documentation and extraction notes |

---

# Core Workflow

The overall environmental data pipeline follows this structure:

```text
Google Earth Engine Datasets
        ↓
ERA5 / ERA5-Land / CAMS Extraction
        ↓
Feature Processing & Cleaning
        ↓
12-Hour Temporal Aggregation
        ↓
5 km Spatial Grid Extraction
        ↓
Dataset Alignment by grid_id + timestamp
        ↓
Preprocessing & Feature Scaling
        ↓
LSTM / Deep Learning Model Inputs
```

---

# Main Datasets

## ERA5 Weather Dataset

The ERA5 pipeline extracts bushfire-relevant meteorological variables such as:
- Air temperature
- Dewpoint temperature
- Wind speed
- Wind direction
- Surface pressure
- Precipitation

The dataset is:
- filtered to Victoria, Australia
- aggregated into 12-hour intervals
- mapped onto 5 km grid cells

### Main Files
- `era5_dataset.py`
- `era5_land_dataset_extraction.js`
- `ERA5_LAND_README.md`

---

## CAMS Atmospheric Dataset

The CAMS pipeline extracts atmospheric composition and smoke-related features.

Selected features include:
- Aerosol Optical Depth (AOD)
- PM2.5

These features provide:
- smoke context
- air quality indicators
- atmospheric aerosol information

The CAMS dataset is aligned with the ERA5 pipeline using:
- identical 5 km grid cells
- shared timestamps
- consistent export structure

### Main Files
- `cams-dataset.py`
- `CAMS-DATASET-README.md`

---

## TerraClimate Dataset

The TerraClimate loader provides access to:
- soil moisture
- precipitation
- climatic water deficit

This module acts as an extendable climate dataset loader for future modelling work.

### Main Files
- `climate_dataset.py`
- `CLIMATE_DATASET_README.md`

---

# Google Earth Engine Integration

The project uses Google Earth Engine (GEE) as the primary environmental data source.

The `gee_api.py` module provides:
- Earth Engine initialization
- dataset loading
- spatial area creation
- raw data extraction
- mean time-series extraction
- conversion to Pandas DataFrames

This abstraction simplifies integration with:
- ERA5
- MODIS
- CAMS
- TerraClimate
- future datasets

### Main File
- `gee_api.py`

### Additional Documentation
- `GEE-API-USAGE.md`

---

# Preprocessing & Data Cleaning

The preprocessing utilities are designed to be reusable across multiple environmental datasets.

Supported preprocessing operations include:
- missing value handling
- duplicate removal
- schema-based type casting
- datetime conversion
- categorical conversion

### Main File
- `preprocessing.py`

### Features
- Generic `DataCleaner` class
- Schema-driven transformations
- Reusable across multiple datasets

---

# Time-Series Transforms

The transforms module provides utilities for:
- temporal interpolation
- grouped interpolation
- feature scaling
- normalization
- standardization

These transformations support model-ready time-series generation.

### Main File
- `transforms.py`

### Supported Scaling Methods
- Standard scaling
- Min-max scaling

---

# LSTM Data Preparation

The `data_processing.py` module prepares sequential environmental datasets for:
- LSTM models
- GRU models
- ConvLSTM workflows

Features include:
- sliding window sequence generation
- 3D tensor reshaping
- satellite temperature conversion utilities

### Main File
- `data_processing.py`

---

# Spatial & Temporal Alignment

A key design principle of this module is maintaining consistent spatial and temporal alignment across all datasets.

## Spatial Structure
- Victoria divided into 5 km grid cells
- each grid cell assigned a unique `grid_id`

## Temporal Structure
- data aggregated into 12-hour intervals
- shared timestamps across datasets

This allows multiple environmental datasets to be merged reliably during:
- feature engineering
- model training
- inference pipelines

---

# Technologies Used

- Python
- JavaScript (Google Earth Engine)
- Google Earth Engine API
- Pandas
- NumPy
- ERA5
- ERA5-Land
- CAMS
- TerraClimate

---

# Typical Use Cases

This module supports:
- Bushfire forecasting
- Environmental feature engineering
- Climate data extraction
- Atmospheric smoke analysis
- LSTM training pipelines
- Spatial-temporal modelling
- Environmental preprocessing workflows

---

# Setup Notes

Install dependencies from the project root:

```bash
pip install -r ai-modelling/requirements.txt
```

Authenticate Earth Engine before running extraction scripts:

```bash
earthengine authenticate
```

---

# Related Documentation

| Document | Description |
|---|---|
| `CLIMATE_DATASET_README.md` | TerraClimate dataset loader documentation |
| `GEE-API-USAGE.md` | Earth Engine API usage guide |
| `DATA_HANDLING_USAGE.md` | Preprocessing and transforms documentation |
| `CAMS-DATASET-README.md` | CAMS dataset extraction details |
| `ERA5_LAND_README.md` | ERA5-Land dataset documentation |

---

# Notes

- Large GEE exports should be processed in smaller date chunks to avoid memory and export limitations.
- Most datasets are aligned using the same spatial and temporal structure to simplify downstream modelling.
- The preprocessing utilities are intentionally generic so they can be reused across future datasets.
