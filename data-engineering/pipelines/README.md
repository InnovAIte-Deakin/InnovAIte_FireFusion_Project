# 🔥 FireFusion Data Engineering Pipeline

## 📌 Overview

This module implements the data engineering pipeline for the FireFusion project, an AI-driven bushfire forecasting system.  

The goal of this pipeline is to transform raw environmental and fire event data into a structured, relational format aligned with the project’s star schema architecture, enabling integration, analysis, and future predictive modelling.

---

## 🧠 Architecture Alignment

The pipeline strictly follows the defined FireFusion data architecture:

### 🟡 Fact Table
- **Fire_Events**
  - Represents actual fire occurrences
  - Acts as the target variable for prediction models

### 🔵 Dimension Table
- **Weather_Conditions**
  - Stores environmental predictors such as temperature, wind speed, and humidity

The pipeline ensures that all processed data matches the schema structure required for relational joins and downstream modelling.

---

## ⚙️ Pipeline Components

### 1️⃣ Victoria Historical Weather Pipeline

📁 `pipelines/victoria_weather/`

This pipeline processes historical weather data (Victoria region, 2019–2022) using the Open-Meteo API.

#### Steps:
- Fetch weather data from Open-Meteo
- Clean and standardise data
- Validate data quality and schema alignment
- Store data into PostgreSQL (`Weather_Conditions`)
- Generate visualisations for analysis

#### Output Schema:
- latitude  
- longitude  
- record_date  
- temperature_c  
- wind_speed_kmh  
- relative_humidity  

---

### 2️⃣ Fire Events Pipeline

📁 `pipelines/fire_events/`

This pipeline processes NASA FIRMS fire event data.

#### Steps:
- Load and filter fire event data
- Clean and validate records
- Store into PostgreSQL (`Fire_Events`)
- Prepare data for integration with weather conditions

#### Output Schema:
- latitude  
- longitude  
- event_date  
- confidence_score  
- source_system  

---

### 3️⃣ Data Integration (Key Contribution)

A critical component of this phase is linking fire events with weather conditions.

#### Approach:
- Match fire events with weather records based on:
  - temporal proximity (same date/hour)
  - spatial proximity (latitude & longitude)
- Assign corresponding `weather_id` to each fire event

#### Impact:
This transforms independent datasets into a **relational dataset**, enabling:
- multi-variable analysis  
- feature engineering  
- predictive modelling readiness  

---

### 4️⃣ PostgreSQL Storage

All processed datasets are stored in a local PostgreSQL database (`firefusion`).

#### Tables Used:
- `Weather_Conditions`
- `Fire_Events`

#### Purpose:
- Structured data storage
- Efficient querying
- Backend/API readiness

---

### 5️⃣ Data Visualisation

Visualisation scripts are included to analyse trends in:
- temperature
- wind speed
- humidity

#### Purpose:
- validate pipeline outputs  
- identify patterns relevant to bushfire behaviour  
- support exploratory data analysis  

---

## 🔄 End-to-End Pipeline Flow




---

## 🚀 Key Contributions

- Developed a complete end-to-end weather data pipeline  
- Integrated fire event data into a structured system  
- Implemented data validation and schema alignment  
- Designed PostgreSQL-based storage for scalability  
- Established relationships between datasets using foreign keys  
- Generated visual insights to validate and analyse data  

---

## 📈 Impact

This phase significantly improves the FireFusion system by:

- moving from raw, isolated datasets to structured relational data  
- enabling integration across multiple data sources  
- preparing data for backend services and APIs  
- supporting future AI/ML-based fire prediction models  

---

## 🔮 Future Improvements

- Integration with shared/cloud database (e.g., Supabase)  
- Expansion to additional dimensions (fuel, topography, infrastructure)  
- Real-time data ingestion pipelines  
- Backend API connectivity  
- Feature engineering for predictive modelling  

---

## 🧑‍💻 Technologies Used

- Python (pandas, requests, SQLAlchemy)  
- PostgreSQL  
- Open-Meteo API  
- NASA FIRMS dataset  
- Matplotlib (for visualisation)  

---

## 📌 Conclusion

This pipeline establishes a strong data engineering foundation for FireFusion by ensuring that all data is clean, structured, and aligned with the system architecture.  

It bridges the gap between raw environmental data and actionable insights, enabling the project to move toward scalable integration and intelligent fire prediction.
