# Climate Dataset Loader

## Overview
This module provides a simple pipeline for loading climate data for Victoria (Australia) using Google Earth Engine (GEE).
It is designed to support the FireFusion AI modelling stream by supplying long-term environmental variables relevant to bushfire prediction.

## Data Source
**TerraClimate (IDAHO_EPSCOR/TERRACLIMATE)**
- Monthly resolution
- Around 4 km spatial resolution
- Covers from 1958-present

## Selected Variables
The following variables are used:
- **soil**: soil moisture indicates fuel dryness
- **def**: climatic water deficit indicates drought intensity
- **pr**: precipitation indicates moisture availability
These variables are selected because they capture long-term environmental conditions that influence fire risk.

## Study Period
The dataset is filtered to: **2012-2020**
This period includes major fire events and aligns with available datasets across the project.

## How It Works
The script:
1. Initializes Google Earth Engine
2. Loads Victoria boundary from the FAO GAUL dataset
3. Filters TerraClimate data by region (Victoria) and data range (2012-2020)
4. Selects relevant climate variables
5. Returns an Earth Engine ImageCollection

## Usage
### 1. Initialize Google Earth Engine
```python
import ee
ee.Initialize()
```
### 2. Load climate data
```python
from climate_dataset import get_victoria_boundary, load_climate_data
region = get_victoria_boundary()
climate_data = load_climate_data(region)
```
### 3. Inspect dataset
```python
print(climate_data)
```

## Output
The script returns an **Earth Engine ImageCollection** containing climate variables for Victoria within the selected date range (2012-2020).
The output is a raster dataset stored in Earth Engine (not yet tabular data), and spatial information is stored implicitly in the image pixels. The dataset will be further processed into a grid-based format for modelling.
