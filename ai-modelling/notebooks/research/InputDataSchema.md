# FireFusion — Model Schema Reference

**Project:** FireFusion | AI Modelling Stream
**Version:** 2.0.0 | Sprint 1 | Trimester 1 | Deakin SIT Capstone

---

## Overview

This document defines two schemas used in the FireFusion bushfire spread prediction pipeline:

1. **Training Schema** — GeoJSON FeatureCollection used to build and evaluate the model. Includes input features and target labels. Split into training and testing sets during model development.
2. **Inference Schema** — Standard JSON sent to the model endpoint at prediction time. Contains input features only. Target labels are absent because the model is predicting them.

**Tensor shape (fixed across both schemas):**

| Parameter | Value | Reason |
|---|---|---|
| Grid resolution | 500m × 500m | Derived from average Victorian bushfire burnt area statistics |
| Cell area | 25.0 ha | Fixed spatial unit for all predictions |
| Temporal window | 4 days | Captures lead-up fire weather conditions |
| Steps per day | 2 (06:00, 18:00) | Sub-daily resolution capturing morning and afternoon fire danger peaks |
| Total timesteps | 8 | 4 days × 2 steps — fixed tensor shape required by LSTM and Transformer architectures |
| Static features | 8 | Terrain and fuel variables that do not change across timesteps |
| Temporal features | 10 | Weather and drought variables that change at each timestep |

---

## Schema 1 — Training GeoJSON

```json
{
  "type": "FeatureCollection",
  "name": "FireFusion_Training_Data",
  "crs": {
    "type": "name",
    "properties": {
      "name": "urn:ogc:def:crs:EPSG::4326"
    }
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [145.47, -37.53]
      },
      "properties": {
        "cell_id": "VIC_GRID_0892",
        "cell_area_ha": 25.0,
        "grid_resolution_m": 500,

        "static_terrain": {
          "elevation_m": 540.0,
          "slope_deg": 12.0,
          "aspect_deg": 315.0,
          "dist_to_water_m": 1200.0
        },

        "biological_fuel": {
          "veg_type_encoded": 3,
          "ndvi_at_ignition": 0.31,
          "ndwi_at_ignition": -0.12,
          "nbr_at_ignition": 0.18
        },

        "historical_fire": {
          "years_since_last_fire": 21.0,
          "fire_frequency": 2,
          "last_fire_area_ha": 4375.0,
          "last_fire_severity": 4
        },

        "weather_sequence": {
          "window_days": 4,
          "steps_per_day": 2,
          "total_timesteps": 8,
          "timesteps": [
            {
              "day": -3, "hour": 6,
              "max_temp_c": 35.8,
              "wind_speed_kmh": 32.0,
              "wind_dir_deg": 292.0,
              "rel_humidity_pct": 22.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 6.1,
              "soil_moisture": 0.11,
              "soil_temp_c": 29.5,
              "days_since_rain": 10,
              "years_since_last_fire": 21.0
            },
            {
              "day": -3, "hour": 18,
              "max_temp_c": 37.0,
              "wind_speed_kmh": 35.0,
              "wind_dir_deg": 295.0,
              "rel_humidity_pct": 18.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 6.5,
              "soil_moisture": 0.10,
              "soil_temp_c": 32.4,
              "days_since_rain": 10,
              "years_since_last_fire": 21.0
            },
            {
              "day": -2, "hour": 6,
              "max_temp_c": 36.5,
              "wind_speed_kmh": 35.0,
              "wind_dir_deg": 298.0,
              "rel_humidity_pct": 18.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 6.5,
              "soil_moisture": 0.10,
              "soil_temp_c": 30.5,
              "days_since_rain": 11,
              "years_since_last_fire": 21.0
            },
            {
              "day": -2, "hour": 18,
              "max_temp_c": 37.8,
              "wind_speed_kmh": 40.0,
              "wind_dir_deg": 302.0,
              "rel_humidity_pct": 15.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 6.9,
              "soil_moisture": 0.09,
              "soil_temp_c": 33.8,
              "days_since_rain": 11,
              "years_since_last_fire": 21.0
            },
            {
              "day": -1, "hour": 6,
              "max_temp_c": 37.2,
              "wind_speed_kmh": 38.0,
              "wind_dir_deg": 305.0,
              "rel_humidity_pct": 15.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 6.9,
              "soil_moisture": 0.09,
              "soil_temp_c": 32.0,
              "days_since_rain": 12,
              "years_since_last_fire": 21.0
            },
            {
              "day": -1, "hour": 18,
              "max_temp_c": 38.2,
              "wind_speed_kmh": 45.0,
              "wind_dir_deg": 308.0,
              "rel_humidity_pct": 13.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 7.3,
              "soil_moisture": 0.08,
              "soil_temp_c": 35.5,
              "days_since_rain": 12,
              "years_since_last_fire": 21.0
            },
            {
              "day": 0, "hour": 6,
              "max_temp_c": 36.4,
              "wind_speed_kmh": 44.0,
              "wind_dir_deg": 310.0,
              "rel_humidity_pct": 14.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 7.1,
              "soil_moisture": 0.09,
              "soil_temp_c": 35.0,
              "days_since_rain": 13,
              "years_since_last_fire": 21.0
            },
            {
              "day": 0, "hour": 18,
              "max_temp_c": 39.8,
              "wind_speed_kmh": 52.0,
              "wind_dir_deg": 315.0,
              "rel_humidity_pct": 9.0,
              "precipitation_mm": 0.0,
              "evapotranspiration": 7.8,
              "soil_moisture": 0.08,
              "soil_temp_c": 38.4,
              "days_since_rain": 13,
              "years_since_last_fire": 21.0
            }
          ]
        },

        "target_labels": {
          "severity_class": 5,
          "area_ha_burned": 4375.0,
          "rate_of_spread_ha_per_day": 546.9
        }

      }
    }
  ]
}
```

---

## Training Schema — Variable Definition Table

### Static Features

| Variable | Block | Type | Unit | Range | Source | Description |
|---|---|---|---|---|---|---|
| `cell_id` | root | string | — | — | Derived — 500m grid | Unique identifier for each 500m × 500m grid cell across Victoria |
| `cell_area_ha` | root | float | ha | 25.0 (fixed) | Derived from grid resolution | Area of each grid cell in hectares. Fixed at 25 ha for 500m resolution. Narrows the spatial unit for model predictions. |
| `grid_resolution_m` | root | int | metres | 500 | Defined by team | Spatial resolution of the prediction grid. Derived from average Victorian bushfire burnt area statistics. |
| `elevation_m` | static_terrain | float | metres | 0 – 1986 | Vicmap DEM WFS | Height above sea level. Higher elevation affects temperature, humidity and fuel type — alpine areas behave differently to lowlands. |
| `slope_deg` | static_terrain | float | degrees | 0 – 90 | Derived from DEM | Terrain slope angle. A fire on a 30-degree slope travels up to 4× faster than on flat ground. Strongest terrain predictor of spread rate. |
| `aspect_deg` | static_terrain | float | degrees | 0 – 360 (N=0) | Derived from DEM | Direction the slope faces. North-facing slopes in Australia receive more solar radiation, making fuels drier and more flammable. |
| `dist_to_water_m` | static_terrain | float | metres | 0 – 50,000 | hy_watercourse WFS | Distance to nearest river or water body. Watercourses act as natural firebreaks and moderate local humidity. |
| `veg_type_encoded` | biological_fuel | int | — | 1–6 | vmlite_forest_su5 WFS | Integer-encoded vegetation class (1=Grassland, 2=Shrubland, 3=Wet Sclerophyll, 4=Dry Sclerophyll, 5=Rainforest, 6=Other). Dense forest burns hotter and faster than grassland. |
| `ndvi_at_ignition` | biological_fuel | float | unitless | −1 to 1 | GEE MODIS / Sentinel-2 | Normalised Difference Vegetation Index at ignition time. Lower values indicate stressed, sparse vegetation — more flammable fine fuel. |
| `ndwi_at_ignition` | biological_fuel | float | unitless | −1 to 1 | GEE Sentinel-2 | Normalised Difference Water Index. Measures canopy water content. Lower values indicate drier, more ignitable vegetation. |
| `nbr_at_ignition` | biological_fuel | float | unitless | −1 to 1 | GEE Sentinel-2 | Normalised Burn Ratio. Captures pre-fire fuel moisture and canopy health using shortwave infrared. Used as a fuel stress indicator. |

### Historical Fire Features

| Variable | Block | Type | Unit | Range | Source | Description |
|---|---|---|---|---|---|---|
| `years_since_last_fire` | historical_fire | float | years | 0 – 100+ | fire_history_lastburnt WFS | Number of years since the most recent fire in this cell. Longer gap = more accumulated fuel load. Areas unburned for 10+ years carry very heavy fuels. |
| `fire_frequency` | historical_fire | int | count | 0 – 20+ | fire_history_frequency WFS | Number of fire events recorded in this cell. High frequency indicates fire-adapted vegetation with faster regrowth and lower accumulated fuel. |
| `last_fire_area_ha` | historical_fire | float | ha | 0 – 200,000 | fire_history WFS | Total area burned in the most recent fire event in this cell. Larger past fires leave larger fuel gaps that take longer to recover. |
| `last_fire_severity` | historical_fire | int | 1–5 | 1 – 5 | fire_history WFS | Severity class of the most recent fire event. High past severity indicates the cell previously supported heavy fuel loads. |

### Temporal Features (per timestep)

| Variable | Block | Type | Unit | Range | Source | Description |
|---|---|---|---|---|---|---|
| `day` | weather_sequence | int | — | −3 to 0 | — | Day offset relative to ignition. Day 0 = ignition day. Day −3 = three days prior. Captures the lead-up drying sequence. |
| `hour` | weather_sequence | int | — | 6 or 18 | — | Hour of the timestep. 06:00 captures morning conditions; 18:00 captures peak afternoon fire danger. |
| `max_temp_c` | weather_sequence | float | °C | 10 – 50 | Open-Meteo archive | Maximum air temperature. Temperatures above 35°C exponentially increase fire risk by drying fine fuels and raising FFDI. |
| `wind_speed_kmh` | weather_sequence | float | km/h | 0 – 150 | Open-Meteo archive | Maximum wind speed. Primary driver of fire spread rate. Doubling wind speed can quadruple rate of spread. |
| `wind_dir_deg` | weather_sequence | float | degrees | 0 – 360 | Open-Meteo archive | Prevailing wind direction. Determines which neighbouring cells fire will spread into. North-westerly winds (270–315°) are most dangerous in Victoria. |
| `rel_humidity_pct` | weather_sequence | float | % | 0 – 100 | Open-Meteo archive | Relative humidity. Below 20% causes rapid moisture loss in fine fuels. The 2019 Black Summer saw humidity drop to single digits in Gippsland. |
| `precipitation_mm` | weather_sequence | float | mm | 0 – 200 | Open-Meteo archive | Total rainfall for the timestep. Rain suppresses fire risk directly and contributes to the days_since_rain counter. |
| `evapotranspiration` | weather_sequence | float | mm | 0 – 20 | Open-Meteo archive | Water lost from soil and vegetation to atmosphere. High values indicate strong atmospheric drying demand — accelerates fuel stress. |
| `soil_moisture` | weather_sequence | float | m³/m³ | 0.0 – 0.8 | Open-Meteo archive | Volumetric water content of the top soil layer. Values below 0.1 m³/m³ indicate critically dry fine fuel on the ground surface. |
| `soil_temp_c` | weather_sequence | float | °C | 0 – 60 | Open-Meteo archive | Soil surface temperature. Elevated values accelerate surface fuel drying and indicate sustained heat stress in the landscape. |
| `days_since_rain` | weather_sequence | int | days | 0 – 365 | Derived from precipitation | Consecutive days without meaningful rainfall. Strong predictor of fine fuel dryness. 10+ consecutive dry days indicates extreme fire risk conditions. |
| `years_since_last_fire` | weather_sequence | float | years | 0 – 100+ | fire_history WFS | Included in temporal block as a slowly-changing contextual feature. Provides the model with fuel accumulation context at each step. |

### Target Labels

| Variable | Block | Type | Unit | Range | Description |
|---|---|---|---|---|---|
| `severity_class` | target_labels | int | 1–5 | 1 – 5 | Categorical fire severity outcome. 1=Low, 2=Moderate, 3=High, 4=Very High, 5=Catastrophic. The primary classification target. |
| `area_ha_burned` | target_labels | float | ha | 0 – 200,000 | Total area burned by the fire event in this cell. Regression target used alongside severity class. |
| `rate_of_spread_ha_per_day` | target_labels | float | ha/day | 0 – 5,000 | Average daily spread rate. Captures how fast the fire expanded. Used to estimate time-to-impact for evacuation planning. |

---

## Schema 2 — Model Inference Input JSON

```json
{
  "schema_version": "2.0.0",
  "request_id": "FFX-20190129-0892",
  "created_at": "2019-01-29T06:00:00Z",
  "grid_resolution_m": 500,
  "cell_area_ha": 25.0,
  "forecast_horizon_h": 24,
  "tensor_shape": {
    "window_days": 4,
    "steps_per_day": 2,
    "total_timesteps": 8,
    "static_features": 8,
    "temporal_features": 10
  },

  "cells": [
    {
      "cell_id": "VIC_GRID_0892",

      "static_features": {
        "feature_order": [
          "elevation_m",
          "slope_deg",
          "aspect_deg",
          "dist_to_water_m",
          "veg_type_encoded",
          "ndvi_at_ignition",
          "ndwi_at_ignition",
          "nbr_at_ignition"
        ],
        "values": [540.0, 12.0, 315.0, 1200.0, 3, 0.31, -0.12, 0.18]
      },

      "temporal_features": {
        "feature_order": [
          "max_temp_c",
          "wind_speed_kmh",
          "wind_dir_deg",
          "rel_humidity_pct",
          "precipitation_mm",
          "evapotranspiration",
          "soil_moisture",
          "soil_temp_c",
          "days_since_rain",
          "years_since_last_fire"
        ],
        "timesteps": [
          { "day": -3, "hour": 6,  "values": [35.8, 32.0, 292.0, 22.0, 0.0, 6.1, 0.11, 29.5, 10, 21.0] },
          { "day": -3, "hour": 18, "values": [37.0, 35.0, 295.0, 18.0, 0.0, 6.5, 0.10, 32.4, 10, 21.0] },
          { "day": -2, "hour": 6,  "values": [36.5, 35.0, 298.0, 18.0, 0.0, 6.5, 0.10, 30.5, 11, 21.0] },
          { "day": -2, "hour": 18, "values": [37.8, 40.0, 302.0, 15.0, 0.0, 6.9, 0.09, 33.8, 11, 21.0] },
          { "day": -1, "hour": 6,  "values": [37.2, 38.0, 305.0, 15.0, 0.0, 6.9, 0.09, 32.0, 12, 21.0] },
          { "day": -1, "hour": 18, "values": [38.2, 45.0, 308.0, 13.0, 0.0, 7.3, 0.08, 35.5, 12, 21.0] },
          { "day": 0,  "hour": 6,  "values": [36.4, 44.0, 310.0, 14.0, 0.0, 7.1, 0.09, 35.0, 13, 21.0] },
          { "day": 0,  "hour": 18, "values": [39.8, 52.0, 315.0, 9.0,  0.0, 7.8, 0.08, 38.4, 13, 21.0] }
        ]
      }
    }
  ]
}
```

---

## Inference Schema — Variable Definition Table

### Static Features

| Variable | Type | Unit | Range | Source | Description |
|---|---|---|---|---|---|
| `elevation_m` | float | metres | 0 – 1986 | Vicmap DEM WFS | Height above sea level. Affects temperature, humidity and fuel type at the cell location. |
| `slope_deg` | float | degrees | 0 – 90 | Derived from DEM | Terrain slope angle. Steeper slope = faster uphill fire spread. Strongest terrain predictor of spread rate. |
| `aspect_deg` | float | degrees | 0 – 360 | Derived from DEM | Direction the slope faces. North-facing slopes are drier and more fire-prone in Australia. |
| `dist_to_water_m` | float | metres | 0 – 50,000 | hy_watercourse WFS | Distance to nearest watercourse. Proximity to water moderates humidity and acts as a natural firebreak. |
| `veg_type_encoded` | int | — | 1 – 6 | vmlite_forest_su5 WFS | Integer-encoded vegetation class. Dense forest (3,4) burns hotter and faster than grassland (1) or shrubland (2). |
| `ndvi_at_ignition` | float | unitless | −1 to 1 | GEE MODIS / Sentinel-2 | Vegetation greenness and density at ignition time. Lower values = sparser, drier, more flammable fuel. |
| `ndwi_at_ignition` | float | unitless | −1 to 1 | GEE Sentinel-2 | Canopy water content at ignition time. Lower values = drier vegetation = higher ignition risk. |
| `nbr_at_ignition` | float | unitless | −1 to 1 | GEE Sentinel-2 | Pre-fire fuel moisture and canopy health using shortwave infrared. Captures vegetation stress before ignition. |

### Temporal Features (per timestep — 8 total: 4 days × 2 steps)

| Variable | Type | Unit | Range | Source | Description |
|---|---|---|---|---|---|
| `max_temp_c` | float | °C | 10 – 50 | Open-Meteo archive | Maximum air temperature. Above 35°C dramatically increases fire risk. Primary FFDI driver. |
| `wind_speed_kmh` | float | km/h | 0 – 150 | Open-Meteo archive | Maximum wind speed. Primary driver of fire spread rate and the single most impactful weather variable in the model. |
| `wind_dir_deg` | float | degrees | 0 – 360 | Open-Meteo archive | Wind direction. Determines which neighbouring grid cells fire will spread into next. |
| `rel_humidity_pct` | float | % | 0 – 100 | Open-Meteo archive | Relative humidity. Below 20% causes rapid fine fuel drying. Single-digit values seen during Black Summer 2019. |
| `precipitation_mm` | float | mm | 0 – 200 | Open-Meteo archive | Total rainfall per timestep. Rain suppresses fire directly and resets the days_since_rain counter. |
| `evapotranspiration` | float | mm | 0 – 20 | Open-Meteo archive | Atmospheric moisture demand. High values indicate strong drying pressure on soil and vegetation even without direct sun. |
| `soil_moisture` | float | m³/m³ | 0.0 – 0.8 | Open-Meteo archive | Volumetric top-layer soil water content. Below 0.1 m³/m³ indicates critically dry fine fuel conditions at ground level. |
| `soil_temp_c` | float | °C | 0 – 60 | Open-Meteo archive | Soil surface temperature. Elevated values accelerate surface fuel drying and signal sustained heat stress. |
| `days_since_rain` | int | days | 0 – 365 | Derived — precipitation | Consecutive days without meaningful rain. 10+ days indicates extreme fine fuel dryness. Strong cumulative drought indicator. |
| `years_since_last_fire` | float | years | 0 – 100+ | fire_history WFS | Fuel accumulation context. Included in the temporal block so the model sees this alongside weather at each step. |

### Metadata Fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version for API compatibility tracking |
| `request_id` | string | Unique request identifier for logging and debugging |
| `created_at` | ISO 8601 | Timestamp of the inference request |
| `grid_resolution_m` | int | Spatial resolution of the prediction grid in metres |
| `cell_area_ha` | float | Area of each grid cell in hectares |
| `forecast_horizon_h` | int | How far ahead the model predicts — 24, 48 or 72 hours |
| `tensor_shape` | object | Defines the fixed dimensions of the input tensor for model validation |

---

## Schema Comparison

| Property | Training GeoJSON | Inference JSON |
|---|---|---|
| Format | GeoJSON FeatureCollection | Standard JSON |
| Has geometry | Yes — Point coordinates | No |
| Has target labels | Yes — severity_class, area_ha_burned, rate_of_spread | No — these are predicted outputs |
| Has suburb / name | No — removed (not processable by tensor) | No |
| Temporal window | 4 days × 2 steps = 8 timesteps | 4 days × 2 steps = 8 timesteps |
| Static features | 8 named fields in objects | 8 values in ordered array |
| Temporal features | 10 named fields per timestep | 10 values per timestep in ordered array |
| Purpose | Model training and evaluation | Live prediction request |
| Data leakage risk | None — labels are the learning signal | None — labels absent by design |

---

*FireFusion — InnovAIte | Deakin University SIT Capstone 2026*