# FireFusion Schema Validation Script

Validates that Supabase tables have the required columns with correct data types before data gets uploaded.

## What it does

- Checks for all 7 core columns (incident_id, location_id, time_id, original_latitude, original_longitude, acq_date, acq_time)
- Verifies column types match expected types
- Checks for dataset-specific columns defined in config
- Reports missing columns, type mismatches, and unexpected extra columns
- Does NOT modify data, only validates schema

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
```
Edit `.env` and add your Supabase URL and API key.

3. **Configure for your dataset:**
Edit `config.yaml` and set the `table_name` to your target table. Add any dataset-specific columns with their types.

## Usage

Run validation for fire_incident_record:
```bash
python validate_schema.py
```

Or specify a different config file:
```bash
python validate_schema.py config/weather_observation.yaml
```

## Output

**If schema is valid:**
```
Validating schema for table: fire_incident_record
✓ Schema validation passed for 'fire_incident_record'
```

**If schema has issues:**
```
Validating schema for table: fire_incident_record
✗ Schema validation FAILED for 'fire_incident_record':
  - MISSING: Core column 'brightness_ti4' not found
  - TYPE MISMATCH: Column 'confidence' is text, expected varchar
```

## Config file structure

```yaml
table_name: fire_incident_record

columns:
  column_name:
    type: float8
  another_column:
    type: text
```

Supported types: int2, int4, int8, float4, float8, text, varchar, date, timestamp, timestamptz

## Adding new datasets

1. Create a new config file: `config/new_dataset.yaml`
2. Set `table_name` and add dataset-specific columns
3. Run: `python validate_schema.py config/new_dataset.yaml`

The core 7 columns are always checked automatically.

## Exit codes

- `0` = validation passed
- `1` = validation failed or error occurred
