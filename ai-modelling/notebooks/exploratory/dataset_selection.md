# DATASET SELECTION 

## 1. Introduction
Effective bushfire detection and prediction require the integration of multiple satellite datasets that capture different environmental factors such as fire activity, temperature, vegetation, and surface conditions. This study utilises datasets from the Google Earth Engine (GEE) catalog, particularly MODIS and Sentinel missions, to develop a comprehensive and data-driven bushfire analysis model. The selected datasets are chosen based on their temporal resolution, spatial resolution, and relevance to fire detection and prediction.

## 2. MODIS Datasets for Fire Detection and Environmental Analysis
MODIS (Moderate Resolution Imaging Spectroradiometer) provides high temporal resolution data, making it highly suitable for near real-time fire monitoring.

### 2.1 Active Fire Dataset
The MODIS active fire products (MOD14A1 for Terra and MYD14A1 for Aqua) are used to detect fire hotspots. These datasets provide daily observations, with combined Terra and Aqua satellites enabling approximately twice-daily monitoring. Fire detection is based on thermal anomalies using mid-infrared (T4) and thermal infrared (T11) bands, making this dataset essential for identifying active fire pixels.

### 2.2 Land Surface Temperature Dataset
The MODIS land surface temperature datasets (MOD11A1 and MYD11A1) provide daily temperature measurements. Temperature is a critical factor influencing fire ignition and spread. These datasets include both daytime and nighttime temperature observations, enabling comprehensive thermal analysis.

### 2.3 Vegetation Dataset (NDVI/EVI)
The MODIS vegetation index dataset (MOD13Q1) provides NDVI and EVI values, which are used to assess vegetation health and fuel availability. Although the dataset has a 16-day temporal resolution, it is essential for understanding vegetation conditions that contribute to fire risk.

### 2.4 Surface Reflectance Dataset
The MODIS MAIAC surface reflectance dataset (MCD19A1) is used to analyse land surface properties and calculate spectral indices such as NDVI and NBR. These indices are important for identifying burned areas and assessing fire severity.

### 2.5 Burned Area Dataset
The MODIS burned area dataset (MCD64A1) provides monthly information on burned regions. This dataset is used to validate fire impact and analyse long-term fire patterns.

### 2.6 Sub-Daily Radiation Dataset
To meet the requirement for high temporal resolution, the MODIS radiation dataset (MCD18A1) is included. This dataset provides data at approximately 3-hour intervals, making it suitable for capturing dynamic environmental conditions that influence fire behaviour.

## 3. Sentinel Datasets for High-Resolution Analysis
While MODIS provides high temporal resolution, Sentinel datasets offer higher spatial resolution, enabling detailed analysis.

### 3.1 Sentinel-2 Surface Reflectance
The Sentinel-2 dataset (COPERNICUS/S2_SR) provides high-resolution optical imagery (10–20 m) and is used for:
- Burn severity mapping  
- Vegetation analysis  
- Calculation of spectral indices such as NDVI and NBR  

Although its temporal resolution is lower (~5 days), its spatial detail significantly enhances analysis accuracy.

### 3.2 Sentinel-1 Radar Dataset
The Sentinel-1 dataset (COPERNICUS/S1_GRD) provides radar imagery that is unaffected by cloud cover or smoke. This makes it particularly useful in bushfire scenarios where optical imagery may be obstructed. It enhances the robustness of the model by ensuring data availability under all weather conditions.

## 4. Summary of Selected Datasets

| Category | Dataset | Purpose | Temporal Resolution |
|---------|--------|--------|-------------------|
| Fire Detection | MOD14A1 / MYD14A1 | Active fire hotspots | Daily (~2x/day) |
| Temperature | MOD11A1 | Surface temperature | Daily |
| Vegetation | MOD13Q1 | NDVI/EVI | 16 days |
| Reflectance | MCD19A1 | Surface reflectance | Daily |
| Burned Area | MCD64A1 | Fire impact validation | Monthly |
| Radiation | MCD18A1 | Environmental dynamics | ~3-hourly |
| High Resolution | Sentinel-2 | Detailed mapping | ~5 days |
| Radar | Sentinel-1 | Cloud-penetrating data | ~6–12 days |

## 5. Justification of Dataset Selection
The selected datasets collectively address all key aspects required for bushfire modelling. MODIS datasets provide high temporal resolution necessary for real-time fire detection and monitoring, while Sentinel datasets enhance spatial accuracy for detailed analysis. The inclusion of sub-daily radiation data ensures that rapidly changing environmental conditions are captured. Additionally, vegetation and temperature datasets support predictive modelling by incorporating key factors influencing fire occurrence.

## 6. Conclusion
The integration of MODIS and Sentinel datasets within the Google Earth Engine platform provides a comprehensive and scalable approach for bushfire detection and prediction. By combining high temporal resolution datasets with high spatial resolution imagery, the model is capable of accurately identifying fire events, analysing burn severity, and predicting future fire risks. This dataset selection forms a strong foundation for developing an effective and reliable bushfire analytics system.
