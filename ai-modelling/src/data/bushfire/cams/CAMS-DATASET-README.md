# CAMS Atmospheric Dataset - Feature Extraction & Documentation
Processing pipeline for the Copernicus Atmosphere Monitoring Service (CAMS) dataset from Google Earth Engine, filtered and aligned for the FireFusion bushfire modelling project in VIctoria.

## Overview
This pipeline collects CAMS atmospheric composition data from Google Earth Engine to support the FireFusion bushfire modelling pipeline.

CAMS provides atmospheric variables related to aerosols, smoke, fine particles, and air quality. 
For this project, CAMS is mainly used as a complementary atmospheric dataset. 

This dataset is intended to support: 
- Validation of fire events against smoke and air quality
- Confirming active or recent fire/smoke conditions
- Short-term spread context when fire activity is already nearby
- Smoke and air quality impact analysis

The final dataset is designed to align with the project's 5 km grid and 12-hour timestamp structure so it can be merged with other modelling datasets. 

## Inputs
- **'ECMWF/CAMS/NRT'**:  Copernicus Atmospheric Monitoring Service Global Near-Real-time dataset from Google Earth Engine
- **Victoria boundary**: used to restrict extraction to Victoria, Australia
- **5 km grid setup**: data will be exported using a 5 km grid
- **Date range**: 2018 to 2022

## Outputs
The final output should have one row for each grid cell and timestamp.

**Output Features**
| Feature | Type | Description |
|---|---|---|
| grid_id | str/int | Unique ID for each 5 km grid cell |
| timestamp | datetime | 12-hour timestamp, aligned with the modelling dataset|
| cams_aod_550 | float | Aerosol Optical Depth at 550nm. This can show aerosol, smoke, haze, or particle loading in the atmosphere |
| cams_pm25 | float | Fine particulate matter, which can show smoke and air quality impact |

## Selected CAMS Features
For the main 2018-2022 dataset, the selected CAMS features are: 
- cams_aod_550
- cams_pm25

These were selected because they are available across the full project period. 

#### AOD at 550 nm
| Item | Detail |
|---|---|
| Output name | cams_aod_550 |
| GEE band | total_aerosol_optical_depth_at_550nm_surface |
| Main use | Smoke, haze, and aerosol indicator |

AOD stands for Aerosol Optical Depth.
It shows how much aerosol or particle matter is in the atmosphere.
For bushfire work, this can help show whether there is smoke or haze around a fire event.
However, AOD is not only caused by bushfires. It can also come from dust, pollution, sea salt, or other sources.
Because of that, it should be used as a supporting signal, not as proof of fire by itself. 

#### PM2.5
| Item | Detail |
|---|---|
| Output name | cams_pm25 |
| GEE band | particulate_matter_d_less_than_25_um_surface |
| Main use | Fine particle and air-quality indicator |

PM2.5 means fine particulate matter in the air. Bushfire smoke often contains fine particles, so PM2.5 is useful for checking smoke impact and air quality conditions. It can also help confirm whether a recorded fire event has related air quality signal. 

## Why These Features Were Selected
Our project uses data from 2018 to 2022, so it is better to choose features that are available across the whole period. 
For CAMS in GEE, the safest features are cams_aod_550 and cams_pm25. 

Other useful CAMS features, such as PM10, carbon monoxide, black carbon AOD, and organic matter AOD, are only available from 1 July 2021 onward.
If those features were included in the 2018-2022 dataset, many rows before July 2021 will have missing values.
That would make the dataset harder to clean, merge, and use for model training. 

Because of that, AOD at 550nm and PM2.5 are selected as the core CAMS features.

## Processing Steps
### 1. Load CAMS Dataset
- Load the CAMS ImageCollection from Google Earth Engine
- Filter the dataset to the project period, 2018-2022
- Filter the dataset to Victoria, Australia

### 2. Select Relevant Bands 
Select the two CAMS features: 
- total_aerosol_optical_depth_at_550nm_surface
- particulate_matter_d_less_than_25_um_surface

Rename them to shorter project names: 
- cams_aod_550
- cams_pm25

### 3. Align Time Format 
- Align CAMS data to a 12-hour timestamp structure
- Match the same time format used in the ERA5-Land dataset
- This makes it easier to merge later using grid_id and timestamp

### 4. Align With 5 km Grid
- Map CAMS values to the FireFusion 5 km grid
- Assign each row to a grid_id
- Keep the output format consistent with the other modelling datasets

### 5. Export Dataset
Export the processed CAMS data as a CSV file.

## Key Parameters
| Parameter | Value | Notes |
|---|---|---|
| Dataset | ECMWF/CAMS/NRT | CAMS dataset from GEE |
| Region | Victoria, Australia | Same project area as FireFusion |
| Time Period | 2018-2022 | Matches the main model training period |
| Temporal format | 12-hour interval | Matches weather data structure |
| Spatial format | 5 km grid | Matches the other datasets grid |
| Core features | AOD at 550 nm, PM2.5 | Available across the full period |
| Output format | CSV | Used for merging and modelling |

## Use Case
The CAMS dataset adds smoke and air-quality context to the FireFusion project.

### Fire Event Validation
CAMS can help check whether recorded fire events also show smoke or air-quality signals.

For example: 
- The fire event label shows that a fire occurred
- cams_aod_550 or cams_pm25 increases around the same time or area

This can help support the fire event record.

### Active Fire or Smoke Confirmation
CAMS can help confirm whether there may be active or recent smoke conditions near a fire area. 

This is useful because AOD and PM3.5 can increase when smoke is present.

### Short-Term Spread Context
CAMS may support short-term spread modeling if a fire is already active nearby. 

For example, if nearby grid cells show high smoke or high particle levels. It may provide useful context that fire activity is already happening in that area. 

However, CAMS should not be used alone to predict where a new fire will start. 

### Smoke and Air-Quality Impact
CAMS can help analyse smoke and air-quality effects from fire activity.
- **cams_pm25**: useful for fine particle pollution
- **cams_aod_550**: useful for broader smoke, haze, or aerosol loading

## Limitations
- **Not a main ignition predictor**: AOD and PM2.5 are more related to smoke and air-quality conditions than direct causes of fire ignition.
- **Not bushfire-specific**: AOD and PM2.5 can also come from dust, pollution, sea salt, or other non-fire sources. 
- **Coarser spatial resolution**: CAMS has a 44.5km grid compared to FireFusion's 5km grid, so nearby grid cells may have similar or identical values. 
- **Limited full-period features**: For 2018-2022, the necessary consistent features are only AOD at 550 nm and PM2.5.
- **Other useful features are not available for the full period**: PM10, carbon monoxide, black carbon AOD, and organic matter AOD are only available from 1 July 2021 onwards.
