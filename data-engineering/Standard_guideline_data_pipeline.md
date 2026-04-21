# FireFusion Data Engineering Pipeline — Technical Guideline and Team Standard

*Data Engineering Team*

Document contributor: Thai Ha NGUYEN

## 1. Purpose

This document defines the technical standard for the FireFusion data engineering stream. Its purpose is to make sure all team members collect, process, document, validate, and deliver data in a consistent way.

This guideline is designed to:
- standardise the data pipeline across the team
- reduce duplicated work and merge conflicts
- improve data quality, traceability, and reproducibility
- support reliable handover to the AI Modelling and Backend streams
- provide a foundation for future automation and scaling

---

## 2. Context

FireFusion aims to support bushfire forecasting and risk visualisation by combining multiple datasets such as:
- bushfire risk registers
- historical fire records
- weather and forecast data
- topography and vegetation-related data
- infrastructure and community risk data

The repository README states that the data engineering stream is responsible for extracting these datasets, transforming them into a unified structure, and aligning outputs with the project database architecture. The repository is organised around `architecture`, `data`, `notebooks`, and `pipelines` directories, and raw or processed datasets should not be pushed to GitHub.

This document expands those principles into a working team standard.

---

## 3. Scope

This guideline applies to all data engineering tasks in the FireFusion project, including:
- dataset discovery and source evaluation
- raw data ingestion
- transformation and cleaning
- schema alignment
- data dictionary preparation
- ETL script development
- validation and QA checks
- loading into local outputs or databases
- GitHub collaboration and pull requests
- downstream handover to other streams

It covers both:
- **static / historical datasets** such as fire risk lists, topography, land cover, and historical bushfire data
- **dynamic / frequently updated datasets** such as weather observations, forecast APIs, and other periodic feeds

---

## 4. Core Principles

### 4.1 Architecture is the source of truth
The `architecture/` folder is the official reference for:
- target table names
- column names
- data types
- key relationships
- schema documentation

Team members must align all processed outputs to the agreed architecture. Do not introduce new fields, rename columns, or change data types without updating the architecture documentation and notifying the team.

### 4.2 Raw data must remain unchanged
Files stored in `data/raw/` must stay exactly as downloaded or extracted from the source.

Do not:
- manually edit raw CSV or JSON files
- rename source columns directly in raw files
- delete source rows from raw storage

All cleaning and standardisation must happen in scripts or in generated files under `data/processed/`.

### 4.3 Processing must be reproducible
Any processed dataset should be reproducible from:
- the original source
- the extraction and transformation code
- the documented transformation rules

If a teammate cannot regenerate your output from the raw source and the code, the pipeline is not complete.

### 4.4 Documentation is part of the deliverable
A dataset is not complete if the code works but nobody can understand:
- where the data came from
- what each variable means
- how the fields were transformed
- what assumptions or limitations exist

Every important dataset must have supporting documentation.

### 4.5 Consistency is more important than local convenience
Quick local fixes are not acceptable if they bypass team standards. Avoid one-off manual work in Excel or undocumented edits outside the pipeline.

---

## 5. Standard Repository Structure

The repository should follow the agreed structure:

```text
/architecture
/data
  /raw
  /processed
  /data_dictionaries
/notebooks
/pipelines
```

### 5.1 `architecture/`
Contains the official database design and technical reference, including:
- ERD or schema diagrams
- table definitions
- column descriptions
- data type standards
- primary and foreign key rules

### 5.2 `data/raw/`
Contains unmodified source data such as:
- files downloaded from government portals
- API responses saved for traceability or testing
- original source extracts

Rules:
- raw files must remain unchanged
- raw data should stay local if `.gitignore` blocks it
- GitHub is for code and documentation, not large datasets

### 5.3 `data/processed/`
Contains cleaned and standardised outputs such as:
- schema-aligned files
- ready-to-load tables
- intermediate outputs when necessary and clearly named

### 5.4 `data/data_dictionaries/`
Contains one markdown file per dataset. Each file should explain:
- dataset name
- source and provider
- collection date
- owner or contributor
- variables and meanings
- types, units, and value ranges
- missing-value meaning
- transformation notes
- target schema mapping

### 5.5 `notebooks/`
Used for:
- exploratory data analysis
- early testing
- profiling and validation
- visual checks and charts

Rules:
- notebooks are for exploration, not final production ETL
- any pipeline logic that matters to the team must be moved into scripts under `pipelines/`

### 5.6 `pipelines/`
Contains the actual ETL logic.

Suggested structure:

```text
/pipelines
  /common
    config.py
    io_utils.py
    validation.py
    logging_utils.py
  /barr
    extract.py
    transform.py
    load.py
  /weather
    extract.py
    transform.py
    load.py
  /firms
    extract.py
    transform.py
    load.py
```

---

## 6. Standard Pipeline Lifecycle

Every dataset should move through the following stages.

### 6.1 Stage 1 — Dataset intake
Before implementation, the dataset owner must record the dataset in the team tracking sheet or equivalent planning board.

Minimum intake details:
- dataset name
- provider or organisation
- direct URL or API endpoint
- file format (`CSV`, `JSON`, `GeoJSON`, raster, API, etc.)
- update frequency
- spatial coverage
- temporal coverage
- expected use in FireFusion
- assigned owner
- known limitations

Questions to confirm before approval:
- Why do we need this dataset?
- Is it static, periodic, or real time?
- Is the source authoritative?
- Is the expected schema compatible with our architecture?
- Does the AI or Backend team require this data now?

### 6.2 Stage 2 — Extraction
Extraction means retrieving data from the source and storing it safely.

Standards:
- save extracted source data to `data/raw/`
- preserve original content exactly
- record collection date and source URL
- keep API keys or secrets in `.env`
- never hardcode credentials in scripts

For API-based extraction, scripts should:
- check response status
- fail clearly on request errors
- support pagination when needed
- log request parameters and extraction time
- save raw payloads for traceability where appropriate

#### File naming rule
Use descriptive file names:

```text
<source>_<dataset>_<yyyymmdd>.<ext>
```

Examples:
- `vic_barr_20260215.json`
- `vic_grassfire_cat4_20260215.json`
- `openmeteo_hourly_weather_20260405.json`
- `nasa_firms_hotspots_20260405.csv`

### 6.3 Stage 3 — Profiling
Before transformation, inspect the raw data.

Minimum profiling checks:
- row count
- column count
- column names
- data types as delivered by the source
- null counts
- duplicate counts
- unusual categories
- coordinate or time format quality
- unexpected schema changes

Profiling can be recorded in:
- notebook notes
- validation output
- the data dictionary

### 6.4 Stage 4 — Transformation
Transformation converts raw data into clean, standardised, schema-aligned output.

Typical tasks include:
- renaming fields
- converting data types
- standardising timestamps
- standardising units
- normalising category labels
- removing or flagging duplicates
- parsing or cleaning coordinates
- joining lookup values
- mapping source fields to target schema columns

Rules:
- all transformation logic must be explicit in code
- manual editing in Excel must not be part of the official pipeline
- dropped rows must be justified and documented
- imputed or replaced values must be documented
- transformation must be deterministic and repeatable

### 6.5 Stage 5 — Validation
No dataset should be loaded or handed over without validation.

Minimum validation checks:
- required columns exist
- columns match expected names
- data types are acceptable
- row counts are reasonable
- duplicates are handled or documented
- null values in critical fields are checked
- category values are standardised
- dates are valid
- coordinates fall within valid ranges if present
- schema mapping is complete

Validation output should include:
- pass/fail status
- warnings
- row counts before and after cleaning
- rejected or filtered record counts

### 6.6 Stage 6 — Loading
Load only validated outputs.

Loading targets may include:
- local processed JSON or CSV files for MVP work
- PostgreSQL tables for integration
- future storage layers such as a warehouse or data lake

Loading standards:
- match the target schema exactly
- enforce correct column order and types
- avoid duplicate inserts
- fail safely on schema mismatch
- log the load date and batch metadata where possible

### 6.7 Stage 7 — Handover
Before handover to another stream, provide:
- processed file or loaded table name
- data dictionary
- schema mapping
- sample preview or sample query
- update frequency
- known issues or limitations
- owner or contact person

---

## 7. Data Contract Standard

Each dataset should be treated as a data contract between the DE stream and downstream users.

For every pipeline, document:
- source name
- extraction method
- target table or output file
- refresh frequency
- primary key or unique row logic
- expected grain of the data
- field definitions
- null handling rules
- limitations and assumptions

This helps avoid confusion when the AI or Backend streams start consuming the data.

---

## 8. Data Dictionary Standard

Every dataset must have a markdown data dictionary using a consistent structure.

Template:

```markdown
# Dataset Name

## Source Information
- Source:
- Provider:
- URL:
- Date collected:
- Collected by:
- Refresh frequency:
- File format:

## Description
Brief description of what the dataset contains and why it is relevant.

## Variables
| Column Name | Description | Type | Unit/Range | Null Allowed | Notes |
|-------------|-------------|------|------------|--------------|-------|

## Data Quality Notes
- Known missing values:
- Known inconsistencies:
- Duplicates:
- Spatial limitations:
- Temporal limitations:

## Transformations Applied
- Column renaming:
- Type conversions:
- Filtering:
- Derived fields:
- Mapping to target schema:

## Target Mapping
- Target table:
- Target columns:
- Primary/foreign keys:
```

---

## 9. Naming Standards

### 9.1 File naming
Use lowercase and underscores only.

Good examples:
- `vic_barr_20260215.json`
- `openmeteo_hourly_weather_20260405.json`
- `processed_barr_facilities_20260215.csv`

Bad examples:
- `Final Data.csv`
- `new file (2).xlsx`
- `latest_weather_data.json`

### 9.2 Python naming
- variables and functions: `snake_case`
- constants: `UPPER_CASE`
- classes: `PascalCase`

### 9.3 Database naming
- table names: `snake_case`
- column names: `snake_case`
- avoid spaces and special characters
- primary key names should be descriptive, for example:
  - `facility_id`
  - `weather_observation_id`
  - `fire_event_id`

If the source has spaces in field names, standardise them during transformation when producing the target output.

---

## 10. Coding Standard for Pipeline Scripts

### 10.1 General rules
- keep scripts modular
- separate `extract`, `transform`, and `load` when practical
- move reusable logic into shared utilities
- do not leave important business logic only inside notebooks

### 10.2 Logging
Each production-ready script should log:
- start time
- end time
- source accessed
- number of records extracted
- number of records processed
- validation result
- output file or table written
- warnings and errors

### 10.3 Error handling
Scripts should:
- fail clearly with useful error messages
- not silently ignore bad data
- stop loading if the schema is broken
- catch predictable exceptions such as network errors or malformed responses

### 10.4 Configuration
Store configurable values outside the main logic when possible, such as:
- API URLs
- limits and pagination settings
- table names
- file paths
- validation thresholds
- credentials in `.env`

---

## 11. Quality Assurance Rules

Before submitting work for review, confirm that:
- the pipeline runs successfully
- the output is reproducible
- raw files are preserved unchanged
- processed outputs follow the agreed naming standard
- validation checks are present
- documentation is updated
- no secrets are exposed
- blocked dataset files are not committed to GitHub

A pipeline task is not complete if only the code exists without documentation and validation.

---

## 12. Definition of Done

A dataset or pipeline task is complete only when all of the following are true:
- source is identified and approved
- raw data is preserved
- extraction and transformation logic is implemented in code
- processed output is aligned with the target schema
- validation checks pass or warnings are documented
- data dictionary is complete
- assumptions and limitations are recorded
- PR is reviewed and merged
- downstream users can understand and use the output

A strong FireFusion data pipeline is not only one that runs successfully. It is one that the whole team can understand, reproduce, review, and extend.
