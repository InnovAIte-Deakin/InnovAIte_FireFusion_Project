# Bushfire Historical Extents Pipeline

## Source Information
- **Source:** Australian Digital Atlas (Geoscience Australia)
- **Provider:** Geoscience Australia / Digital Atlas of Australia
- **URL:** https://digital.atlas.gov.au/datasets/524e2962bd8b4968b8df9f9774345926/about
- **Date Collected:** April 2026
- **Collected by:** Joshua Jose
- **Refresh Frequency:** Static dataset (updated periodically by provider)
- **File Format:** Geodatabase (.gdb) — bulk download only, no API available

## Description
This dataset contains historical bushfire and prescribed burn extent boundaries across Australia, sourced from the Australian Digital Atlas. It is used in the FireFusion project to support fire-spread forecasting model training and validation. The pipeline filters the national dataset to Victorian records and exports two cleaned GeoJSON files for use by the AI Modelling stream.

## Variables

| Column Name | Description | Type | Unit/Range | Null Allowed | Notes |
|-------------|-------------|------|------------|--------------|-------|
| fire_id | ID attached to fire (e.g. incident ID, Event ID, Burn ID) | String | — | Yes | Nulls filled with "Unknown" |
| fire_name | Incident name (if available) | String | — | Yes | Many records have no name |
| ignition_date | Date and time of ignition, captured in jurisdiction local time and converted to UTC | Date | ISO datetime | No | Converted to string during transformation |
| capture_date | Date the incident boundary was captured or updated, converted to UTC | Date | ISO datetime | Yes | All values null for Victoria |
| extinguish_date | Date a fire is declared safe (contained and under control), if available | Date | ISO datetime | Yes | All values null for Victoria |
| fire_type | Binary variable describing whether a fire was a bushfire or prescribed burn | String | Bushfire, Prescribed Burn, Unknown | No | — |
| ignition_cause | Cause of fire | String | — | Yes | Nulls filled with "Unknown" |
| capt_method | Categorical variable describing the source of data used for defining the spatial extent of the fire | String | — | Yes | All values null for Victoria; dropped during transformation |
| area_ha | Burnt area in hectares, calculated so that all area calculations are done in the same map projection | Double | >= 0 | No | — |
| perim_km | Burnt perimeter in kilometres, calculated so that all area calculations are done in the same map projection | Double | >= 0 | No | — |
| state | State custodian of the data. Note: some states use cross border data | String | — | No | Filtered to VIC (Victoria) only |
| agency | Agency responsible for the incident | String | — | No | Dropped during transformation |
| SHAPE_Length | Geometric perimeter length calculated by the GIS system | Float | — | No | Dropped during transformation |
| SHAPE_Area | Geometric area calculated by the GIS system | Float | — | No | Dropped during transformation |
| geometry | Polygon boundary of the fire extent | MultiPolygon | — | No | GeoJSON format |

## Data Quality Notes
- **Missing values:** `fire_id` (18,649 nulls) and `ignition_cause` (87,440 nulls) filled with "Unknown"; `capture_date`, `extinguish_date`, and `capt_method` are entirely null for Victorian records
- **Duplicates:** None found
- **Invalid geometries:** None found
- **Spatial limitations:** Filtered to Victoria only; note that some states use cross border data
- **Temporal limitations:** Historical records only; earliest records date back to 1903

## Transformations Applied
- Filtered national dataset (345,345 records) to Victoria only (87,771 records) using `state == 'VIC (Victoria)'`
- Dropped columns: `SHAPE_Length`, `SHAPE_Area`, `capt_method`, `agency`
- Filled null values in `fire_id` and `ignition_cause` with "Unknown"
- Converted date columns (`ignition_date`, `extinguish_date`, `capture_date`) to string format
- Generated a separate Black Summer subset filtered to 2019–2020 ignition dates (16,154 records)

## Output Files
- `victoria_bushfire_historical.geojson` — All Victorian records (87,771)
- `victoria_bushfire_black_summer.geojson` — Black Summer 2019–2020 records (16,154)

## Setup
Install dependencies: