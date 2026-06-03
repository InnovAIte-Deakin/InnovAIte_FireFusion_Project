# Vic Emergency Realtime Bushfire Incident Pipeline

Document contributor: Thai Ha NGUYEN

## 1. Overview

This task implements a realtime data pipeline for collecting bushfire and fire-related incident data from the Vic Emergency public feed, assigning each incident to an existing FireFusion grid location, checking for duplicates, and inserting only new records into the Supabase PostgreSQL database.

The pipeline supports the FireFusion Data Engineering stream by preparing realtime incident data for downstream visualisation, risk analysis, and integration with other streams.

---

## 2. Pipeline Objective

The objective of this pipeline is to:

1. Extract realtime incident data from Vic Emergency.
2. Filter bushfire/fire-related incidents.
3. Match each incident latitude and longitude to an existing `location_id`.
4. Prevent duplicate incident records.
5. Insert only new incident records into the Supabase table:

```sql
public.vic_emercency_bushfire_incident_realtime
````

---

## 3. Data Source

### Source Name

Vic Emergency Realtime Incident Feed

### Source URL

```text
https://emergency.vic.gov.au/public/events-geojson.json
```

### Data Format

The source returns data in GeoJSON format. Each record may contain:

* Incident ID
* Incident category
* Incident status
* Location text
* Latitude and longitude
* Updated timestamp
* Geometry information

The pipeline extracts usable incident records from the GeoJSON response and converts them into a structured format suitable for Supabase insertion.

---

## 4. Target Database Table

The processed data is inserted into:

```sql
public.vic_emercency_bushfire_incident_realtime
```

This table stores realtime bushfire/fire incident records from Vic Emergency.

The key fields include:

| Column        | Description                                    |
| ------------- | ---------------------------------------------- |
| `id`          | Unique incident identifier from Vic Emergency  |
| `location_id` | Matched grid location from `location_registry` |
| `latitude`    | Original latitude from Vic Emergency           |
| `longitude`   | Original longitude from Vic Emergency          |
| `category1`   | Main incident category                         |
| `category2`   | Sub-category, such as Fire or Bushfire         |
| `status`      | Current incident status                        |
| `location`    | Human-readable location description            |
| `updated`     | Last updated timestamp from Vic Emergency      |
| `created_at`  | Database insertion timestamp                   |

---

## 5. Pipeline Workflow

The final pipeline follows this workflow:

```text
Step 1: Fetch data from Vic Emergency
Step 2: Extract and filter bushfire/fire incidents
Step 3: Check existing incident IDs in Supabase
Step 4: Keep only new records
Step 5: Match latitude/longitude to existing location_registry rows
Step 6: Insert new records into Supabase
```

---

## 6. Step 1: Get and Extract Data from Vic Emergency

The pipeline sends a request to the Vic Emergency GeoJSON endpoint.

It then extracts incident records and filters only relevant fire-related events.

Relevant categories include:

```text
Fire
Bushfire
Planned Burn
```

The pipeline also extracts coordinates from the GeoJSON geometry field.

Only records with valid latitude and longitude are prepared for the next step.

---

## 7. Step 2: Add `location_id` Using Existing `location_registry`

The pipeline does **not** use the old `GridSnapper.get_location_id()` function because that function may create new rows in `location_registry`.

For this task, the requirement is:

> Do not add anything to `location_registry`.

Therefore, the pipeline only uses existing rows in `location_registry`.

The approved registry range is:

```sql
location_id BETWEEN 1 AND 463807
```

This ensures the pipeline only uses the original approved grid registry rows and does not use any accidentally created or polluted records.

---

## 8. Grid Snapping Logic

For each Vic Emergency incident, the pipeline takes:

```text
latitude, longitude
```

Then it searches for the nearest existing grid point in:

```sql
public.location_registry
```

Only rows within this range are considered:

```sql
WHERE location_id BETWEEN 1 AND 463807
```

The nearest grid point is selected by comparing the incident coordinate against `grid_latitude` and `grid_longitude`.

The selected row provides the final:

```text
location_id
```

This `location_id` is then inserted into the realtime incident table.

---

## 9. Important Design Decision

### Old Approach

```text
latitude/longitude
→ GridSnapper
→ snap to grid
→ create new location if not found
→ return location_id
```

### Final Approach

```text
latitude/longitude
→ search existing location_registry only
→ use nearest approved location_id
→ insert incident record
```

The final approach is safer because it protects the integrity of the shared FireFusion grid system.

No new rows are inserted into `location_registry`.

---

## 10. Step 3: Duplicate Checking

Before inserting new incident records, the pipeline checks whether the Vic Emergency incident ID already exists in:

```sql
public.vic_emercency_bushfire_incident_realtime
```

The duplicate check uses the incident `id`.

If the `id` already exists, the record is skipped.

This prevents repeated runs of the pipeline from inserting the same incident multiple times.

---

## 11. Step 4: Insert New Records

After duplicate filtering and location matching, only new records are inserted into Supabase.

The insert operation includes conflict protection using the incident ID, so even if duplicate records are found during concurrent runs, the database will not insert duplicates.

The pipeline inserts:

* Vic Emergency incident ID
* Matched `location_id`
* Original latitude
* Original longitude
* Category information
* Status
* Location description
* Updated timestamp
* Other available incident metadata

---

## 12. Environment Variables

The pipeline uses a `.env` file for database credentials.

Example:

```env
DB_HOST=your-supabase-host
DB_PORT=5432
DB_NAME=postgres
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

Optional setting:

```env
MAX_SNAP_DISTANCE_KM=20
DEBUG_LOCATION_MATCHES=false
```

Set this to `true` if debugging location matching:

```env
DEBUG_LOCATION_MATCHES=true
```

---

## 13. Required Python Packages

Install the required packages:

```bash
pip install requests psycopg2-binary python-dotenv
```

---

## 14. How to Run the Pipeline

Run the final pipeline script:

```bash
python vic_emergency_realtime_pipeline_v4_registry_only.py
```

Expected output example:

```text
Step 1: Fetching data from Vic Emergency...
Extracted bushfire/fire incident records: 73

Step 2: Validating Supabase schema...

Step 3: Checking duplicates in Supabase...
Existing records: 10
New records: 63

Step 4: Matching location_id from approved location_registry rows...

Step 5: Inserting new records into Supabase...
Inserted records: 63

Pipeline completed successfully.
```

---

## 15. Optional Database Index

To improve grid snapping performance, create an index on the approved grid fields:

```sql
CREATE INDEX IF NOT EXISTS idx_location_registry_approved_grid
ON public.location_registry (location_id, grid_latitude, grid_longitude)
WHERE location_id BETWEEN 1 AND 463807;
```

This helps the pipeline search existing grid points faster.

---

## 16. Data Quality Rules

The pipeline applies the following data quality checks:

| Check                                     | Action                         |
| ----------------------------------------- | ------------------------------ |
| Missing latitude/longitude                | Skip record                    |
| Coordinate outside usable range           | Skip or fail location match    |
| Duplicate incident ID                     | Skip record                    |
| No matching location in approved registry | Skip record                    |
| Invalid database schema                   | Stop pipeline before inserting |

---

## 17. Key Constraints

The final version follows these constraints:

* Do not insert into `location_registry`.
* Do not use polluted or newly created registry rows.
* Only use `location_id` from `1` to `463807`.
* Preserve original latitude and longitude from Vic Emergency.
* Use `location_id` only for grid-based integration.
* Insert only new records into the realtime incident table.

---

## 18. Why This Pipeline Matters

This pipeline provides a reliable realtime incident ingestion process for FireFusion.

It allows the Data Engineering stream to continuously collect current fire-related incidents and align them with the project’s shared grid system. This makes the data ready for dashboard visualisation, spatial analysis, and future integration with weather, vegetation, topography, and AI modelling outputs.

---

## 19. Future Improvements

Possible future improvements include:

1. Schedule the pipeline to run automatically every 5–15 minutes.
2. Add logging to a separate pipeline execution table.
3. Store failed records for later review.
4. Add a more accurate spatial matching method using PostGIS.
5. Add alerting if the Vic Emergency API is unavailable.
6. Add automated tests for duplicate checking and location matching.
7. Compare realtime incidents with historical bushfire datasets for validation.

---

## 20. Summary

This task created a realtime Vic Emergency bushfire incident pipeline that extracts fire-related incident data, matches each incident to the approved FireFusion grid, checks for duplicates, and inserts only new records into Supabase.

The final version is safe for the shared database because it only reads from `location_registry` and does not create or modify grid registry rows.