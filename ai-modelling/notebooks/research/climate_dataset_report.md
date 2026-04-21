# Climate Dataset Exploration

## Overview
This document presents the evaluation of climate datasets for bushfire prediction modelling in the FireFusion project. The goal is to identify suitable datasets that capture long-term environmental conditions influencing fire risk. 

## Climate vs Weather
Weather data captures short-term conditions such as temperature, wind, and rainfall, while climate data represents long-term environmental patterns such as drought and fuel dryness.

Both are required for modelling, weather explains fire behaviour, and climate data explains fire risk. 

## Datasets Evaluated
### TerraClimate
- Monthly data
- Model-based dataset derived from climate models and historical observations
- Includes soil moisture, precipitation, and water deficit
- Strong data to understand long-term drought and fuel dryness
  Use as a primary climate dataset

### CHIRPS
- Daily rainfall data
- Combines satellite observations with ground weather station data
- More accurate on precipitation
  Use to improve rainfall quality

### ERA5-Land
- Daily weather data
- Reanalysis dataset combining model simulations with satellite and station observations
- Includes temperature, wind, and precipitation
  Use for short-term fire behaviour

## Limitation
- Climate data is monthly, resulting in lower temporal resolution
- Requires alignment with daily weather data
- Some variables are model-derived rather than directly observed

## Recommended Approach
- Use ERA5 for weather data (short-term)
- Use TerraClimate for climate (long-term)
- Use CHIRPS for improved rainfall
This combined approach supports modelling by capturing both immediate fire behavior and underlying environmental risk factors.

## Reference 
- Google Earth Engine Data Catalog - TerraClimate
  https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_TERRACLIMATE
  
- Google Earth Engine Data Catalog - CHIRPS
  https://developers.google.com/earth-engine/datasets/catalog/UCSB_CHG_CHIRPS_DAILY
  
- Google Earth Engine Data Catalog - ERA5-Land
  https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
  
- Funk et al. (2015). The Climate Hazard Infrared Precipitation with Stations (CHIRPS) dataset.
  https://doi.org/10.1038/sdata.2015.66
  
- Abatzoglou et al. (2018). TerraClimate: A high-resolution global dataset of monthly climate and water balance.
  https://doi.org/10.1038/sdata.2017.191
  
- ECMWF (European Centre for Medium-Range Weather Forecasts) - ERA5 documentation
  https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5
