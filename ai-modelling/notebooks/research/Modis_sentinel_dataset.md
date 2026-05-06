# DATASET SELECTION 

## 1. Introduction

Effective bushfire detection and prediction require integrating multi-source satellite datasets capturing fire activity, temperature, vegetation, and surface conditions.  

This project uses datasets from Google Earth Engine, combining:
- MODIS (high temporal resolution)
- Sentinel (high spatial resolution)

for a robust fire analytics pipeline.

The variables selected from each dataset are not all available variables, but only those that directly contribute to:

- Fire detection (target/output)  
- Environmental conditions (input features)  
- Model reliability and validation  

---

## 2. MODIS Datasets (High Temporal Resolution)

### 2.1 Active Fire Dataset

- **Dataset:** MOD14A1 / MYD14A1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD14A1  

#### Selected Variables:
- FireMask  
- MaxFRP  
- sample  

#### Why these variables are selected & value they bring:
- FireMask is the most important variable because it directly labels whether a pixel contains fire or not.  
  → Used as the target variable (y) in classification models.  

- MaxFRP provides fire intensity, helping the model differentiate between weak and strong fires.  
  → Improves model understanding of fire severity.  

- sample ensures correct pixel referencing and consistency across observations.  

#### How it helps the project:
This dataset forms the foundation of the pipeline, enabling:

- Training supervised ML models  
- Real-time fire detection  
- Label generation for prediction tasks  

---

### 2.2 Land Surface Temperature (LST)

- **Dataset:** MOD11A1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1  

#### Selected Variables:
- LST_Day_1km  
- LST_Night_1km  
- QC_Day  

#### Why these variables are selected & value they bring:
- LST_Day_1km captures daytime heating, which increases fire risk.  
- LST_Night_1km helps measure heat retention, indicating dry conditions.  
- QC_Day filters unreliable data to avoid noisy inputs.  

#### How it helps the project:
These variables act as predictor features (X) in the model, helping it learn:

- When conditions are suitable for fire ignition  
- How temperature patterns influence fire spread  

---

### 2.3 Vegetation Index (NDVI/EVI)

- **Dataset:** MOD13Q1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1  

#### Selected Variables:
- NDVI  
- EVI  
- SummaryQA  

#### Why these variables are selected & value they bring:
- NDVI measures vegetation density (fuel availability)  
- EVI improves detection in dense vegetation  
- SummaryQA ensures data quality  

#### How it helps the project:
These variables allow the model to understand:

- Fuel load (how much can burn)  
- Vegetation health (dry vs healthy)  

→ Critical for fire risk prediction models  

---

### 2.4 Surface Reflectance (MAIAC)

- **Dataset:** MCD19A1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A1  

#### Selected Variables:
- sur_refl_b01 (Red)  
- sur_refl_b02 (NIR)  
- sur_refl_b07 (SWIR)  

#### Why these variables are selected & value they bring:
These bands are specifically chosen because they are used to compute:

- NDVI → vegetation health  
- NBR → burn severity detection  

#### How it helps the project:
- Enables feature engineering (creating indices like NDVI/NBR)  
- Helps detect burned vs unburned areas  
- Supports post-fire severity analysis  

---

### 2.5 Burned Area Dataset

- **Dataset:** MCD64A1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1  

#### Selected Variables:
- BurnDate  
- Uncertainty  
- QA  

#### Why these variables are selected & value they bring:
- BurnDate provides exact timing of fire occurrence  
- Uncertainty helps assess reliability  
- QA ensures data quality  

#### How it helps the project:
- Used as ground truth labels  
- Helps evaluate model accuracy  
- Supports training for burned area classification models  

---

### 2.6 Radiation Dataset

- **Dataset:** MCD18A1  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD18A1  

#### Selected Variables:
- SWGDN  
- LWGAB  

#### Why these variables are selected & value they bring:
- SWGDN affects surface heating  
- LWGAB influences energy balance and cooling  

#### How it helps the project:
These variables improve the model’s ability to capture:

- Short-term environmental changes  
- Rapid fire spread conditions  

---

## 3. Sentinel Datasets (High Spatial Resolution)

### 3.1 Sentinel-2 Surface Reflectance

- **Dataset:** COPERNICUS/S2_SR  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR  

#### Selected Variables:
- B4  
- B8  
- B12  
- QA60  

#### Why these variables are selected & value they bring:
- B4 (Red) + B8 (NIR) → NDVI  
- B8 + B12 → NBR  
- QA60 → cloud masking  

#### How it helps the project:
- Provides high-resolution features (10–20m)  
- Improves spatial accuracy of predictions  
- Enables detailed burn severity mapping  

---

### 3.2 Sentinel-1 Radar Dataset

- **Dataset:** COPERNICUS/S1_GRD  
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD  

#### Selected Variables:
- VV  
- VH  

#### Why these variables are selected & value they bring:
- VV and VH capture surface structure and moisture  
- Sensitive to changes caused by fire damage  

#### How it helps the project:
- Works in cloud/smoke conditions  
- Ensures continuous data availability  
- Improves model robustness in real-world scenarios  

---

## 4. Overall Dataset

We can select the following variables as:

### Input Features (X):
- Temperature → LST_Day_1km  
- Vegetation → NDVI, EVI  
- Radiation → SWGDN  
- Reflectance → spectral bands  

### Target Labels (y):
- Fire detection → FireMask  
- Burned areas → BurnDate  

### Supporting Features:
- Quality → QA, QC_Day  
- Spatial refinement → Sentinel bands  