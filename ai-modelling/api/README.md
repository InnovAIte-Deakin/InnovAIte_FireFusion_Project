# FireFusion - AI Modeling – FastAPI Model Interface (Template)

## Overview

This repository contains the **initial FastAPI interface for the LSTM model for predicting bushfire**. The purpose of this API is to provide a structured endpoint that accepts **GeoJSON FeatureCollection input**, processes the data into a format suitable for a machine learning model, and returns predictions in **GeoJSON format**.

At this stage, the API is designed as a **template and development scaffold** for the future model integration. It demonstrates how the system will:

* Accept **spatial wildfire prediction inputs**
* Convert the input data into **machine learning features**
* Run **model inference**
* Return results as **GeoJSON for mapping and visualization**

The current implementation uses **placeholder logic** because the actual model has not yet been trained.

---

## Project Context

This API is part of the **FireFusion bushfire prediction system**, which aims to predict wildfire severity and spread using environmental, terrain, and weather data.

The model will eventually incorporate:

* **Static terrain features** (elevation, slope, aspect)
* **Biological fuel data** (vegetation type and satellite indices)
* **Ignition risk indicators**
* **Historical fire information**
* **7-day weather sequence data**

The machine learning model planned for this system is an **LSTM-based spatiotemporal model**, which will learn patterns from sequential weather data combined with static environmental features.

---

## API Architecture

```
GeoJSON Input
      │
      ▼
FastAPI Endpoint
      │
      ▼
Feature Extraction
(static + weather sequence)
      │
      ▼
Tensor Conversion
      │
      ▼
LSTM Model Inference (Future)
      │
      ▼
GeoJSON Prediction Output
```

---

## Current Implementation

The API currently performs the following steps:

1. Receives a **GeoJSON FeatureCollection** request.
2. Validates the request using **Pydantic schemas**.
3. Extracts:

   * Static terrain features
   * Vegetation and ignition risk features
   * 7-day weather sequence
4. Converts these values into tensors compatible with an **LSTM architecture**.
5. Runs a **placeholder prediction function**.
6. Returns the prediction results in **GeoJSON format**.

---

## Expected Input Schema

The API expects a **GeoJSON FeatureCollection** similar to the following structure:

```
FeatureCollection
 └── Feature
      ├── geometry (Point)
      └── properties
            ├── cell_id
            ├── suburb
            ├── static_terrain
            ├── biological_fuel
            ├── ignition_risk
            ├── historical_fire_data
            ├── weather_sequence_7d
            └── target_labels
```

The **weather_sequence_7d** field represents the temporal input used by the LSTM model.

---

## Example Request

POST request:

```
POST /predict
```

Body (simplified):

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [145.47, -37.53]
      },
      "properties": {
        "cell_id": "VIC_GRID_0892",
        "suburb": "Toolangi",
        "static_terrain": {
          "elevation_m": 540,
          "slope_deg": 12,
          "aspect_deg": 315,
          "dist_to_water_m": 1200
        },
        "weather_sequence_7d": [...]
      }
    }
  ]
}
```

---

## Example Response

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [145.47, -37.53]
      },
      "properties": {
        "cell_id": "VIC_GRID_0892",
        "prediction": {
          "predicted_severity": 4.2,
          "predicted_area_ha": 3780.5,
          "predicted_spread_rate": 510.3
        }
      }
    }
  ]
}
```

---

## Running the API

Install dependencies:

```
pip install fastapi uvicorn torch numpy
```

Start the server:

```
uvicorn main:app --reload
```

API documentation will be available at:

```
http://127.0.0.1:8000/docs
```

---

## Important Note ⚠️

This implementation is **only a template for the future AI model interface**.

* The current code **does not contain a trained model**.
* The prediction logic is **placeholder code used for development and testing**.
* The **model architecture, feature extraction pipeline, and inference logic will be updated once the LSTM model is trained**.

Once the training phase is completed, the following updates will be required:

* Load the trained model weights
* Adjust feature preprocessing
* Replace placeholder predictions with real model inference
* Optimize batch processing for large spatial datasets

---

## Future Improvements

Planned improvements include:

* Integration of the **trained LSTM wildfire prediction model**
* Support for **batch inference on large grid datasets**
* Conversion of predictions into **spatial fire spread maps**
* Integration with **frontend map dashboards**
* Connection to **satellite and weather data pipelines**

---

## Purpose of This Template

This template allows the development team to:

* Define the **expected API contract**
* Test **data flow between components**
* Validate the **GeoJSON input/output format**
* Prepare the system for **seamless model integration later**

---

## Author

FireFusion AI Modelling Stream - Tran Minh Quan Nguyen 
