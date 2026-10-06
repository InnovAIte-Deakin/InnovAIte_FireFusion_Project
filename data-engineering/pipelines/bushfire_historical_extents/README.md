# Bushfire Historical Extents Pipeline

## Source Information
- **Provider:** Australian Digital Atlas (Geoscience Australia)
- **URL:** https://digital.atlas.gov.au/datasets/524e2962bd8b4968b8df9f9774345926/about
- **Date Collected:** April 2026
- **Collected by:** Joshua Jose
- **Refresh Frequency:** Static dataset (updated periodically by provider)
- **File Format:** Geodatabase (.gdb) — bulk download only, no API available

## Description
This pipeline extracts and transforms historical bushfire extent data for Victoria from the Australian Digital Atlas. It filters the national dataset to Victorian records, matches each fire incident to the Location_Registry and Time_Registry, and produces two cleaned CSV files aligned to the `Fire_Incident_Record` schema for use in the FireFusion fire-spread forecasting model.

## Target Table
`Fire_Incident_Record`

| Column | Type | Description |
|--------|------|-------------|
| incident_id | Integer (PK) | Unique identifier for each fire incident |
| location_id | Integer (FK) | Matched from Location_Registry via centroid coordinates |
| time_id | Integer (FK) | Matched from Time_Registry via ignition date |
| original_latitude | Float | Raw centroid latitude extracted from fire polygon |
| original_longitude | Float | Raw centroid longitude extracted from fire polygon |

## Variables

| Column Name | Description | Type | Unit/Range | Null Allowed | Notes |
|-------------|-------------|------|------------|--------------|-------|
| fire_id | ID attached to fire (e.g. incident ID, Event ID, Burn ID) | String | — | Yes | Nulls filled with "Unknown" |
| fire_name | Incident name (if available) | String | — | Yes | Many records have no name |
| ignition_date | Date and time of ignition, captured in jurisdiction local time and converted to UTC | Date | ISO datetime | No | Used temporarily for time_id matching; dropped from final output |
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
| geometry | Polygon boundary of the fire extent | MultiPolygon | — | No | Used to extract centroid coordinates; dropped from final output |

## Data Quality Notes
- **Missing values:** `fire_id` (18,649 nulls) and `ignition_cause` (87,440 nulls) filled with "Unknown"; `capture_date`, `extinguish_date`, and `capt_method` are entirely null for Victorian records
- **Duplicates:** None found
- **Invalid geometries:** None found
- **Spatial limitations:** Filtered to Victoria only; note that some states use cross border data
- **Temporal limitations:** Historical records only; earliest records date back to 1903

## Pipeline Scripts
| Script | Description |
|--------|-------------|
| `extract_bushfire_historical.py` | Main ETL script — extracts, transforms, and orchestrates the full pipeline |
| `match_location_id.py` | Matches fire centroids to nearest location_id using KD-tree spatial index |
| `match_time_id.py` | Matches ignition dates to time_id using the Time_Registry |


## Setup
Install dependencies:
```
pip install -r requirements.txt
```

## Usage
1. Download the dataset from the URL above
2. Place the `.gdb` file, `location_registry.csv`, and `time_registry_rows.csv` in the same folder as the scripts
3. Run:
```
python extract_bushfire_historical.py
```

## Output Files
- `victoria_fire_incident_record.csv` — All Victorian records (87,771) aligned to Fire_Incident_Record schema
- `victoria_fire_incident_black_summer.csv` — Black Summer 2019–2020 records (16,154)

## Known Limitations
- Dataset must be manually downloaded as a bulk file — no API is available
- File size is approximately 847MB
- Historical records before 1990 may be less complete or less accurate
- Records with ignition dates before 2018 will have a null `time_id` as the Time_Registry only covers from 2018 onwards
