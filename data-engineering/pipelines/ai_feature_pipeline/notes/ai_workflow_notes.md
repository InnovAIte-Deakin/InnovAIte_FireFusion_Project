# AI Workflow Analysis Notes

## Overview
Analysis of the AI modelling team's existing workflows to understand data requirements and integration points for the data engineering pipeline.

## Key Findings

### 1. AI Model Input Requirements

#### TCN Classifier Training Pipeline
- **Location**: `ai-modelling/src/training/tcn_train_classifier.py`
- **Input Data**: Multiple ERA5-Land CSV files (2018-2022, 6-month chunks)
- **Spatial Resolution**: 5km grid for Victoria region
- **Temporal Resolution**: 12-hourly intervals
- **Target Variable**: Fire labels from satellite detections

#### Required Features
```python
FEATURES = [
    'temperature_2m_c',
    'skin_temperature_c', 
    'soil_temperature_level_1_c',
    'surface_solar_radiation_downwards',
    'surface_thermal_radiation_downwards',
    'u_component_of_wind_10m',
    'v_component_of_wind_10m',
]
```

#### Model Architecture
- **Model Type**: Temporal Convolutional Network (TCN)
- **Lookback Window**: 60 steps (30 days at 12-hour intervals)
- **Batch Size**: 64
- **Sequence Generation**: On-the-fly during training

### 2. Data Processing Pipeline

#### Existing Data Sources
1. **ERA5-Land Environmental Data**: Hourly land surface variables
2. **Satellite Fire Detections**: Point-based fire observations
3. **Spatial Join**: Fire detections mapped to 5km grid cells

#### Processing Steps
1. Load multiple ERA5-Land CSV files
2. Load satellite fire detection data
3. Spatially join fire detections to environmental grid cells
4. Build complete label table (environmental data as spine, fire as labels)
5. Time-based train/val/test split (no leakage)
6. StandardScaler fitting on training data only
7. Sequence generation for TCN input

### 3. Data Schema Requirements

#### Environmental Features
- Temperature variables (multiple levels)
- Radiation components (solar, thermal)
- Wind components (u, v vectors)
- Soil moisture and temperature
- Precipitation totals

#### Spatial Components
- Grid cell identifiers
- Latitude/longitude coordinates
- Stable grid references

#### Temporal Components
- Timestamp fields for sequence ordering
- Consistent 12-hourly intervals

#### Target Labels
- Binary fire presence/absence
- Fire temperature readings
- Fire temporal characteristics

### 4. Integration Points

#### Data Loading Patterns
- Multiple CSV file loading
- Chunked processing for large datasets
- Spatial coordinate handling

#### Preprocessing Requirements
- Temperature unit conversions
- Missing value handling
- Duplicate removal
- Coordinate validation

#### Output Requirements
- AI-ready feature matrices
- Consistent temporal sequences
- Validated spatial references

## Recommendations for DE Pipeline

### 1. Schema Alignment
The master dataset schema aligns well with AI requirements:
- Contains all required environmental features
- Includes spatial coordinates and grid identifiers
- Has temporal information in universal_key

### 2. Processing Priorities
- **Chunked Processing**: Essential for 2.2GB dataset
- **Validation**: Coordinate ranges, missing values, duplicates
- **Standardization**: Consistent column naming and types
- **Export**: AI-ready CSV outputs with proper indexing

### 3. Reusable Components
- Leverage existing validation patterns from `open_meteo/` pipeline
- Use interpolation utilities for spatial processing
- Follow established DE architecture patterns

### 4. Output Format
- Processed CSV with AI-ready schema
- Proper temporal ordering for sequence generation
- Validated spatial and temporal consistency
- Metadata for processing logs and row counts