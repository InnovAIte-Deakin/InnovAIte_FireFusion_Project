# Weather Dataset Exploration for Bushfire Forecasting

## 1. Introduction
This report presents an exploration of weather datasets available in the Google Earth Engine (GEE) weather catalog for use in bushfire forecasting. These datasets serve as the primary source of input features for the forecasting model, providing key weather variables such as temperature, wind, humidity, and precipitation.

A range of datasets were reviewed and evaluated based on their temporal resolution, spatial coverage, data type, and availability of these core variables. From this exploration, several candidate datasets were identified and selected for further comparison to determine their suitability for building a basic bushfire forecasting model.

---

## 2. Bushfire Modelling Requirements
Bushfire behaviour can be understood through three main aspects: ignition, spread, and intensity. Weather conditions directly influence all three.

Among available weather variables, temperature, wind, humidity, and precipitation have the most direct impact on these factors. High temperature and low humidity dry out vegetation, increasing ignition likelihood and fire intensity. Wind strongly affects fire spread by supplying oxygen and determining the speed and direction of fire movement. Precipitation influences fuel moisture over time, where low rainfall leads to dry conditions that increase fire risk.

For these reasons, these four variables are considered core features for developing a basic but functional bushfire forecasting model.

---

## 3. Dataset Selection Criteria
To identify suitable datasets, the following criteria were used:

- Temporal resolution (e.g. hourly, 6-hourly)  
- Spatial resolution (data granularity)  
- Data type (reanalysis vs forecast)  
- Availability of core variables (temperature, wind, humidity, precipitation)  

Datasets that satisfy these criteria are more suitable for modelling fire behaviour effectively.

---

## 4. Dataset Exploration (GEE Weather Catalog)

All datasets available within the GEE weather catalog were initially reviewed to understand their characteristics, including temporal resolution, spatial resolution, and available variables. Based on the defined selection criteria, datasets were filtered to identify those that provide the core weather variables required for bushfire forecasting.

From this process, a subset of candidate datasets was selected for further analysis. In particular, ERA5, CFSR, CFSv2, and GFS were chosen as primary candidates, as they offer suitable temporal resolution and include the key variables needed for modelling.

Direct source URLs for all datasets are provided in Appendix A.

| Dataset | Frequency | Type | Spatial Coverage | Time Span | Resolution | Core Variables | Accessibility | Suitability |
|--------|----------|------|------------------|-----------|------------|----------------|--------------|------------|
| CFSR | 6-hourly | Reanalysis | Global | 2018–2026 | 55 km | Temperature, Humidity, Wind, Precipitation | GEE | Suitable |
| CFSv2 | 6-hourly | Forecast/Reanalysis | Global | 1979–2026 | 22 km | Temperature, Humidity, Wind, Precipitation | GEE | Moderate |
| ERA5 | Hourly | Reanalysis | Global | 1940–2026 | 27 km | Temperature, Humidity, Wind, Precipitation | GEE | Highly suitable |
| GFS | 1–3 hourly | Forecast | Global | 2015–2026 | 28 km | Temperature, Humidity, Wind, Precipitation | GEE | Better for prediction |

---

## 5. Selected Variables and Band Names

To ensure consistency between the data pipeline and model input, the exact technical band names of the selected variables are specified below for each dataset.

### 5.1 CFSR

| Feature | Band Name | Unit |
|--------|----------|------|
| Temperature | Temperature_surface | K |
| Humidity | Specific_humidity_height_above_ground | Mass fraction |
| Precipitation | Precipitation_rate_surface_3_Hour_Average | kg/m²/s |
| Wind (U) | u_component_of_wind_10m_above_ground | m/s |
| Wind (V) | v_component_of_wind_10m_above_ground | m/s |

---

### 5.2 CFSv2

| Feature | Band Name | Unit |
|--------|----------|------|
| Temperature | Temperature_height_above_ground | K |
| Humidity | Specific_humidity_height_above_ground | Mass fraction |
| Precipitation | Precipitation_rate_surface_6_Hour_Average | kg/m²/s |
| Wind (U) | u-component_of_wind_height_above_ground | m/s |
| Wind (V) | v-component_of_wind_height_above_ground | m/s |

---

### 5.3 ERA5

| Feature | Band Name | Unit |
|--------|----------|------|
| Temperature | temperature_2m | K |
| Humidity | relative_humidity_850hPa | % |
| Precipitation | mean_total_precipitation_rate | kg/m²/s |
| Wind (U) | u_component_of_wind_10m | m/s |
| Wind (V) | v_component_of_wind_10m | m/s |

---

### 5.4 GFS

| Feature | Band Name | Unit |
|--------|----------|------|
| Temperature | temperature_2m_above_ground | °C |
| Humidity | relative_humidity_2m_above_ground | % |
| Precipitation | total_precipitation_surface | kg/m² |
| Wind (U) | u_component_of_wind_planetary_boundary_layer | m/s |
| Wind (V) | v_component_of_wind_planetary_boundary_layer | m/s |

---

## 6. Discussion

All selected datasets provide the required core variables for bushfire forecasting. However, they differ in temporal resolution, spatial resolution, and data type, which affects their suitability.

ERA5 provides hourly data, allowing it to capture short-term changes in weather conditions more effectively than 6-hourly datasets such as CFSR and CFSv2. This is particularly important for bushfire spread modelling, where rapid changes in wind, temperature, and humidity can significantly influence fire behaviour. Additionally, ERA5 offers consistent reanalysis data with no missing values, which is important for constructing a reliable training dataset.

Although ERA5 and CFSR have similar spatial resolution, ERA5 is generally preferred due to its higher temporal resolution and improved consistency as a reanalysis dataset. The availability of core variables — temperature, wind, humidity, and precipitation — further supports its use as a primary data source.

CFSv2 provides similar variables but includes forecast components, which may introduce additional uncertainty when used for model training. GFS offers high-frequency data but is primarily designed for forecasting future conditions, making it more suitable for prediction rather than training.

Overall, ERA5 provides the best balance of temporal resolution, data consistency, and completeness within the GEE weather catalog.

---

## 7. Conclusion

This study explored weather datasets available in the Google Earth Engine (GEE) weather catalog for use in bushfire forecasting. Among the evaluated datasets, ERA5 was identified as the most suitable primary data source.

The selected variables — temperature, wind, humidity, and precipitation — are directly relevant to bushfire behaviour. The use of exact technical band names ensures consistency between the data pipeline and model input.

Other datasets such as CFSR, CFSv2, and GFS may be considered as complementary sources in future work.

Overall, this work establishes a clear and practical foundation for building a basic bushfire forecasting model.

---

## Appendix A – Dataset Source URLs

- ERA5: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY  
- CFSR: https://developers.google.com/earth-engine/datasets/catalog/NOAA_CFSR  
- CFSv2: https://developers.google.com/earth-engine/datasets/catalog/NOAA_CFSV2  
- GFS: https://developers.google.com/earth-engine/datasets/catalog/NOAA_GFS0P25  