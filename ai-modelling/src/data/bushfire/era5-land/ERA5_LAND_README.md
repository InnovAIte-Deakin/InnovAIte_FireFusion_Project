# FireFusion - ERA5-Land Dataset Loader
## Overview
This module prepares the ERA5-Land environmental dataset for hte FireFusion bushfire forecasting model.
The goal is to load, process, aggregate, and export environmental variables from Google Earth Engine (GEE) into a structured dataset for baseline bushfire risk prediction.

## Study Area
- **Region**: Victoria, Australia
- **Focus Area**: Bushfire-prone and forest-dominant regions
- **Grid Size**: 5km x 5km  
Victoria was selected because it is one of the highest bushfire-risk regions in Australia and aligns with the project scope.

## Dataset Source
### Primary Dataset
- **Dataset**: Era5-Land Hourly
- **GEE ID**: ECMWF/ERA5_LAND/HOURLY

### Boundary Dataset
- **Boundary Source**: FAO/GAUL/2015/level1  
Used to define the Victoria administrative boundary.

## Time Period
- **Start Date**: 2018-01-01
- **End Date**: 2022-12-31  

This period includes: 
- pre-Black Summer conditions
- Black Summer bushfires (2019-2020)
- post-fire recovery patterns

This improves model training by covering both normal and extreme fire seasons. 

## Temporal Resolution
### Original Frequency
ERA5-Land provides hourly environmental observations.
### Target Frequency
The team modelling decision uses **12-hour prediction intervals**. 
Since ERA5-Land does not directly provide 12-hour data, hourly data is collected first and then aggregated into **12-hour mean intervals**. 
This supports twice-daily fire risk prediction. 

## Defined Features
### Selected Environmental Variables
| Original Feature | Output Column | Meaning | Why It Matters |
|---|---|---|---|
| 'temperature_2m' | 'temperature_2m_c' | Air temperature at 2 metres | High temperature increases fire risk |
| 'skin_temperature' | 'skin_temperature_c' | Land surface temperature | Shows surface heat and dryness |
| 'soil_temperature_level_1' | 'soil_temperature_level_1_c' | Upper soil temperature | Helps represent dry ground conditions |
| 'surface_solar_radiation_downwards' | 'surface_solar_radiation_downwards' | Solar energy reaching ground | Supports fuel drying and hear exposure |
| 'surface_thermal_radiation_downwards' | 'surface_thermal_radiation_downwards' | Thermal radiation reaching surface | Supports heat retention analysis |
| 'u_component_of_wind_10m' | 'u_component_of_wind_10m' | East-West wind movement | Help predict fire spread direction |
| 'v_component_of_wind_10m' | 'v_component_of_wind_10m' | North-SOuth wind movement | Help predict fire spread direction |
| 'timestamp' | 'timestamp' | Time of each 12-hour interval | Allows matching with fire event data |
| '.geo' | '.geo' | Grid cell geometry | Allow spatial mapping across Victoria |

## Processing Workflow
1. Load Victoria boundary using FAO GAUL administrative data
2. Load ERA5-Land hourly dataset from Google Earth Engine
3. Select required environmental features
4. Convert temperature variables from Kelvin to Celsius
5. Aggregate hourly observations into 12-hour mean intervals
6. Create 5km x 5km spatial grid across Victoria
7. Extract mean environmental values for each grid cell
8. Export structured CSV dataset for model training

## Output
This output is designed for direct use in baseline LSTM modelling.
**Output Includes**
- processed environmental veriables
- timestamp
- interval start
- interval end
- spatial grid reference

## Files
| File | Purpose |
|---|---|
| era5_land_dataset_extraction.js | Main Google Earth Engine dataset loader pipeline |
| ERA5_Land_Dataset_Documentation.md | Detailed explanation of dataset logic and defined features |
| README.md | GitHub overview and workflow explanation |

## How to Run
1. Open Google Earth Engine Code Editor
2. Copy era5_land_dataset_extraction.js into a new script
3. Run the script
4. Review progress message in the Console
5. Check the export task in the Tasks tab
6. Run the export task
7. Download the CSV from Google Drive

## Current Testing Scope
To reduce export load and verify correctness, the current export uses January 2018 only.
This is intentional becayse the full 2018-2022 dataset is very large.

After validation the workflow can be extended to: 
- month-by-month exports
- year-by-year exports
- full model-ready dataset generation

## Use Case
This dataset supports:
- baseline LSTM bushfire forecasting
- bushfire risk classification
- spatial fire prediction
- integration with historical fire event labels
- future fire spread modelling

## Limitations
**1. Spatial Resolution is Limited**  
   Even with a 5km x 5km grid, small local conditions like steep slopes, valleys, and microclimates may not be fully captured.
   
**2. 12-Hour Aggregation May Lose Detail**  
   Converting hourly data into 12-hour averages can hide sudden changes like strong wind shifts or rapid temperature increases that affect fire behaviour.
   
**3. Wind Features Need More Processing**  
   The dataset uses raw wind components (u and v) which may later need to be converted into wind speed and wind direction for better modelling.
