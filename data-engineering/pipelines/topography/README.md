# FireFusion: Topography Data Engineering Pipeline

## Overview

This module implements the topography ingestion pipeline for the FireFusion bushfire forecasting project.

The pipeline is responsible for:

- ingesting topography elevation and slope datasets
- mapping coordinates to the FireFusion spatial grid system
- generating or retrieving `location_id` values using GridSnapper
- uploading processed topography data into the `topography_profile` table
- supporting scalable and repeatable ingestion workflows

The pipeline integrates directly with the FireFusion spatial architecture through the `location_registry` and `topography_profile` tables.

---

# Repository Structure

```text
data-engineering/
├── data/
│   ├── docs/
│   └── topography_data.csv
│
├── grid_snapper/
│   └── grid_snapper.py
│
├── pipelines/
│   └── topography/
│       ├── upload_topography_profile.py
│       ├── requirements.txt
│       └── README.md
│
└── .env

# System Architecture
The pipeline follows the FireFusion ETL architecture:
Topography CSV Dataset
        ↓
Extraction Layer (pandas)
        ↓
Transformation Layer
(validation, cleaning, deduplication)
        ↓
GridSnapper Layer
(latitude/longitude → location_id)
        ↓
Load Layer (Supabase/PostgreSQL)
        ↓
topography_profile table

# Environment Setup
1. Install Required Libraries

From data-engineering/:
pip install -r pipelines/topography/requirements.txt

2. Configure Environment Variables

Create a .env file inside:

data-engineering/

Add the following variables:

DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_database_user
DB_PASSWORD=your_database_password

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

The pipeline uses:

PostgreSQL connection for GridSnapper
Supabase API client for batch uploads

# Data Source

The pipeline currently processes:

DEM-derived elevation datasets
slope angle measurements
coordinate-based topography observations

CSV files are stored locally and are not committed to GitHub.

Required CSV Structure

Place the CSV file at:

data-engineering/data/topography_data.csv

Required columns:

Column	Description
latitude	Geographic latitude
longitude	Geographic longitude
elevation_meters	Elevation above sea level
slope_angle	Terrain slope angle
Data Processing Pipeline
1. Extraction

The pipeline reads raw CSV data using pandas.

Processing includes:

column validation
null filtering
duplicate coordinate removal
2. Grid Snapping

The pipeline integrates with FireFusion GridSnapper:

(latitude, longitude)
        ↓
GridSnapper
        ↓
location_id

GridSnapper performs:

spatial snapping to FireFusion grid cells
validation against supported Victoria region bounds
lookup/creation of entries in location_registry
3. Transformation

The pipeline transforms CSV rows into the FireFusion schema:

CSV Field	Database Field
latitude	original_latitude
longitude	original_longitude
GridSnapper output	location_id
elevation_meters	elevation_meters
slope_angle	slope_angle
4. Deduplication

Multiple coordinates may snap to the same spatial grid location.

To prevent database conflicts:

records are deduplicated using location_id
only one record per snapped grid cell is uploaded

This prevents duplicate updates during batch upserts.

5. Load (Supabase/PostgreSQL Integration)

Processed records are uploaded into:

topography_profile

using batch upserts:

ON CONFLICT(location_id)

This enables:

idempotent ingestion
safe reprocessing
scalable uploads
duplicate prevention
Database Integration
location_registry

Stores snapped FireFusion spatial grid locations.

Important columns:

Column	Description
location_id	Unique grid location identifier
grid_latitude	Snapped latitude
grid_longitude	Snapped longitude
topography_profile

Stores processed topography data.

Important columns:

Column	Description
topo_id	Primary key
location_id	Foreign key to spatial grid
original_latitude	Raw source latitude
original_longitude	Raw source longitude
elevation_meters	Elevation value
slope_angle	Terrain slope
Running the Pipeline

From data-engineering/:

python pipelines/topography/upload_topography_profile.py
Upload Behaviour

The pipeline:

validates required CSV columns
maps coordinates to FireFusion spatial grid cells
generates/retrieves location_id
deduplicates snapped locations
uploads records in batches
performs conflict-safe upserts
Data Governance
.env files are excluded through .gitignore
raw CSV datasets are not committed to GitHub
credentials are stored locally only
uploads use secure service-role authentication
Technical Highlights

This implementation demonstrates:

ETL pipeline development
spatial grid integration
PostgreSQL + Supabase integration
scalable batch ingestion
deduplication handling
geospatial data standardisation
Future Enhancements

Potential future improvements include:

automated DEM dataset refresh workflows
higher-resolution grid support
spatial indexing optimisation
terrain feature enrichment
integration with predictive fire risk models
Contribution Summary

This module contributes to FireFusion by:

standardising topography ingestion
integrating terrain datasets into the FireFusion spatial architecture
enabling scalable geospatial processing
supporting downstream AI and bushfire modelling workflows
