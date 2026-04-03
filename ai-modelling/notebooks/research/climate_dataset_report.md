# Climate Dataset Exploration

## Overview
This document presents the evaluation of climate datasets for bushfire prediction modelling in the FireFusion project.

## Climate vs Weather
Weather data captures short-term conditions such as temperature, wind, and rainfall, while climate data represents long-term environmental patterns such as drought and fuel dryness.

Both are required for modelling, weather explains fire behavior, and climate data explains fire risk. 

## Datasets Evaluated
### TerraCLimate
- Monthly data
- Includes soil moisture, precipitation, and water deficit
- Strong data to understand long-term drought and fuel dryness
  Use as a main climate dataset

### CHIRPS
- Daily rainfall data
- Combines satellite data and station data
- More accurate on precipitation
  Use to improve rainfall quality

### ERA5-Land
- Daily weather data
- Includes temperature, wind, and precipitation
  Use for short-term fire behaviour

## Limitation
- Climate data is monthly
- Requires alignment with daily weather data
- Some variables are model-derived

## Recommended Approach
- Use ERA5 for weather data (short-term)
- Use TerraClimate for climate (long-term)
- Use CHIRPS for improved rainfall

