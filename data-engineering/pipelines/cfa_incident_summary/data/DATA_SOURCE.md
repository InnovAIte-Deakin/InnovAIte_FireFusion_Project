# CFA Incident Summary — Data Source

The raw dataset is **not stored in this repository**.

## Dataset

- **Name:** CFA Incident Summary (historical incident records)
- **Format:** Excel (`.xlsx`) or CSV export
- **Columns:** `incident_datetime`, `incident_no`, `District_no`, `incident_type_code`, `incident_type`

## Local setup

1. Download the dataset from your team’s shared storage (Deakin cloud / team drive).
2. Place the file at:

   ```
   data-engineering/pipelines/cfa_incident_summary/data/raw/cfa_incident_summary.xlsx
   ```

   Or set `CFA_INCIDENT_RAW_PATH` in `.env` to your local path.

## Official / team link

> **Add your team’s download URL here** (OneDrive, SharePoint, DataVic, etc.)  
> Example: `https://<your-team-link>/CFA_Incident_Summary.xlsx`

## Notes

- Datetime format: `D/MM/YYYY  H:MM:SS AM/PM` (e.g. `1/07/2020  1:17:10 AM`)
- Location is **district-level** (`District_no`), not incident GPS — see `data/reference/cfa_district_registry.csv`
- Timezone for parsing: `Australia/Melbourne`
