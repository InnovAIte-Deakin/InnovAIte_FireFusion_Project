# Comprehensive Guide to the FireFusion Data Architecture

This documentation explains our Spatial-Temporal Hub and Spoke architecture. We moved away from a traditional Star Schema to ensure our AI model can query any location at any time, even if a fire is not currently active.

## 1. The "Hub and Spoke" Strategy

Our system is built like a wheel. The "Hubs" are the center, and all other data tables are the "Spokes" that connect to them.

* **The Hubs (Location & Time)**: These tables act as the universal anchors for the entire project.

* **The Spokes (Observations)**: These tables contain the actual data (weather, fire, soil) and must always plug into the Hubs.

* **The Benefit**: This design allows us to "stack" different types of data perfectly on top of each other for the AI to analyze.

## 2. Detailed Table Definitions

Our database is organized into three categories based on how the data behaves.

### A. The Anchors (The Hubs)

These tables define "Where" and "When" an event happened.

| Table Name | Purpose | Key Columns |
|---|---|---|
| Location_Registry | Acts as our universal map grid. Each row is a specific square in Victoria. | `location_id`, `grid_latitude`, `grid_longitude` |
| Time_Registry | Acts as our universal calendar. It tracks data by the hour and season. | `time_id`, `datetime_record`, `season` |

### B. Dynamic Observation Tables (Daily Spokes)

These tables store data that changes every day. They must connect to both Location and Time.

* **Weather_Observation**: Stores temperature, wind, and humidity readings.

* **Fire_Incident_Record**: Stores data on active fires and hotspots.

* **Vegetation_Condition**: Stores soil moisture and how dry the "fuel" (plants) is.

### C. Static Feature Tables (Historical Spokes)

These tables store data that stays the same for a long time. They only connect to the Location Hub.

* **Topography_Profile**: Stores elevation and the angle of slopes.

* **Infrastructure_Asset**: Stores the location of hospitals, schools, and fire stations.

## 3. The "Data Lining" Process

As the Lead, I have implemented two mandatory rules for every piece of data entering our system.

### Step 1: Data Alignment (The Snap)

Incoming data from NASA or APIs often has messy coordinates.

* **The Rule**: All scripts must "snap" or round raw coordinates to match a `location_id` in our registry.

* **The Goal**: This ensures that when we look at "Grid Square #101," we see the correct weather and fire data in the exact same spot.

### Step 2: Data Lineage (The Receipt)

We must never lose the original truth provided by the satellite.

* **The Rule**: Every table must store the raw, untouched coordinates in the `original_latitude` and `original_longitude` columns.

* **The Goal**: This creates a permanent record of where the data came from before we aligned it to our grid.

## 4. Operational Pipeline Workflow

We manage our data through two separate workflows to keep the system organized.

* **Historical (Bulk) Pipeline**: This is run once. It fills the database with years of past fire and weather data to train our AI model.

* **Daily (Batch) Pipeline**: This runs on a schedule. It fetches live updates from APIs to keep the fire prediction system current.

## 5. Mandatory Developer Checklist

Before submitting code to GitHub, every team member must verify these four points:

1. **Source Identity**: Did you include the API link or data source URL in your code comments?

2. **Hub Connection**: Does your script correctly map data to `location_id` and `time_id`?

3. **Lineage Protection**: Are you saving the raw, untouched coordinates in the "Original" columns?

4. **Type Matching**: Does your Python data match our database types (e.g., Integer for IDs, Float for coordinates)?