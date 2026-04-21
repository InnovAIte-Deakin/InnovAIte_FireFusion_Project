# 🔧 FireFusion Data Engineering – Technical Documentation

## 📌 Overview

This document provides a technical overview of the data engineering work completed as part of Phase 2 of the FireFusion project.  

The objective of this phase was to design and implement a structured, scalable data pipeline that transforms raw environmental and fire event data into a relational format aligned with the system’s star schema architecture.

The pipeline integrates multiple external data sources, applies standard data engineering processes, and prepares the dataset for downstream analysis and predictive modelling.

---

## 🧠 System Architecture Context

The pipeline aligns with a star schema design consisting of:

### 🔹 Fact Table
- **Fire_Events**
  - Represents observed fire occurrences
  - Acts as the primary dataset for prediction

### 🔹 Dimension Table
- **Weather_Conditions**
  - Stores environmental attributes influencing fire behaviour

The architecture enables structured joins between datasets and supports feature extraction for machine learning workflows.

---

## ⚙️ Data Sources

### 1. Open-Meteo Historical Weather API
- Provides hourly environmental data
- Variables used:
  - temperature
  - wind speed
  - relative humidity
- Data range:
  - 2019–2022
- Region:
  - Victoria, Australia

### 2. NASA FIRMS (Fire Information for Resource Management System)
- Provides satellite-detected fire event data
- Key attributes:
  - latitude, longitude
  - acquisition date
  - confidence score

---

## 🔄 Pipeline Design

The pipeline follows a standard layered data engineering approach:

### 1. Data Ingestion
- Weather data fetched using API calls
- Fire event data loaded from CSV (FIRMS dataset)

### 2. Raw Data Layer
- Data stored in CSV format
- Serves as the base input for further processing

### 3. Data Cleaning and Transformation
- Removal of null and duplicate records
- Standardisation of column names and formats
- Conversion of timestamps and data types

### 4. Data Filtering
- Spatial filtering using Victoria bounding box
- Temporal filtering for relevant date ranges (2019–2022)

### 5. Data Validation
- Validation of data completeness
- Range checks (e.g., humidity, coordinates)
- Schema consistency checks

### 6. Schema Alignment
- Mapping cleaned data to predefined schema
- Ensuring compatibility with:
  - `Weather_Conditions`
  - `Fire_Events`

---

## 🗄️ Database Design and Storage

A PostgreSQL database (`firefusion`) is used for structured storage.

### Tables Implemented:

#### Weather_Conditions
Stores environmental variables:
- latitude
- longitude
- record_date
- temperature_c
- wind_speed_kmh
- relative_humidity

#### Fire_Events
Stores fire occurrence data:
- latitude
- longitude
- event_date
- confidence_score
- source_system

Foreign key fields are included to support future integration:
- weather_id
- topo_id
- fuel_id
- facility_id

---

## 🔗 Data Integration Strategy

A key technical contribution of this phase is the integration of fire events with weather data.

### Approach:
- Match fire events with weather records based on:
  - temporal proximity (same date)
  - spatial proximity (nearest coordinates)

### Implementation:
- A Python-based matching process assigns `weather_id` to each fire event
- This establishes a relational link between:
  - Fire_Events (fact)
  - Weather_Conditions (dimension)

### Outcome:
- Enables joined queries
- Supports feature engineering
- Prepares dataset for predictive modelling

---

## 📊 Data Analysis and Visualisation

Basic visualisation has been implemented to:
- verify pipeline outputs
- observe environmental trends
- support exploratory data analysis

Visualisations include:
- temperature trends
- wind speed variation
- humidity patterns

---

## 🚀 System Impact

This phase improves the FireFusion system by:

- transitioning from raw data ingestion to structured data engineering
- enabling integration between multiple data sources
- aligning data pipelines with system architecture
- providing a scalable foundation for backend and AI integration

---

## 🔮 Future Enhancements

Planned improvements include:

- integration with cloud database solutions (e.g., Supabase)
- expansion to additional dimensions (fuel, topography, infrastructure)
- real-time data ingestion pipelines
- backend API integration
- advanced feature engineering for machine learning models

---

## 🧑‍💻 Technologies Used

- Python (pandas, SQLAlchemy)
- PostgreSQL
- Open-Meteo API
- NASA FIRMS dataset
- Matplotlib (for visualisation)

---

## 📌 Conclusion

The implemented data pipeline establishes a robust and scalable foundation for FireFusion.  

By aligning data ingestion, processing, and storage with the system architecture, this work enables seamless integration across project streams and prepares the system for future predictive analytics and real-world deployment.