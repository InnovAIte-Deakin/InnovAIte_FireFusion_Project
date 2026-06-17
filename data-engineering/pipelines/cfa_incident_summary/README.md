# CFA Incident Summary — Historical Pipeline

Historical **Workflow A** pipeline for the FireFusion hub-and-spoke architecture. Ingests CFA incident records into `CFA_District_Registry` and `Fire_Incident_Record`, linked to `Location_Registry` and `Time_Registry`.

## Overview

| Step | Script | Output |
|------|--------|--------|
| Profile | `scripts/profile_cfa_incidents.py` | `logs/cfa_incident_profile.json` |
| Preprocess | `scripts/preprocess_cfa_incidents.py` | `data/processed/cfa_incidents_ready.parquet` |
| Validate | `scripts/validate_cfa_incidents.py` | `logs/cfa_validation_report.json` |
| Load | `scripts/load_cfa_to_supabase.py` | Supabase tables + `logs/cfa_load_report.json` |

Or run end-to-end:

```bash
cd data-engineering/pipelines/cfa_incident_summary
pip install -r requirements.txt
cp .env.example .env   # add Supabase credentials
python main.py --all
```

## Data source (not in Git)

Raw Excel/CSV is **not committed**. See [`data/DATA_SOURCE.md`](data/DATA_SOURCE.md) for the team download link and local path:

```
data/raw/cfa_incident_summary.xlsx
```

## Schema

- **Static:** `CFA_District_Registry` — 20 CFA districts → `location_id` (HQ anchor coordinates)
- **Observation:** `Fire_Incident_Record` — extended with `district_no`, `incident_type_code`, `incident_type`

SQL migrations (run on Supabase/Postgres before `--load`):

1. `sql/create_cfa_district_registry.sql`
2. `sql/alter_fire_incident_record_cfa.sql`

## Prerequisites

1. `location_registry` populated (Victoria grid — see `data-engineering/notebooks/grid/`)
2. `time_registry` populated for incident date range (`data-engineering/notebooks/time/time_registry.ipynb`)
3. `.env` with `SUPABASE_URL` and `SUPABASE_KEY`

**Full setup guide:** [`docs/SUPABASE_SETUP.md`](docs/SUPABASE_SETUP.md)  
**Verify before load:** `python scripts/verify_supabase_setup.py`

## Design decisions

| Topic | Approach |
|-------|----------|
| Location | District HQ lat/lon from CFA map → nearest `location_registry` cell (`nearest` snap) |
| Lineage | `original_latitude` / `original_longitude` = district HQ reference (documented approximation) |
| Datetime | Parsed as `Australia/Melbourne`, floored to minute → `time_id` lookup |
| Unknown districts | Quarantined (not silently dropped without logging) |

## Quantifiable metrics (for PR / 5.2C)

After `--profile` and `--preprocess`, cite:

- `total_rows` vs `output_rows` and `retention_rate_pct`
- `quarantine_*` counts in `data/quarantine/preprocess_stats.json`
- `distinct_incident_id`, `distinct_districts`, `distinct_timestamps` from validation report
- `districts_upserted` / `incidents_upserted` from load report

## Example join (ML / dashboard)

```sql
SELECT
  f.incident_id,
  f.incident_type,
  d.cfa_region,
  t.datetime_record,
  l.grid_latitude,
  l.grid_longitude
FROM fire_incident_record f
JOIN cfa_district_registry d ON f.district_no = d.district_no
JOIN time_registry t ON f.time_id = t.time_id
JOIN location_registry l ON f.location_id = l.location_id;
```

## Testing

```bash
pytest tests/ -q
```

## Notes

- `.env` and raw/processed data files are gitignored (same pattern as [PR #143](https://github.com/InnovAIte-Deakin/InnovAIte_FireFusion_Project/pull/143))
- Module layout follows [PR #152](https://github.com/InnovAIte-Deakin/InnovAIte_FireFusion_Project/pull/152) (`config/`, `scripts/`, `main.py`, reports in `logs/`)

## Author

**Anoop Kashyap Pradeep** — FireFusion Data Engineering
