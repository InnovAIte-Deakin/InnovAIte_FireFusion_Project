# Land Surface Temperature (LST) – Research Findings for Wildfire Prediction

## 1. Introduction
This research evaluates the role of Land Surface Temperature (LST) in wildfire prediction and examines how it should be incorporated within a multi-source modelling pipeline. The analysis is based on reviewing recent studies to understand how temperature interacts with meteorological, vegetation, and spatial variables in predicting fire occurrence and spread.

---

## 2. Evidence from Existing Studies

### MODIS vs VIIRS: Implications for Feature and Target Design
Studies comparing MODIS and VIIRS show that predictive performance varies significantly depending on how datasets are used. While MODIS-derived inputs retain useful predictive structure, configurations using VIIRS (VNP14) as the target consistently outperform those using MODIS fire masks (MOD14). This indicates that MOD14 introduces instability as a supervisory signal, whereas VIIRS aligns more closely with observed fire patterns.

**Key implication:**
- Dataset suitability depends on its role  
- MODIS → better as a feature source  
- VIIRS → better as a target variable  

---

### LST within Wildfire Prediction Models
Across studies, LST is consistently included as a feature representing surface thermal conditions. It captures the energy state of vegetation and soil, which is linked to fuel drying and ignition potential. However, LST does not function as an independent predictor. Its contribution becomes meaningful only when combined with variables representing moisture, vegetation condition, and atmospheric dynamics.

**Key implication:**
- LST should be treated as part of a broader environmental feature set, not a dominant variable  

---

### Importance of Feature Interaction
High-performing models do not rely on individual variables but instead integrate multiple feature groups:
- Thermal  
- Meteorological  
- Vegetation  
- Spatial  

Predictive accuracy improves when these variables are combined, as wildfire behaviour is governed by their interaction rather than isolated effects.

---

### Temporal and Resolution Considerations
- **MODIS LST**
  - High spatial resolution  
  - Daily observations  

- **ERA5**
  - Lower spatial resolution  
  - Sub-daily temporal resolution  

Studies suggest combining both enables models to capture:
- Spatial variability  
- Short-term temporal dynamics  

---

## 3. Position of LST Relative to Other Variables

| Aspect                | Contribution of LST                          | Limitation                                      |
|----------------------|---------------------------------------------|------------------------------------------------|
| Thermal representation | Captures surface heating conditions        | Does not capture atmospheric dynamics          |
| Fuel condition        | Indirectly reflects fuel drying            | Requires vegetation context                    |
| Temporal behaviour    | Useful with transformations (lag, variation)| Raw values less informative                    |
| Predictive role       | Supporting feature                         | Not sufficient independently                   |

---

## 4. Key Observations from the Analysis

- LST is consistently used across wildfire prediction models but does not dominate feature importance  
- Its predictive value emerges through interaction with:
  - Moisture  
  - Vegetation  
  - Atmospheric variables  
- Temporal transformations (e.g., lagged values, day–night differences) enhance usefulness  
- Dataset alignment across spatial and temporal dimensions is essential  

---

## 5. Implications for Dataset Selection

An effective dataset configuration should include:

- **MODIS LST (MOD11A1)** → surface thermal conditions  
- **ERA5-Land** → meteorological variables (humidity, wind, precipitation)  
- **VIIRS (VNP14)** → fire occurrence (target variable)  
- **Vegetation indices (NDVI / LAI)** → fuel availability  
- **Terrain data (DEM, land cover)** → spatial influences  

### Required alignment variables:
- Latitude  
- Longitude  
- Time  