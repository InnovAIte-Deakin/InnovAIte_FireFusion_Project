# VicEmergency Real-Time Bushfire Incidents Pipeline

Contributor: **Thai Ha NGUYEN** (DE Lead)

Planner Task: [Link to MS Planner](https://planner.cloud.microsoft/webui/v1/plan/H6UJiW7Qd0-pqy0lPXGgZ8gADBxI/view/board/task/Lt_U_d_iiEKugOZeMH8v5cgACeq6?tid=d02378ec-1688-46d5-8540-1c28b5f470f6)

## Pipeline Name

VicEmergency Real-Time Bushfire Incidents Pipeline

## Pipeline Script

```text
get_realtime_incidents_CFA.py
```

## Purpose

This pipeline extracts real-time incident data from the VicEmergency public GeoJSON feed and prepares a filtered CSV containing bushfire, fire, and planned burn incidents.

The output can support the FireFusion project by providing current fire-related incident information for risk visualisation, dashboard updates, and future integration with the common FireFusion location and time structure.

This pipeline is designed for dynamic / frequently updated data because the VicEmergency feed changes over time.

---

## Source Information

* Source: VicEmergency public events GeoJSON feed
* Provider: VicEmergency
* API URL: `https://emergency.vic.gov.au/public/events-geojson.json`
* Collection method: HTTP GET request using Python `requests`
* Data format from source: GeoJSON
* Output format: CSV
* Refresh frequency: Real-time / frequently updated
* Pipeline owner: Data Engineering stream

---

## Input Data

The script does not require a local input file.

It fetches data directly from the VicEmergency public API endpoint:

```text
https://emergency.vic.gov.au/public/events-geojson.json
```

The API response is expected to contain a GeoJSON structure with a `features` list.

Each feature contains:

* `properties`
* `geometry`

The pipeline reads both sections to create the final incident records.

---

## Output File

```text
vic_emergency_bushfire_incidents.csv
```

The sample output file contains:

* Number of rows: 5
* Number of columns: 16

Because this is a real-time feed, the number of rows will change depending on when the pipeline is executed.

---

## Pipeline Flow

```text
Fetch VicEmergency GeoJSON API
        ↓
Read feature properties and geometry
        ↓
Extract latitude and longitude
        ↓
Create incident records
        ↓
Convert records to Pandas DataFrame
        ↓
Filter feed_type = incident
        ↓
Filter fire-related categories
        ↓
Sort by created date
        ↓
Save output CSV
```

---

# 1. Extraction Stage

## API Request

The script sends a GET request to the VicEmergency public API.

The request includes:

```python
headers={"User-Agent": "Mozilla/5.0"}
timeout=20
```

The script uses:

```python
response.raise_for_status()
```

This means the pipeline will fail clearly if the API request returns an HTTP error.

## Extracted Source Structure

The script loops through:

```text
data["features"]
```

For each feature, it extracts:

```text
feature["properties"]
feature["geometry"]
```

The `properties` section provides incident metadata, while the `geometry` section provides the incident coordinate.

---

# 2. Coordinate Extraction

## Function

```text
extract_point(geometry)
```

## Purpose

The `extract_point()` function extracts latitude and longitude from the GeoJSON geometry.

The script supports two geometry types:

1. `Point`
2. `GeometryCollection`

## Logic

If the geometry type is `Point`, the script extracts:

```text
longitude, latitude
```

from the coordinate list.

If the geometry type is `GeometryCollection`, the script searches inside the collection and uses the first geometry with type `Point`.

If no valid point is found, the script returns:

```text
None, None
```

## Notes

GeoJSON coordinates are usually stored as:

```text
longitude, latitude
```

The pipeline correctly converts this into:

```text
latitude, longitude
```

for the output CSV.

---

# 3. Transformation Stage

## Record Creation

For each feature, the script creates a structured record with selected fields from the VicEmergency API.

The output record includes:

| Output Column  | Source Field             | Description                            |
| -------------- | ------------------------ | -------------------------------------- |
| `id`           | `properties.id`          | Unique incident ID from the source     |
| `feed_type`    | `properties.feedType`    | Feed type, such as `incident`          |
| `category1`    | `properties.category1`   | Main incident category                 |
| `category2`    | `properties.category2`   | Secondary incident category            |
| `status`       | `properties.status`      | Current incident status                |
| `name`         | `properties.name`        | Incident name if available             |
| `action`       | `properties.action`      | Recommended action if available        |
| `location`     | `properties.location`    | Incident location description          |
| `created`      | `properties.created`     | Created timestamp                      |
| `updated`      | `properties.updated`     | Updated timestamp                      |
| `size`         | `properties.sizeFmt`     | Incident size in source display format |
| `source_org`   | `properties.sourceOrg`   | Source organisation                    |
| `source_title` | `properties.sourceTitle` | Source incident title                  |
| `latitude`     | `geometry.coordinates`   | Extracted latitude                     |
| `longitude`    | `geometry.coordinates`   | Extracted longitude                    |
| `text`         | `properties.text`        | Additional incident text if available  |

---

# 4. Filtering Stage

## Feed Type Filter

The script first filters the dataset to keep only records where:

```text
feed_type = incident
```

This removes non-incident records from the broader VicEmergency feed.

## Category Filter

The script then keeps records where either `category1` or `category2` is one of:

```text
Fire
Planned Burn
Bushfire
```

The filtering logic is:

```text
category1 in ["Fire", "Planned Burn", "Bushfire"]
OR
category2 in ["Fire", "Planned Burn", "Bushfire"]
```

This means the output can include active fire incidents, bushfires, and planned burns.

---

# 5. Sorting Stage

The filtered records are sorted by:

```text
created
```

in descending order.

This places the most recently created incidents at the top of the CSV output.

---

# 6. Loading / Output Stage

The final filtered DataFrame is saved as:

```text
vic_emergency_bushfire_incidents.csv
```

The CSV is saved with:

```text
index = False
encoding = utf-8
```

This makes the file easier to use in downstream scripts, dashboards, and database loading steps.

---

# Sample Output Structure

The uploaded sample CSV contains the following columns:

| Column Name    | Example Value                | Notes                               |
| -------------- | ---------------------------- | ----------------------------------- |
| `id`           | `ESTA:260504752`             | Source incident ID                  |
| `feed_type`    | `incident`                   | All sample records are incidents    |
| `category1`    | `Fire`                       | Main category                       |
| `category2`    | `Bushfire`                   | Secondary category                  |
| `status`       | `Under Control`              | Current incident status             |
| `name`         | Empty / incident name        | Often missing in sample             |
| `action`       | Empty                        | Missing in sample                   |
| `location`     | `Baileys Rocks Rd, Dergholm` | Human-readable location             |
| `created`      | `2026-05-03T01:56:00.000Z`   | Source timestamp                    |
| `updated`      | `2026-05-03T04:59:00.000Z`   | Source timestamp                    |
| `size`         | `Small` / `0.5 Ha.`          | Source display format               |
| `source_org`   | `VIC/CFA`                    | Source agency                       |
| `source_title` | `Baileys Rocks Rd`           | Incident title                      |
| `latitude`     | `-37.2943809190038`          | Extracted from geometry             |
| `longitude`    | `141.2075324352281`          | Extracted from geometry             |
| `text`         | Empty                        | Additional source text if available |

---

# Data Quality Notes

* The VicEmergency feed is real-time, so row counts will change each time the script runs.
* Some fields may be missing, especially:

  * `name`
  * `action`
  * `text`
* The sample CSV contains incident records from multiple source organisations, such as:

  * `VIC/CFA`
  * `VIC/DEECA`
  * `NSW/RFS`
* Some incidents may be near or outside the Victorian border, depending on the source feed coverage.
* The `size` field is stored as formatted text, for example:

  * `Small`
  * `0.5 Ha.`
  * `2724.29 Ha.`
* The `created` and `updated` fields may use different timestamp formats depending on the source record.
* Latitude and longitude are required for map visualisation and future matching to `location_registry`.
* Records without valid geometry will have missing latitude and longitude.

---

# Validation Rules

Before using or loading the output, validate that:

* The API request succeeds.
* The response contains a `features` list.
* Required columns exist in the output:

  * `id`
  * `feed_type`
  * `category1`
  * `category2`
  * `status`
  * `location`
  * `created`
  * `updated`
  * `latitude`
  * `longitude`
* All output records have `feed_type = incident`.
* All output records have `category1` or `category2` matching:

  * `Fire`
  * `Planned Burn`
  * `Bushfire`
* `latitude` and `longitude` values are numeric where present.
* Coordinates fall within the expected Australian or Victorian range.
* Duplicate `id` values are checked.
* `created` and `updated` values can be parsed as timestamps.
* Missing coordinates are counted and documented.
* Row count is logged after extraction and filtering.

---

# Recommended Target Mapping

## Target Table

Recommended target table:

```text
realtime_fire_incident
```

or staging table:

```text
stg_vic_emergency_fire_incident
```

## Target Mapping Table

| CSV Column     | Target Column          | Data Type        | Notes                      |
| -------------- | ---------------------- | ---------------- | -------------------------- |
| `id`           | `source_incident_id`   | VARCHAR          | Source incident ID         |
| `feed_type`    | `feed_type`            | VARCHAR          | Expected value: `incident` |
| `category1`    | `category_primary`     | VARCHAR          | Main category              |
| `category2`    | `category_secondary`   | VARCHAR          | Secondary category         |
| `status`       | `incident_status`      | VARCHAR          | Example: `Under Control`   |
| `name`         | `incident_name`        | VARCHAR          | Nullable                   |
| `action`       | `recommended_action`   | TEXT             | Nullable                   |
| `location`     | `location_description` | TEXT             | Human-readable location    |
| `created`      | `created_at_source`    | TIMESTAMP        | Source created time        |
| `updated`      | `updated_at_source`    | TIMESTAMP        | Source updated time        |
| `size`         | `incident_size_text`   | VARCHAR          | Raw formatted size         |
| `source_org`   | `source_org`           | VARCHAR          | Example: `VIC/CFA`         |
| `source_title` | `source_title`         | VARCHAR          | Source incident title      |
| `latitude`     | `incident_latitude`    | DOUBLE PRECISION | Extracted latitude         |
| `longitude`    | `incident_longitude`   | DOUBLE PRECISION | Extracted longitude        |
| `text`         | `incident_text`        | TEXT             | Nullable                   |
| Derived        | `location_id`          | INTEGER          | Future nearest-grid match  |
| Derived        | `ingested_at`          | TIMESTAMP        | Pipeline run timestamp     |

---

# Suggested PostgreSQL Schema

```sql
CREATE TABLE realtime_fire_incident (
    realtime_fire_incident_id SERIAL PRIMARY KEY,
    source_incident_id VARCHAR(100) NOT NULL,
    feed_type VARCHAR(50),
    category_primary VARCHAR(100),
    category_secondary VARCHAR(100),
    incident_status VARCHAR(100),
    incident_name VARCHAR(255),
    recommended_action TEXT,
    location_description TEXT,
    created_at_source TIMESTAMP,
    updated_at_source TIMESTAMP,
    incident_size_text VARCHAR(100),
    source_org VARCHAR(100),
    source_title VARCHAR(255),
    incident_latitude DOUBLE PRECISION,
    incident_longitude DOUBLE PRECISION,
    incident_text TEXT,
    location_id INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_realtime_fire_incident_source_id UNIQUE (source_incident_id),
    CONSTRAINT fk_realtime_fire_incident_location
        FOREIGN KEY (location_id)
        REFERENCES location_registry(location_id)
);
```

---

# Primary Key / Unique Row Logic

Recommended unique source key:

```text
source_incident_id
```

However, because real-time incident records may be updated, the pipeline should also compare:

```text
source_incident_id + updated_at_source
```

This can help decide whether to update an existing row or store a new incident snapshot.

---

# FireFusion Usage

This pipeline can support:

* real-time bushfire incident monitoring
* dashboard visualisation
* fire incident map layers
* joining active incidents with suburb or grid locations
* future matching to `location_registry`
* AI model features related to active fire presence
* backend API endpoints for current incident data

---

# Recommended Improvements

## Add scheduled execution

Because the dataset is real-time, this script can be scheduled to run periodically.

Possible schedule:

```text
Every 15 minutes or every 1 hour
```

The best schedule depends on backend and dashboard requirements.

---

# Known Issues and Limitations

* The feed is dynamic, so results will vary between runs.
* The pipeline currently does not save the raw GeoJSON response.
* The output CSV only represents the feed state at the time of execution.
* The script does not currently load data into PostgreSQL.
* The script does not currently match incident coordinates to `location_registry`.
* The script does not currently create a validation report.
* Timestamp formats may vary between records.
* Some incidents may have missing optional fields.
* Some source organisations may report incidents outside Victoria but still appear in the feed.

