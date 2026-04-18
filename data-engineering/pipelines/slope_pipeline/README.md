# Terrain Slope Dataset Pipeline

## Overview
This pipeline generates a terrain slope dataset for Victoria, Australia using the SRTM (Shuttle Radar Topography Mission) elevation data. The dataset is used to support bushfire risk modelling by providing topographic features.

---

## Dataset Description
This dataset shows terrain characteristics across Victoria using a grid of sampled geographic coordinates. For each coordinate:
- Elevation is extracted from SRTM data
- Slope is computed from elevation differences

Slope is a derived variable that describes how steep the terrain is at each location.

---

## Data Ingestion

The pipeline includes a data ingestion step where elevation data is retrieved from the SRTM dataset based on generated geographic coordinates.

This involves:
- Querying elevation data for each latitude and longitude point  
- Collecting raw elevation values from the source  
- Preparing the data for further transformation  

This ensures the data can be consistently retrieved and reproduced when the pipeline is executed.

---

## Variables

- **latitude**: Geographic latitude of the point (degrees)  
- **longitude**: Geographic longitude of the point (degrees)  
- **elevation**: Height above sea level (meters)  
- **slope**: Terrain steepness calculated from elevation differences (unitless)

---

## Slope Interpretation

Slope indicates how steep the terrain is:

- **Slope ≈ 0** → Flat terrain  
- **Slope 0 – 0.5** → Gentle incline  
- **Slope 0.5 – 1** → Moderate incline  
- **Slope > 1** → Steep terrain  

A higher slope value means the terrain rises more sharply. This is important for bushfire modelling because fire spreads faster uphill due to heat rising and preheating vegetation.

---

## Data Source

- **Dataset**: SRTM (Shuttle Radar Topography Mission)  
- **Provider**: NASA  
- **Type**: Digital Elevation Model (DEM)  
- **Coverage**: Global (subset used for Victoria)

---

## Pipeline Process

1. Generate a grid of latitude and longitude points across Victoria  
2. Extract elevation values using SRTM data  
3. Clean data by removing null or invalid values  
4. Compute slope from elevation differences  
5. Store results in a structured dataset  

---

## Data Scope

- **Region**: Victoria, Australia  
- **Coverage**: Grid-based sampling of coordinates  
- **Resolution**: Controlled by step size parameter in the pipeline  


---

## Workflow

1. Data Ingestion  
   - Retrieve elevation data from SRTM using geographic coordinates  

2. Data Cleaning  
   - Remove null and invalid values  

3. Feature Engineering  
   - Compute slope from elevation differences  

4. Output  
   - Generate structured dataset with slope values
   
---

## Integration

This dataset is designed to be integrated with other features such as:
- Weather data
- Vegetation indices
- Fire history data

---

## Scalability

This pipeline is designed to be flexible and scalable:

- The region can be changed by modifying coordinate boundaries  
- The resolution can be adjusted using grid step size  
- The same pipeline can be applied to other regions or datasets  
- Additional topographic features (e.g., aspect) can be added  

---

## Data Quality and Validation

- Null or missing elevation values are removed  
- Invalid values (e.g., ocean points) are filtered  
- Dataset is generated programmatically to ensure reproducibility  

---
**Contributor:** Nouman Ullah Khan
