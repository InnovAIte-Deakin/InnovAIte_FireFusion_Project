# Real-Time Weather Ingestion Pipeline

## Overview

This pipeline supports Sprint 2 development for FireFusion by extending the weather data workflow from static historical CSV processing towards real-time ingestion.

The pipeline fetches current weather observations for selected Victorian locations using the Open-Meteo API, validates the response, transforms it into the FireFusion Supabase schema, and prepares it for upload into the `weather_observation` table.

## Data Source

- Source: Open-Meteo API
- Region: Victoria, Australia
- Variables:
  - temperature
  - wind speed
  - relative humidity
  - latitude
  - longitude
  - ingestion timestamp

## Pipeline Flow

```text
Open-Meteo API
→ Fetch real-time weather
→ Validate values
→ Transform to schema
→ Create Supabase-ready CSV
→ Upload to weather_observation