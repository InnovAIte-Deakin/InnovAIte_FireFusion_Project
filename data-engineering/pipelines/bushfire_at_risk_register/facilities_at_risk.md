# Facility Geocoding and Location Registry Matching Pipeline

Document contributor: **Thai Ha NGUYEN**

Planner Task: [Link to MS Planner](https://planner.cloud.microsoft/webui/v1/plan/H6UJiW7Qd0-pqy0lPXGgZ8gADBxI/view/board/task/eloSFgRZBEWwC1fi41KBxsgAE1Pl?tid=d02378ec-1688-46d5-8540-1c28b5f470f6)

## Pipeline Name

Facility Geocoding and Location Registry Matching Pipeline

## Pipeline Scripts

This pipeline contains two main Python scripts:

1. `get_geocode.py`
2. `match_facilities_to_location_id.py`

The pipeline should be executed in this order:

```text
get_geocode.py
        ↓
match_facilities_to_location_id.py
```

## Purpose

This pipeline prepares bushfire at-risk facility data for spatial integration with the FireFusion database architecture.

The first stage geocodes facility addresses and adds latitude and longitude values to each facility record. The second stage uses those latitude and longitude values to match each facility to the nearest grid point in the `location_registry` table.

This allows facility-level risk records to be connected to the FireFusion 1km x 1km location grid, supporting later joins with weather, fire, vegetation, and risk datasets.

---

# 1. `get_geocode.py`

## Stage Purpose

The `get_geocode.py` script takes raw bushfire at-risk facility records and attempts to find latitude and longitude coordinates for each facility.

It uses address-related fields from each facility record to build search queries, sends those queries to OpenStreetMap Nominatim, and saves the geocoding result back into the facility dataset.

## Input File

```text
bushfire_at_risk_register.json
```

This file contains the raw facility records from the Bushfire At-Risk Register dataset.

Expected source fields used by the script include:

| Field              | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `Facility address` | Main address used for geocoding                           |
| `Town/Suburb`      | Suburb used to improve address matching                   |
| `LGA`              | Local Government Area used as an additional location hint |
| `Facility name`    | Used as a fallback query when address matching is weak    |

## Output Files

```text
facilities_at_risk_register_geocoded.json
geocode_cache.json
```

| Output File                                 | Description                                         |
| ------------------------------------------- | --------------------------------------------------- |
| `facilities_at_risk_register_geocoded.json` | Main geocoded facility output                       |
| `geocode_cache.json`                        | Cache file storing previous geocoding query results |

## Main Processing Logic

### 1. Load input data

The script loads the input JSON file. If the JSON object is a single dictionary, it converts it into a list so the rest of the pipeline can process it consistently.

### 2. Continue from existing output

If the geocoded output file already exists, the script continues from that file instead of starting again from the raw input file.

This is useful because geocoding can take time and may be interrupted.

### 3. Load geocode cache

The script checks whether `geocode_cache.json` already exists.

If it exists, the script loads previous query results. If not, it starts with an empty cache.

This reduces duplicate API requests and makes the pipeline more efficient and reproducible.

### 4. Build address queries

For each facility, the script builds multiple possible search queries using:

* facility address
* suburb
* state
* facility name
* Local Government Area

Example query formats:

```text
<Facility address>, <Town/Suburb>, VIC, Australia
<Facility address>, <Town/Suburb>, Victoria, Australia
<Facility name>, <Town/Suburb>, VIC, Australia
<Facility address>, <Town/Suburb>, <LGA>, Victoria, Australia
```

The script tries these queries in order until a valid location is found.

### 5. Skip already matched records

If a facility already has:

```text
latitude
longitude
geocode_status = matched
```

the script skips that record.

This prevents unnecessary reprocessing.

### 6. Geocode using OpenStreetMap Nominatim

The script uses:

```text
OpenStreetMap Nominatim
```

with a rate limiter to avoid sending requests too quickly.

The rate limiter uses:

```text
minimum delay: 1.5 seconds
maximum retries: 3
error wait time: 10 seconds
```

The geocoding request is limited to Australia using:

```text
country_codes = "au"
```

### 7. Save matched result

If a location is found, the script adds the following fields to the facility record:

| Output Field           | Description                                |
| ---------------------- | ------------------------------------------ |
| `latitude`             | Matched latitude                           |
| `longitude`            | Matched longitude                          |
| `geocode_status`       | Set to `matched`                           |
| `geocode_source`       | Set to `OpenStreetMap Nominatim`           |
| `geocode_query`        | Query that produced the match              |
| `geocode_display_name` | Full display address returned by Nominatim |

### 8. Save unmatched result

If no location is found, the script still records the geocoding attempt.

The following fields are added:

| Output Field           | Description                      |
| ---------------------- | -------------------------------- |
| `latitude`             | `null`                           |
| `longitude`            | `null`                           |
| `geocode_status`       | Set to `not_matched`             |
| `geocode_source`       | Set to `OpenStreetMap Nominatim` |
| `geocode_query`        | First query attempted            |
| `geocode_display_name` | `null`                           |

### 9. Save progress after every row

The script saves the output JSON file after each processed facility.

This protects progress if the script stops during execution.

## Data Quality Notes

* Some facility addresses may not be matched by OpenStreetMap Nominatim.
* Some records may be matched using facility name instead of facility address.
* Geocoding results should be manually reviewed where accuracy is important.
* The field `geocode_display_name` should be used to inspect whether the matched address looks correct.
* Records with `geocode_status = not_matched` should be reviewed or retried using another geocoding provider.

## Validation Checks

Before using the geocoded output, check:

* total number of input records
* number of records with `geocode_status = matched`
* number of records with `geocode_status = not_matched`
* records with missing `latitude`
* records with missing `longitude`
* coordinates outside Victoria
* suspicious matches where `geocode_display_name` does not match the original facility suburb or LGA

## Suggested Output Location

```text
data/processed/facilities_at_risk_register_geocoded.json
```

---

# 2. `match_facilities_to_location_id.py`

## Stage Purpose

The `match_facilities_to_location_id.py` script takes geocoded facility records and matches each facility to the nearest grid point in the FireFusion `location_registry`.

The `location_registry` table contains the project’s standard grid coordinates. Matching facilities to this table allows all facility records to be linked with the common FireFusion spatial structure.

## Input Files

```text
facilities_fire_risk_google_geocoded.json
location_registry.csv
```

| Input File                                  | Description                                                                                     |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `facilities_fire_risk_google_geocoded.json` | Geocoded facility records with latitude and longitude                                           |
| `location_registry.csv`                     | FireFusion grid reference table containing `location_id`, `grid_latitude`, and `grid_longitude` |

## Important File Name Note

The first script outputs:

```text
facilities_at_risk_register_geocoded.json
```

However, the second script currently expects:

```text
facilities_fire_risk_google_geocoded.json
```

Before running the full pipeline, either:

1. rename the geocoded output file, or
2. update `FACILITY_JSON_FILE` in `match_facilities_to_location_id.py`.

Recommended update:

```python
FACILITY_JSON_FILE = "facilities_at_risk_register_geocoded.json"
```

This will make the two scripts connect directly.

## Output Files

```text
facilities_fire_risk_with_location_id.json
facilities_fire_risk_with_location_id.csv
```

| Output File                                  | Description                                 |
| -------------------------------------------- | ------------------------------------------- |
| `facilities_fire_risk_with_location_id.json` | Facility records with matched `location_id` |
| `facilities_fire_risk_with_location_id.csv`  | CSV version of the matched output           |

## Main Processing Logic

### 1. Load geocoded facilities

The script loads the geocoded facility JSON file and converts it into a Pandas DataFrame.

If the JSON file contains a single dictionary, it is converted into a list first.

### 2. Load location registry

The script loads:

```text
location_registry.csv
```

This file is expected to contain the FireFusion grid reference points.

Expected columns include:

| Column           | Description                   |
| ---------------- | ----------------------------- |
| `location_id`    | Unique ID for each grid point |
| `grid_latitude`  | Latitude of the grid point    |
| `grid_longitude` | Longitude of the grid point   |
| `region_name`    | Optional region name          |

### 3. Convert coordinate columns to numeric values

The script converts the following columns to numeric format:

```text
facilities.latitude
facilities.longitude
location_registry.grid_latitude
location_registry.grid_longitude
```

Invalid coordinate values are converted to missing values.

### 4. Remove invalid grid rows

Rows in `location_registry.csv` with missing `grid_latitude` or `grid_longitude` are removed before matching.

This prevents invalid grid points from being used in nearest-neighbour matching.

### 5. Build BallTree index

The script builds a `BallTree` using the grid coordinates from `location_registry`.

Coordinates are converted into radians because haversine distance is used.

The haversine metric is suitable for latitude and longitude distance calculation on the Earth’s surface.

### 6. Prepare output columns

The script creates the following new output columns in the facility DataFrame:

| Output Column            | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| `location_id`            | Nearest matched location ID from `location_registry`              |
| `matched_grid_latitude`  | Latitude of the matched grid point                                |
| `matched_grid_longitude` | Longitude of the matched grid point                               |
| `distance_to_grid_m`     | Distance from facility coordinate to matched grid point in metres |
| `grid_match_status`      | Matching status                                                   |

Default value:

```text
grid_match_status = no_facility_lat_lon
```

This default is used for records that do not have valid facility latitude and longitude.

### 7. Match valid facility coordinates

The script only matches records where both `latitude` and `longitude` are available.

For each valid facility, it finds the nearest grid point from `location_registry`.

The output includes:

```text
location_id
matched_grid_latitude
matched_grid_longitude
distance_to_grid_m
```

### 8. Calculate distance in metres

The script calculates haversine distance and converts the result from radians to metres using:

```text
EARTH_RADIUS_M = 6371000
```

The final distance is rounded to two decimal places.

### 9. Assign grid match status

The script uses a 1000-metre threshold.

If the nearest grid point is within 1000 metres:

```text
grid_match_status = matched
```

If the nearest grid point is more than 1000 metres away:

```text
grid_match_status = matched_far_check_needed
```

This is used because the FireFusion grid is approximately 1km x 1km, and some geocoded addresses may not be perfectly accurate.

### 10. Save output

The script saves the final matched output into both JSON and CSV formats.

## Data Quality Notes

* Facilities without latitude or longitude cannot be matched to `location_registry`.
* These records keep `grid_match_status = no_facility_lat_lon`.
* Facilities with a long distance to the nearest grid point are still matched, but they are flagged as `matched_far_check_needed`.
* A distance above 1000 metres should be reviewed.
* The quality of this step depends on the accuracy of the geocoding output from Stage 1.
* Invalid grid coordinates are removed before matching.

## Validation Checks

Before handover, validate:

* total number of facility records loaded
* total number of grid records loaded
* number of facilities with valid latitude and longitude
* number of facilities with `grid_match_status = matched`
* number of facilities with `grid_match_status = matched_far_check_needed`
* number of facilities with `grid_match_status = no_facility_lat_lon`
* maximum `distance_to_grid_m`
* average `distance_to_grid_m`
* facilities with distance greater than 1000 metres
* facilities with missing `location_id`

## Suggested Output Location

```text
data/processed/facilities_fire_risk_with_location_id.json
data/processed/facilities_fire_risk_with_location_id.csv
```

---

# End-to-End Pipeline Flow

## Step 1: Prepare Raw Input

Place the raw Bushfire At-Risk Register JSON file in the working directory or expected raw data folder.

Recommended raw path:

```text
data/raw/bushfire_at_risk_register.json
```

## Step 2: Run Geocoding

Run:

```bash
python get_geocode.py
```

Expected output:

```text
facilities_at_risk_register_geocoded.json
geocode_cache.json
```

## Step 3: Check Geocoding Results

Review the geocoding status summary.

Important fields to inspect:

```text
geocode_status
geocode_source
geocode_query
geocode_display_name
latitude
longitude
```

Records with `geocode_status = not_matched` should be reviewed before the next stage.

## Step 4: Prepare Location Registry

Make sure the following file exists:

```text
location_registry.csv
```

Required columns:

```text
location_id
grid_latitude
grid_longitude
```

## Step 5: Align File Name

Before running the second script, confirm that its input file matches the output from the geocoding step.

Recommended script setting:

```python
FACILITY_JSON_FILE = "facilities_at_risk_register_geocoded.json"
```

## Step 6: Run Location Matching

Run:

```bash
python match_facilities_to_location_id.py
```

Expected outputs:

```text
facilities_fire_risk_with_location_id.json
facilities_fire_risk_with_location_id.csv
```

## Step 7: Review Match Status

Review:

```text
grid_match_status
distance_to_grid_m
location_id
matched_grid_latitude
matched_grid_longitude
```

Records with `matched_far_check_needed` should be manually checked.

---

# Output Fields Added by the Pipeline

## Fields Added by `get_geocode.py`

| Field                  | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| `latitude`             | Facility latitude returned by geocoder                  |
| `longitude`            | Facility longitude returned by geocoder                 |
| `geocode_status`       | `matched` or `not_matched`                              |
| `geocode_source`       | Geocoding provider used                                 |
| `geocode_query`        | Query that produced the result or first attempted query |
| `geocode_display_name` | Full matched address returned by geocoder               |

## Fields Added by `match_facilities_to_location_id.py`

| Field                    | Description                                                 |
| ------------------------ | ----------------------------------------------------------- |
| `location_id`            | Nearest FireFusion grid ID                                  |
| `matched_grid_latitude`  | Latitude of matched grid point                              |
| `matched_grid_longitude` | Longitude of matched grid point                             |
| `distance_to_grid_m`     | Distance between facility coordinate and matched grid point |
| `grid_match_status`      | Match quality status                                        |

---

# Target Mapping

## Target Table

Recommended target table:

```text
facility_at_risk
```

or staging table:

```text
stg_facility_at_risk_geocoded
```

## Suggested Mapping

| Pipeline Output Field    | Target Column            | Notes                              |
| ------------------------ | ------------------------ | ---------------------------------- |
| `Facility name`          | `facility_name`          | Rename to snake_case               |
| `Facility address`       | `facility_address`       | Original address                   |
| `Town/Suburb`            | `suburb`                 | Rename to snake_case               |
| `LGA`                    | `lga`                    | Local Government Area              |
| `latitude`               | `facility_latitude`      | From geocoding stage               |
| `longitude`              | `facility_longitude`     | From geocoding stage               |
| `geocode_status`         | `geocode_status`         | Geocoding quality flag             |
| `geocode_source`         | `geocode_source`         | Source provider                    |
| `geocode_query`          | `geocode_query`          | Query used for traceability        |
| `geocode_display_name`   | `geocode_display_name`   | Returned address                   |
| `location_id`            | `location_id`            | Foreign key to `location_registry` |
| `matched_grid_latitude`  | `matched_grid_latitude`  | Grid coordinate for audit          |
| `matched_grid_longitude` | `matched_grid_longitude` | Grid coordinate for audit          |
| `distance_to_grid_m`     | `distance_to_grid_m`     | Distance to nearest grid point     |
| `grid_match_status`      | `grid_match_status`      | Match quality flag                 |

---

# Recommended Database Consideration

The final dataset should include `location_id` as a foreign key to the `location_registry` table.

Example relationship:

```text
facility_at_risk.location_id → location_registry.location_id
```

This allows facility data to be joined with other FireFusion datasets using the common location grid.

---

# Known Issues and Limitations

* OpenStreetMap Nominatim may not match all facility addresses.
* Some facility names or addresses may be ambiguous.
* The second script currently expects a different input filename from the first script’s output filename.
* `matched_far_check_needed` records require manual review.
* A matched `location_id` does not guarantee that the geocoded address is correct; it only shows the nearest grid point to the available coordinate.
* Facilities without valid latitude and longitude cannot be matched.
* This pipeline currently writes to local JSON and CSV files, not directly to PostgreSQL.

---
