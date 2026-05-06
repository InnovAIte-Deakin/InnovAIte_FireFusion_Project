![](media/05ff9d4b456c2ff4dbbeca40c86db297.emf)

# 1. Overview & Purpose

This is a documentation of the findings of the task to research and evaluate primarily the atmospheric datasets in the Google Earth Engine (GEE) Atmosphere Catalogue and other publicly accessible repositories. The objective was to identify which datasets and atmospheric variables are most relevant to FireFusion's bushfire spread and risk forecasting model, while being realistic about what is achievable within the Capstone timeframe. From the atmospheric variables this document concentrates on heavily **non-meteorological atmospheric variables** such as surface pressure, aerosols, atmospheric stability, and other smoke-related signals.

# 2. Google Earth Engine Atmospheric Catalogue Dataset Overview

| Dataset                                                                                                     | GEE ID / Link                                                                                                                    | Key Variables                                                                                                                                                                                                  | Temporal Res. | Spatial Res. | Coverage       | Relevance Notes                                                                                                                                                                                                                                        |
|-------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|--------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ERA5-Land Hourly<br>(Potential Primary Source)                                                              | ECMWF/ERA5_LAND/HOURLY<br><https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY>                   | Surface pressure (sp), Mean sea-level pressure (msl), Boundary layer height, Soil moisture (all layers), Evaporation.                                                                                          | Hourly        | \~9 km       | 1950–present   | Good as a primary source for surface pressure and boundary layer height; also provides soil moisture used to compute drought/fuel dryness                                                                                                              |
| ERA5 Hourly<br>(Potential Source)                                                                           | ECMWF/ERA5_HOURLY<br><https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY>                             | Mid-atmosphere pressure map, Boundary layer pressure, Full pressure-level atmosphere (The complete vertical 3D slice of the atmosphere at every altitude) and total precipitation / water vapour in atmosphere | Hourly        | \~31 km      | 1940–present   | Gives a broader coverage of atmosphere. Could be used for upper-level **synoptic pressure patterns** (e.g. ridges and troughs at 500 hPa) that set up dangerous fire-weather conditions. This data isn't in ERA5-Land.                                 |
| MODIS MAIAC AOD<br>(Potential Source for Aerosol variable)                                                  | MODIS/061/MCD19A2_GRANULES<br>Link: <br><https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES> | Aerosol Optical Depth (AOD) over land at 470 nm and 550 nm — MAIAC algorithm, optimised for variable land surfaces                                                                                             | Daily         | 1 km         | 2000–present   | BEST aerosol dataset for this project: detects smoke plumes from active fires; AOD spikes are a corroborating signal for fire event detection and post-fire smoke footprint                                                                            |
| Sentinel-5P Aerosol Index<br>(Potential Complimentary source for Aerosol Variable & confirming fire origin) | COPERNICUS/S5P/OFFL/L3_AER_AI<br><https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_AER_AI>     | UV Aerosol Index — detects UV-absorbing particles like smoke, dust, and volcanic ash                                                                                                                           | Daily         | \~7 km       | 2018–present   | Sensitive to smoke-type aerosols from biomass burning (vegetation fires); Works alongside MODIS AOD to confirm fire-origin smoke - if both datasets show elevated readings at the same time and place, you can be much more confident a fire occurred. |
| MERRA-2 Aerosols<br>(Potential Complimentary source for Aerosol Variable & confirming fire origin)          | NASA/GSFC/MERRA/aer/2<br><https://developers.google.com/earth-engine/datasets/catalog/NASA_GSFC_MERRA_aer_2>                     | Black carbon surface mass density, Organic carbon, Dust, Sea salt, SO4 (Sulphate) aerosol mass density                                                                                                         | Hourly avg    | \~55 km      | 1980–present   | Longer history than Sentinel-5P, letting you train models on fire events before 2018. Black carbon is a direct chemical fingerprint of fire smoke. Complements MODIS AOD for identifying fire-related aerosols.                                        |
| MERRA-2 Single-Level                                                                                        | NASA/GSFC/MERRA/slv/2<br><https://developers.google.com/earth-engine/datasets/catalog/NASA_GSFC_MERRA_slv_2>                     | Surface pressure, Sea-level pressure, Boundary layer height, Specific humidity                                                                                                                                 | Hourly avg    | \~55 km      | 1980–present   | A completely independent source for the same pressure variables as ERA5-Land. Lower resolution, but useful for double-checking ERA5-Land results and catching potential errors or biases.                                                              |
| CAMS Near Real-Time                                                                                         | ECMWF/CAMS/NRT<br><https://developers.google.com/earth-engine/datasets/catalog/ECMWF_CAMS_NRT>                                   | Organic matter, black carbon, dust, sea salt, SO₂, CO — surface concentrations of all major aerosol types                                                                                                      | 3-hourly      | \~40 km      | Near real-time | Best suited for a future operational smoke-tracking dashboard. Shows aerosol composition shortly after it's measured, making it useful for monitoring where smoke is spreading from active fires in real time.                                         |
| Sentinel-5P CO<br>(Potential Complimentary source for fire signals)                                         | COPERNICUS/S5P/OFFL/L3_CO<br><https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_CO>             | Carbon monoxide (CO) total column density [mol/m²]                                                                                                                                                             | Daily         | \~7 km       | 2018–now       | CO is directly produced by burning. Column density above \~0.04 mol/m² is a strong sign of active fire smoke overhead. One of the cleanest signals you can use to confirm a fire event is happening..                                                  |
| AIRS Atmospheric Profiles                                                                                   | NASA/AIRS/006/L3<br><https://developers.google.com/earth-engine/datasets/catalog/NASA_AIRS_006_L3_RetStd_v006>                   | Temperature and humidity vertical profiles, Total column CO, Surface air temperature                                                                                                                           | Daily         | \~111 km     | 2002–present   | Describes how temperature and moisture change with altitude. Too coarse and complex for early project stages — flag this for future modelling of pyroconvection (fire-driven thunderstorms).                                                           |

# 3. Primary Dataset Source Identified - ERA5-Land & ERA5

## 3.1 What is ERA5?

ERA5 stands for ECMWF Reanalysis version 5. ECMWF (the European Centre for Medium-Range Weather Forecasts) is an independent intergovernmental organisation based in Reading, UK, widely regarded as producing the world's most respected weather and climate datasets.

ERA5 is a reconstruction of what the atmosphere looked like at every point on Earth going back to 1940.

The process works in three steps:

1.  Every available observation from that time period is collected — weather stations, weather balloons, satellites, aircraft, ships and buoys
2.  These observations are fed into a numerical weather prediction model that fills gaps between sparse observations using the laws of atmospheric physics
3.  The output is a complete, consistent gridded dataset — every variable, at every grid cell, at every time step, with no missing values. The result is a best estimate of what the atmosphere was doing at any point in history.

## 3.2 ERA5 vs ERA5-Land

ERA5 and ERA5-Land are produced by the same ECMWF system but serve different purposes. **ERA5** covers the full atmosphere and surface at approximately 31 km grid spacing. **ERA5-Land** is ERA5 rerun at higher resolution with a more detailed land surface model, covering only the land surface at approximately 9 km grid spacing. For bushfire modelling, ERA5-Land is the better choice because it has finer resolution and is optimised for near-surface variables that matter most such as the 2m temperature, 10m wind, and dewpoint that directly drive fire weather.

Both datasets provide hourly temporal resolution extending from 1950 to the present day.

## 

# 4.Atmospheric Variables — Assessment & Justification

This documentation looks beyond the standard meteorological variables (surface air temperature, wind, precipitation), looking at **non-meteorological atmospheric variables** in relevant to the bushfire modelling. The table below assesses each variable, explains what it measures, and provides reasons for inclusion or exclusion given the current sprint scope.

| Variable                                   | What it measures                                                                                                                                               | Dataset                                     | Priority                                 | Why use it (with evidence)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Caveats                                                                                                                                                                                                                                                                               |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Surface Pressure                           | Weight of the atmosphere pressing down at ground level, measured in hPa. Changes in surface pressure indicate approaching weather systems.                     | ERA5-Land (ECMWF/ERA5_LAND/HOURLY)          | **Moderate**                             | Pressure patterns at the synoptic (continent-wide) scale set up the dangerous fire-weather conditions characteristic of southern Australian fire events. In Victoria, the deadly hot and dry northerly winds ahead of cold fronts are driven by exactly these pressure configurations. Some ML fire spread studies include surface pressure as a secondary atmospheric feature.<br>References:<br>[arXiv 2025 (wildfire spread deep learning)](https://arxiv.org/html/2505.17556v1)<br>[Harris et al. 2019 (Victorian fire weather)](https://mssanz.org.au/modsim2019/H7/harris.pdf) |  Only include if feature importance testing in model confirms it adds real predictive value beyond the core meteorological variables (temperature, humidity, wind).                                                                                                                   |
| Aerosol Optical Depth (AOD)                | How much sunlight is scattered or absorbed by particles in the air (smoke, dust). Higher AOD = smokier atmosphere.                                             | MODIS MAIAC (MODIS/061/MCD19A2_GRANULES)    | **Moderate**                             | AOD spikes sharply over and downwind of active Australian fires. During the 2019-20 Black Summer, AOD values over southeastern Australia reached 2.74, far above background levels. Useful as a corroborating signal to confirm fire event dates in training data.<br>References:<br>[Sci. Reports 2021 (Black Summer AOD)](https://www.nature.com/articles/s41598-021-91547-y)                                                                                                                                                                                                      | AOD tells you smoke is present, not that a fire will start. Best used for detection and cross-validation of event dates, not as a predictive fire-weather variable. Could be of use in training data.                                                                                 |
| UV Aerosol Index (Absorbing Aerosol Index) | Detects UV-absorbing particles in the atmosphere such as smoke, dust, and volcanic ash. A positive index value indicates absorbing aerosols are present.       | Sentinel-5P (COPERNICUS/S5P/OFFL/L3_AER_AI) | **Optional Sprint 1 / Valuable later**   | Particularly sensitive to smoke from vegetation fires because biomass burning produces strongly UV-absorbing black carbon particles. Works alongside MODIS AOD to confirm fire-origin smoke — if both datasets show elevated readings at the same time and place, you can be much more confident a fire occurred. Useful for active-fire event corroboration.<br>References:<br>[Sci. Reports 2021 (Black Summer aerosols)](https://www.nature.com/articles/s41598-021-91547-y)                                                                                                      | Not a fire predictor — best used as a cross-validation signal for confirming event dates. Dust and volcanic ash can also elevate the index, so elevated values are not unambiguously fire-origin without corroboration from AOD or CO. Record starts 2018. Recommended for Sprint 2+. |
| Black Carbon Surface Mass Density          | Mass of black carbon (soot) particles per unit volume near the surface. Black carbon is produced almost exclusively by combustion of fossil fuels and biomass. | MERRA-2 Aerosols (NASA/GSFC/MERRA/aer/2)    | **Optional Sprint 1 / Valuable later**   | Black carbon is a direct chemical fingerprint of fire smoke. Spikes in surface black carbon mass density are a strong indicator that smoke from biomass burning is present at ground level. MERRA-2 provides data back to 1980, making it valuable for training models on fire events before Sentinel-5P's 2018 start date.<br>References:<br>[McNorton et al. 2025 (data-driven fire prediction)](https://www.nature.com/articles/s41467-025-58097-7)<br>[Sci. Reports 2021 (Black Summer aerosols)](https://www.nature.com/articles/s41598-021-91547-y)                            | Coarser spatial resolution (\~55 km) than MODIS or Sentinel-5P. MERRA-2 is a reanalysis product, so black carbon values are model-estimated rather than directly observed. Best used alongside MODIS AOD rather than as a standalone signal.                                          |
| Carbon Monoxide Column (CO)                | Total amount of CO gas in a vertical column of atmosphere above a point. CO is produced directly when things burn.                                             | Sentinel-5P (COPERNICUS/S5P/OFFL/L3_CO)     | **Moderate - Useful for fire detection** | CO column density spiking above roughly 0.04 mol/m2 is a strong and direct indicator of active fire smoke. Because CO is chemically produced by combustion, it provides a near-unambiguous fire signal. Very useful for confirming that event dates in your dataset are correct.<br>References:<br>[Sci. Reports 2021 (Black Summer)](https://www.nature.com/articles/s41598-021-91547-y)                                                                                                                                                                                            | Record only goes back to 2018. Good for validation but not long enough to drive prediction model training. Could also prioritise for next semester as a detection/validation layer rather than a model input feature.                                                                 |
| Geopotential Height at 500 hPa             | How high you need to go before air pressure drops to 500 hPa (mid-troposphere). Reveals large-scale pressure and wind patterns across the continent.           | ERA5 (not ERA5-Land) (ECMWF/ERA5_HOURLY)    | **Low (Sprint 1)**                       | Blocking high-pressure systems and ridges at 500 hPa are linked to sustained hot, dry conditions over southern Australia — the precursor pattern to major fire weather events. Important context for understanding why dangerous fire days occur.<br>References:<br>[Di Giuseppe et al. 2020 (ERA5 fire danger)](https://www.nature.com/articles/s41597-020-0554-z)                                                                                                                                                                                                                  | Not in ERA5-Land; requires a separate dataset pull. Adds preprocessing complexity. Defer unless model specifically targets synoptic-scale atmospheric pattern recognition or operational forecasting.                                                                                 |
| Trace Gases (NO2, SO2, CH4)                | Atmospheric pollutant gases measured in the air column above a location.                                                                                       | Sentinel-5P / CAMS                          | **Not relevant (Sprint 1)**              | These gases are emitted during fire events and are used in emissions accounting and air quality research. Not meaningful inputs for fire prediction or spread modelling.                                                                                                                                                                                                                                                                                                                                                                                                             | Avoid for Sprint 1 entirely. Only relevant if the project pivots to smoke dispersion and air quality health impacts.                                                                                                                                                                  |

## Small Note on Surface Pressure & Synoptic Patterns

The synoptic pattern associated with Victoria's worst fire days typically involves: a broad high-pressure ridge extending from the Australian interior across the north of the state, driving hot, dry northerly winds; a strong cold front approaching from the southwest, associated with a low-pressure system in the Southern Ocean. As the front passes, winds rapidly shift from northerly to southwesterly, dramatically changing fire spread direction. This sudden wind change is a defining feature of fire disasters in Victoria.

Surface and sea-level pressure fields capture the presence and movement of these synoptic systems in the **ERA5-Land** record. Including pressure in the feature set allows the model to learn, at least partially, the large-scale atmospheric setup associated with extreme fire days — something wind and temperature alone cannot fully encode without the broader pressure context.

## Small Note on AOD Measures

Aerosol Optical Depth (AOD) is a dimensionless quantity describing how opaque the atmosphere is to light due to suspended particles. The physical definition is the logarithmic ratio of incident solar radiation to transmitted solar radiation through the atmospheric column. In practical terms it is a haziness score:

• AOD \< 0.1 — clean, clear atmosphere; almost all sunlight reaches the ground

• AOD 0.1 to 0.5 — moderate haze; dust, sea spray, or light smoke

• AOD 0.5 to 1.0 — heavy haze or smoke; visibility noticeably reduced

• AOD \> 1.0 — very thick aerosol load; extreme smoke or dust conditions

During the 2019-2020 Black Summer, peak AOD over eastern Australia reached 2.74. By comparison, the global annual average background AOD is approximately 0.12.

The GEE dataset MODIS/061/MCD19A2_GRANULES uses the Multi-Angle Implementation of Atmospheric Correction (MAIAC) algorithm. MAIAC is specifically tuned for retrievals over land surfaces with variable reflectance characteristics — bare soil, dry grassland, forest — which are common across Victoria's fire-prone regions. Older AOD algorithms struggled over bright surfaces, leading to systematic overestimates. MAIAC addresses this by using a time-series-based surface characterisation algorithm.

MAIAC provides daily AOD at 1 km resolution, fitting neatly within the 250 m to 1 km grid resolution planned for the FireFusion model

# 5. External Datasets Beyond GEE

The following peer-reviewed studies and official reports were reviewed in preparing this documentation. They are recommended reading for the FireFusion team to understand the current state of atmospheric data use in fire research.

| **Dataset**                                        | **Platform**                                      | **Contents**                                                                                                                                                                                   | **Coverage**      | **Temporal Res.**                              | **Relevance to FireFusion**                                                                                                                                                | **Verified Link**                                                                                                                                                                                                        |
|----------------------------------------------------|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Next Day Wildfire Spread**                       | Kaggle                                            | ERA5 weather + MODIS fire perimeters + SRTM topography; 12 features including temperature, humidity, wind, vegetation, population density                                                      | USA (continental) | Daily                                          | Directly reusable for training spread models; feature set aligns with FireFusion's ERA5 approach. Note: coverage is US-only, not Australian.                               | [kaggle.com: Next Day Wildfire Spread](https://www.kaggle.com/datasets/fantineh/next-day-wildfire-spread)<br>*Verified active. Original dataset by Huot et al. (2022), IEEE TGRS.*                                       |
| **Fires from Space: Australia**                    | Kaggle                                            | NASA FIRMS MODIS C6 and VIIRS 375m active fire detections over Australia and New Zealand, including brightness temp, FRP, confidence                                                           | Australia / NZ    | Sub-daily (Aug 2019 to Jan 2020)               | Historical Australian fire location data covering Black Summer onset; useful as ground truth for spatial fire occurrence.                                                  | [kaggle.com: Fires from Space: Australia](https://www.kaggle.com/datasets/carlosparadis/fires-from-space-australia-and-new-zeland)<br>*Verified active. 219,604 fire detections. Note: covers Black Summer period only.* |
| **Wildfire Prediction Dataset (Satellite)**        | Kaggle                                            | Satellite images labelled as fire / no-fire for binary classification tasks                                                                                                                    | North America     | Per-event                                      | Pre-labelled binary classification dataset; useful for benchmarking fire detection classifiers. Not Australian data.                                                       | [kaggle.com: Wildfire Prediction Dataset](https://www.kaggle.com/datasets/abdelghaniaaba/wildfire-prediction-dataset)<br>*Verified active. Image-based; not tabular weather data.*                                       |
| **NASA FIRMS Active Fire**                         | NASA EARTHDATA / LANCE                            | Near real-time and historical MODIS/VIIRS active fire detections: fire radiative power (FRP), coordinates, brightness temperature, confidence                                                  | Global            | Sub-daily (within 3 hours of detection)        | Gold standard for active fire locations; integrates directly with GEE; free API access. Primary ground-truth source for FireFusion.                                        | [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/download/)<br>*Verified active. Free API and bulk download available.*                                                                               |
| **National Bushfire Extents (Historical)**         | Digital Atlas of Australia (Geoscience Australia) | Mapped fire scar extents for historical Australian bushfires from 1899 to 2023, including Black Summer 2019-20; available as file geodatabase (FGDB)                                           | Australia         | Per-event (historical archive)                 | Official historical fire perimeter data from Geoscience Australia; essential for training and validating spread models in the Australian context.                          | [digital.atlas.gov.au: National Bushfire Data](https://digital.atlas.gov.au/pages/national-bushfire-data)<br>*Verified active. Also available via data.gov.au.*                                                          |
| **BoM Historical Fire Weather (FFDI Climatology)** | Bureau of Meteorology (BoM)                       | Gridded FFDI climatology (1950-2016), daily temperature, relative humidity, wind speed, KBDI/Drought Factor from BoM weather stations. Station data also downloadable via Climate Data Online. | Australia         | Daily (station data); Monthly climatology maps | Ground-truth fire weather observations; useful for validating ERA5-Land reanalysis data against real station readings. FFDI is the canonical Australian fire danger index. | [bom.gov.au: FFDI Climatology](https://www.bom.gov.au/climate/maps/averages/ffdi/)<br>*Verified active. Station data via bom.gov.au/climate/data/*                                                                       |
| **NOAA Global Surface Summary of Day (GSOD)**      | NOAA NCEI / also on Kaggle                        | Station-level daily summaries: mean temp, dew point, wind speed, pressure, precipitation, visibility from 9,000+ global stations. Data from 1929 to present.                                   | Global            | Daily                                          | Point-level observations useful for bias-correcting ERA5; sparse in regional Victoria but covers major Australian cities and airports.                                     | [ncei.noaa.gov: GSOD](https://www.ncei.noaa.gov/access/search/data-search/global-summary-of-the-day)<br>*Verified active. Also available on Kaggle and AWS S3.*                                                          |
| **Copernicus Climate Data Store (CDS)**            | ECMWF / Copernicus                                | ERA5, ERA5-Land, CAMS reanalysis; same data as GEE but downloadable directly via Python API (cdsapi). Supports bulk downloads for entire fire seasons.                                         | Global            | Hourly (ERA5/ERA5-Land)                        | Alternative access path to ERA5-Land if GEE quotas or compute limits are hit; allows bulk NetCDF downloads for offline processing of entire fire seasons.                  | [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/)<br>*Verified active. Free account required. Python: pip install cdsapi*                                                                                  |

# 6. Key Research References

## 6.1 Atmospheric Reanalysis & Fire Danger

ERA5-based global meteorological wildfire danger maps (Di Giuseppe et al., 2020, Nature Scientific Data)

*Describes the GEFF fire danger reanalysis product built on ERA5; validates ERA5 as the standard atmospheric input for global fire danger indices including FWI. Highly relevant as a methodology reference.*

**Link:** <https://www.nature.com/articles/s41597-020-0554-z>

Global data-driven prediction of fire activity (McNorton et al., 2025, Nature Communications)

*Demonstrates ERA5-Land-driven ML outperforming traditional fire weather indices by incorporating fuel data; emphasises data quality over model complexity. Key reference for FireFusion's overall modelling approach.*

**Link:** <https://www.nature.com/articles/s41467-025-58097-7>

***

## 6.2 Australia & Victoria-Specific

Bushfire Severity Modelling Across Australia Using GEE and ML (arXiv, 2024)

*Uses ERA5-Land + NASA SMAP on GEE for Australian fire severity modelling; directly replicable GEE workflow relevant to FireFusion.*

**Link:** <https://arxiv.org/html/2410.02963>

Victorian Fire Weather Trends — VicClim Dataset (Harris et al., MODSIM 2019)

*Victoria-specific analysis at 4 km / hourly resolution; finds r=0.79 correlation between FFDI 90th percentile and log burned area in Victoria. Direct evidence for FFDI-linked variable selection.*

**Link:** <https://mssanz.org.au/modsim2019/H7/harris.pdf>

Australian fire weather — FFDI (Bureau of Meteorology)

*Official BoM documentation on FFDI calculation: temperature, relative humidity, wind speed and Drought Factor (KBDI). The canonical reference for Australian fire danger variables.*

**Link:** <https://www.bom.gov.au/climate/maps/averages/ffdi/>

***

## 6.3 Fire Spread Modelling with ERA5-Land

Wildfire Spread Forecasting with Deep Learning (arXiv, 2025)

*Uses ERA5-Land variables (temperature, dewpoint, wind u/v, surface pressure, precipitation, solar radiation) as the complete atmospheric feature set for fire spread prediction. Very closely aligned with FireFusion's approach.*

**Link:** <https://arxiv.org/html/2505.17556v1>

Wildfire Spreading Prediction Using Multimodal Data and DNNs (Shadrin et al., Scientific Reports, 2024)

*Downloads ERA5-Land and aggregates min/max per fire event; combines with elevation, slope, aspect, land cover — a strong template for FireFusion's multi-source feature engineering.*

**Link:** <https://www.nature.com/articles/s41598-024-52821-x>

Geo-Spatial Data and ML for Wildfire Occurrence Prediction (Scientific Reports, 2025)

*Retrieves 6 ERA5-Land variables at 3-hourly resolution for occurrence prediction; adds day-of-year as seasonal feature — directly applicable to FireFusion's feature engineering.*

**Link:** <https://www.nature.com/articles/s41598-025-94002-4>

***

## 6.4 Aerosol & AOD

2019-2020 Australian Bushfire Air Particulate Pollution and AOD (Scientific Reports, 2021)

*Documents Black Summer AOD reaching 2.74 — confirms AOD as a strong bushfire signal in Australian context; relevant for future FireFusion detection layer.*

**Link:** <https://www.nature.com/articles/s41598-021-91547-y>

Satellite-Based MAIAC AOD During the 2020 Wildfire Season (ScienceDirect, 2024)

*ℹ Evaluates MODIS MAIAC Collection 6.1 performance during wildfire events; r=0.91 for medium smoke, r=0.90 for heavy smoke vs AERONET ground truth. Validates MAIAC for fire-event AOD retrieval.*

**Link:** <https://www.sciencedirect.com/science/article/abs/pii/S0048969724012610>

Assimilation of AOD into Warn-on-Forecast System for Smoke (WoFS-Smoke) (AGU, 2022)

*ℹ Shows that AOD assimilation into forecast systems indirectly improves temperature, humidity and wind fields — confirming the cross-cutting role of aerosol data in atmospheric fire modelling.*

**Link:** <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022JD037454>

# 7. Summary

Potential variables identified as important for training data:

-   Surface Pressure
    -   Dataset: ERA5-Land: ECMWF/ERA5_LAND/HOURLY
-   Aerosol Optical Depth (AOD)
    -   Dataset: MODIS MAIAC: MODIS/061/MCD19A2_GRANULES
-   UV Aerosol Index
    -   Dataset: Sentinel-5P: COPERNICUS/S5P/OFFL/L3_AER_AI
-   Black Carbon Surface Mass Density
    -   Dataset: MERRA-2: NASA/GSFC/MERRA/aer/2
-   Carbon Monoxide Column
    -   Dataset:Sentinel-5P: COPERNICUS/S5P/OFFL/L3_CO

# 8. GEE Implementation Notes

(Will add after team specifies the variables to concentrate on this semester and GEE pull is done)
