NASA FIRMS Fire Data Engineering Pipeline
1. Overview

This module implements a robust data engineering pipeline for ingesting, transforming, and integrating bushfire detection data from NASA FIRMS into the FireFusion system.

The pipeline supports both batch (historical) and near real-time ingestion, enabling continuous updates of fire events for downstream analytics and predictive modelling.

All processed data is aligned with the Fire_Events fact table in the FireFusion Star Schema, ensuring seamless integration with weather, topography, vegetation, and infrastructure datasets.

2. System Architecture

The pipeline follows a standard ETL (Extract → Transform → Load) architecture:

NASA FIRMS API / CSV
        ↓
Extraction Layer (requests / pandas)
        ↓
Transformation Layer (data cleaning, schema alignment)
        ↓
Staging Layer (temporary PostgreSQL table)
        ↓
Load Layer (Fire_Events fact table)
        ↓
Indexed Database (PostgreSQL)

3. Project Structure
data-engineering/
├── pipelines/
│   └── nasa_firms/
│       ├── transform_firms.py
│       ├── load_to_postgres.py
│       ├── realtime_ingest_firms.py
│       ├── db_connection.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   └── fire_analysis.ipynb

4. Data Source

The pipeline uses NASA FIRMS (Fire Information for Resource Management System):

Satellite-based fire detection (MODIS, VIIRS)
Global coverage with high temporal resolution
Supports both historical archives and near real-time feeds

Real-time ingestion uses the FIRMS Area API with bounding-box filtering.

5. Data Processing Pipeline
5.1 Extraction

Two ingestion modes are implemented:

Batch Processing
Reads raw CSV files downloaded from FIRMS
Used for historical analysis (Black Summer 2019–2020)
Real-time Ingestion
Uses FIRMS API via HTTP requests
Fetches recent fire detections (last 1–5 days)
Supports region-based filtering (Victoria / Australia)
5.2 Transformation

Data is standardised into the Fire_Events schema:

Type conversion and validation
Handling mixed-type columns (e.g., confidence values)
Mapping categorical confidence levels to numeric scale
Filtering invalid or null records
Deduplication based on spatial-temporal attributes

Key transformations:

acq_date → event_date
confidence → confidence_score
Missing foreign keys set to NULL (future integration)
5.3 Load (PostgreSQL Integration)

Data is inserted into PostgreSQL using a staging + merge strategy:

Load transformed data into a temporary staging table
Insert into Fire_Events using INSERT ... SELECT
Apply ON CONFLICT DO NOTHING for deduplication
Drop staging table after successful load

This ensures:

idempotent ingestion
safe reprocessing
consistent dataset state

6. Database Design
Fire_Events Table
Column	Type	Description
event_id	INTEGER	Primary key
weather_id	INTEGER	Foreign key
topo_id	INTEGER	Foreign key
fuel_id	INTEGER	Foreign key
facility_id	INTEGER	Foreign key
latitude	DOUBLE	Geographic coordinate
longitude	DOUBLE	Geographic coordinate
event_date	DATE	Detection date
confidence_score	INTEGER	Fire detection confidence
source_system	VARCHAR	Data origin

6.1 Indexing Strategy

To optimise query performance:

Spatial filtering:
CREATE INDEX idx_fire_events_latitude ON Fire_Events(latitude);
CREATE INDEX idx_fire_events_longitude ON Fire_Events(longitude);
Temporal filtering:
CREATE INDEX idx_fire_events_event_date ON Fire_Events(event_date);
Combined index for analytics:
CREATE INDEX idx_fire_events_location_date 
ON Fire_Events(latitude, longitude, event_date);

6.2 Deduplication Strategy

A composite uniqueness constraint is applied:

(latitude, longitude, event_date, confidence_score, source_system)

This ensures:

no duplicate fire events
safe ingestion of overlapping API data
consistent incremental updates

7. Real-time Ingestion Design

The real-time ingestion pipeline is designed for continuous operation:

Fetches recent fire detections periodically
Uses bounding-box filtering to reduce data volume
Supports region-specific processing (Victoria for optimisation)
Key Features
API-based ingestion (no manual downloads)
Automatic deduplication
Incremental data loading
Compatible with scheduled execution (cron)
8. Configuration
Environment Variables
FIRMS_MAP_KEY=your_api_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=firefusion_db
DB_USER=postgres
DB_PASSWORD=your_password
9. Execution
Batch Processing
python3 transform_firms.py
python3 load_to_postgres.py
Real-time Ingestion
python3 realtime_ingest_firms.py
10. Automation

Real-time ingestion can be scheduled using cron:

*/10 * * * * python3 realtime_ingest_firms.py

This enables near real-time updates every 10 minutes.

11. Data Governance
Raw and processed datasets are stored locally
No large datasets are committed to GitHub
Sensitive configurations (.env) are excluded
Repository follows strict structure for collaboration

12. Future Enhancements
Spatial indexing using PostGIS
Integration with weather and topography tables
Streaming ingestion (Kafka / real-time pipeline)
Fire risk scoring models
Interactive dashboards for monitoring

13. Technical Highlights

This implementation demonstrates:

End-to-end ETL pipeline design
API-based real-time ingestion
Database optimisation and indexing
Data quality and deduplication strategies
Scalable architecture for multi-source integration

14. Contribution Summary

This module contributes to the FireFusion project by:

providing structured fire event data
enabling real-time monitoring capability
supporting predictive modelling workflows
improving system-wide data consistency and performance