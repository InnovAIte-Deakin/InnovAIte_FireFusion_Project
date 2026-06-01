# Topography Analysis for Bushfire Risk (Victoria)

## Overview
This project processes Digital Elevation Model (DEM) data to extract elevation and slope features for fire occurrence points in Victoria, Australia. These terrain features are important factors influencing bushfire behaviour and spread.

## Dataset
- Source: SRTM Digital Elevation Model (DEM)
- Region: Victoria, Australia
- Input: Fire dataset containing latitude and longitude coordinates
- Resolution: ~30m (1 arc-second)

## What I Did
- Merged DEM tiles to create a continuous elevation dataset for Victoria  
- Filtered fire dataset to match DEM coverage  
- Extracted elevation (`elevation_meters`) for each coordinate  
- Computed slope (`slope_angle`) using a 3x3 local neighborhood (Horn’s method)  
- Converted spatial resolution from degrees to meters for accurate slope calculation  
- Handled missing and NoData values safely  

## Key Observations
- Most fire points occur in low to moderate slope regions  
- Higher elevation areas show more terrain variation  
- Slope values are generally low, consistent with Victoria’s terrain  

## Why This Matters
Topography plays a critical role in bushfire behaviour. Slope affects fire spread speed, while elevation influences vegetation and climate conditions. These features can be used as inputs for bushfire prediction models.

## Tech Stack
- Python  
- NumPy, Pandas  
- Rasterio  
- Matplotlib  

## Output
- Processed topography features (generated locally)  
- Elevation and slope values aligned with project schema  

## Notes
Datasets are not included in this repository due to storage guidelines.  
To run this notebook locally, ensure the following files are available:
- `fire_prediction_dataset.csv`
- `victoria_merged_dem.tif`