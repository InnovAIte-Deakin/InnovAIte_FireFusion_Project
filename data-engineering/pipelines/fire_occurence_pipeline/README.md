# FireFusion: Fire Occurrence Data Engineering Pipeline

## Overview

This module implements the fire occurrence ingestion pipeline for the FireFusion bushfire forecasting project.

The pipeline is responsible for:

- ingesting cleaned fire occurrence datasets
- processing 2024–2025 fire event records
- mapping fire coordinates to the FireFusion spatial grid system
- retrieving nearest `location_id` values using KDTree spatial mapping
- uploading processed fire occurrence data into the `fire_occurrence` table
- supporting scalable and repeatable ingestion workflows

The pipeline integrates directly with the FireFusion spatial architecture through the `location_registry` and `fire_occurrence` tables.

---

# Repository Structure

```text
data-engineering/
├── data/
│   ├── docs/
│   └── fire_data_2024_2025_cleaned.csv
│
├── pipelines/
│   └── fire_occurrence_pipeline/
│       ├── fire_pipeline.py
│       ├── requirements.txt
│       └── README.md
│
└── .env
```

---

# System Architecture

The pipeline follows the FireFusion ETL architecture:

```text
Fire Occurrence CSV Dataset
        ↓
Extraction Layer (pandas)
        ↓
Transformation Layer
(validation, cleaning, deduplication)
        ↓
Spatial Mapping Layer
(latitude/longitude → nearest location_id)
        ↓
Load Layer (Supabase/PostgreSQL)
        ↓
fire_occurrence table
```

---

# Environment Setup

## 1. Install Required Libraries

From `data-engineering/`:

```bash
pip install -r pipelines/fire_occurrence_pipeline/requirements.txt
```

---

## 2. Configure Environment Variables

Create a `.env` file inside:

```text
data-engineering/
```

Add the following variables:

```env
DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

The pipeline uses:

- PostgreSQL connection for database integration
- Supabase PostgreSQL backend for data uploads

---

# Data Source

The pipeline currently processes:

- NASA FIRMS fire occurrence datasets
- cleaned bushfire event records
- confidence-filtered fire detections

CSV files are stored locally and are not committed to GitHub.

---

# Required CSV Structure

Place the CSV file at:

```text
data-engineering/data/fire_data_2024_2025_cleaned.csv
```

Required columns:

| Column | Description |
|---|---|
| latitude | Geographic latitude |
| longitude | Geographic longitude |
| acq_date | Fire acquisition date |
| confidence | Fire confidence level |
| brightness | Fire brightness value |
| frp | Fire radiative power |
| fire_occurred | Binary fire occurrence indicator |

---

# Data Processing Pipeline

## 1. Extraction

The pipeline reads raw CSV data using pandas.

Processing includes:

- column validation
- null filtering
- datetime conversion
- duplicate removal

---

## 2. Spatial Mapping

The pipeline integrates with the FireFusion spatial registry system:

```text
(latitude, longitude)
        ↓
KDTree Spatial Mapping
        ↓
nearest location_id
```

The spatial mapping layer performs:

- nearest-neighbor spatial lookup
- mapping fire coordinates to existing grid cells
- retrieval of normalized `location_id` values
- integration with `location_registry`

---

## 3. Transformation

The pipeline transforms CSV rows into the FireFusion schema:

| CSV Field | Database Field |
|---|---|
| acq_date | event_time |
| confidence | confidence |
| brightness | fire_brightness |
| frp | fire_radiative_power |
| fire_occurred | fire_occurred |
| spatial mapping output | location_id |

---

## 4. Deduplication

Duplicate fire occurrence records are removed before upload.

This prevents:

- duplicate ingestion
- repeated fire records
- unnecessary database growth

---

## 5. Load (Supabase/PostgreSQL Integration)

Processed records are uploaded into:

```text
fire_occurrence
```

using chunked uploads for scalability.

This enables:

- scalable ingestion
- memory-efficient uploads
- normalized relational storage
- architecture-compliant ETL processing

---

# Database Integration

## location_registry

Stores FireFusion spatial grid locations.

Important columns:

| Column | Description |
|---|---|
| location_id | Unique grid location identifier |
| grid_latitude | Spatial grid latitude |
| grid_longitude | Spatial grid longitude |

---

## fire_occurrence

Stores processed fire occurrence data.

Important columns:

| Column | Description |
|---|---|
| event_id | Primary key |
| location_id | Foreign key to spatial grid |
| event_time | Fire event timestamp |
| confidence | Fire confidence level |
| fire_brightness | Fire brightness |
| fire_radiative_power | Fire radiative power |
| fire_occurred | Binary fire occurrence indicator |

---

# Running the Pipeline

From `data-engineering/`:

```bash
python pipelines/fire_occurrence_pipeline/fire_pipeline.py
```

---

# Upload Behaviour

The pipeline:

- validates required CSV columns
- cleans and transforms fire occurrence data
- converts timestamps into datetime format
- maps fire coordinates to nearest FireFusion spatial locations
- retrieves valid `location_id` values
- removes duplicate records
- uploads records in chunks
- maintains normalized database architecture

---

# Data Governance

- `.env` files are excluded through `.gitignore`
- raw CSV datasets are not committed to GitHub
- credentials are stored locally only
- uploads use secure PostgreSQL connections

---

# Technical Highlights

This implementation demonstrates:

- ETL pipeline development
- geospatial data processing
- KDTree nearest-neighbor spatial mapping
- PostgreSQL + Supabase integration
- scalable batch ingestion
- normalized database architecture
- geospatial data standardisation

---

# Future Enhancements

Potential future improvements include:

- real-time fire ingestion workflows
- automated satellite data refresh
- spatial indexing optimisation
- regional fire severity aggregation
- integration with predictive fire risk models

---

# Contribution Summary

This module contributes to FireFusion by:

- standardising fire occurrence ingestion
- integrating fire datasets into the FireFusion spatial architecture
- replacing raw coordinate storage with normalized spatial references
- enabling scalable geospatial processing
- supporting downstream AI and bushfire modelling workflows