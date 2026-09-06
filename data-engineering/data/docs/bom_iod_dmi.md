# Indian Ocean Dipole (IOD) Dipole Mode Index (DMI) Data Pipeline

Contributor: **FireFusion Data Engineering Stream**

## Pipeline Name

Indian Ocean Dipole (IOD) NOAA PSL DMI Data Pipeline

## Pipeline Script

```text
fetch_iod.py
```

## Purpose

This pipeline extracts monthly Sea Surface Temperature (SST) anomaly indices for the Indian Ocean Dipole (Dipole Mode Index / DMI) from NOAA Physical Sciences Laboratory (PSL) public endpoints.

The output supports the FireFusion project by providing macro-climate teleconnection features (`dmi_anomaly`, `dmi_lag6m`, `iod_phase`) to pre-condition fuel dryness and long-term bushfire risk predictions in Australia.

---

## Source Information

* Source: Australian Bureau of Meteorology (BOM) & NOAA Physical Sciences Laboratory
* Provider: NOAA Physical Sciences Laboratory (PSL)
* API / Dataset URL: `https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmiwest.had.long.data` & `https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmieast.had.long.data`
* Collection method: HTTP GET request using Python `urllib.request`
* Data format from source: Space-delimited ASCII text
* Output format: CSV
* Refresh frequency: Monthly
* Pipeline owner: Data Engineering stream

---

## Input Data

The script fetches data directly from the official NOAA PSL endpoints:

```text
https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmiwest.had.long.data
https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmieast.had.long.data
```

Raw data is preserved unchanged in `data/raw/iod_dmi_raw_<YYYYMMDD>.csv` for audit lineage.

---

## Variables & Output Schema

| Column Name | Description | Type | Unit/Range | Null Allowed | Notes |
|-------------|-------------|------|------------|--------------|-------|
| `iod_id` | Primary Key | `INTEGER` | `1` to `N` | No | Entity primary key following team rule |
| `time_id` | Universal Master Calendar Key | `INTEGER` | `YYYYMMDDHH` | No | Foreign key linking to `Time_Registry` |
| `datetime_record` | Standard month-start timestamp | `TIMESTAMP` | `YYYY-MM-01 00:00:00` | No | Month-start alignment |
| `record_year_month` | Year-Month string | `VARCHAR` | `YYYY-MM` | No | e.g. `'2024-01'` |
| `dmi_anomaly` | Dipole Mode Index anomaly | `NUMERIC` | `-3.0` to `+3.0 °C` | No | SST anomaly difference ($\text{West} - \text{East}$) |
| `iod_phase` | Active IOD Phase | `VARCHAR` | `'Positive IOD'`, `'Negative IOD'`, `'Neutral'` | No | Derived categorical phase |
| `dmi_lag6m` | 6-Month Prior DMI Anomaly | `NUMERIC` | `-3.0` to `+3.0 °C` | Yes (first 6 rows) | Derived fuel drying pre-conditioning lag |
| `original_source` | Data Lineage Origin | `VARCHAR` | `'NOAA_PSL_DMI'` | No | Standard lineage tracking |

---

## Data Processing Steps

1. **Extraction**: Fetch raw space-delimited ASCII data for both Western and Eastern Indian Ocean poles from NOAA PSL endpoints and store in `data/raw/`.
2. **DMI Calculation**: Merge Western (`dmiwest`) and Eastern (`dmieast`) SST anomalies by Year and Month, and compute $\text{dmi\_anomaly} = \text{West} - \text{East}$.
3. **Date Alignment**: Map month names to 2-digit numeric month strings and construct `datetime_record` (`YYYY-MM-01 00:00:00`).
4. **Master Time Key**: Generate integer `time_id` (`YYYYMM0100`) aligned with the central `Time_Registry` architecture.
5. **Feature Engineering**: Compute `dmi_lag6m` (6-month lag) and derive categorical `iod_phase` (`Positive IOD` if DMI >= +0.40°C, `Negative IOD` if DMI <= -0.40°C).
6. **Primary Key Assignment**: Add sequential `iod_id` (1, 2, 3, ...) as the first column.
7. **Output Delivery**: Save processed CSV files to `data/processed/iod_dmi_processed_<YYYYMMDD>.csv` and `datasets/iod/iod_dmi_<YYYYMMDD>.csv`.

---

## Output Data

* **Raw Storage**: `data-engineering/data/raw/iod_dmi_raw_<YYYYMMDD>.csv`
* **Processed Target**: `data-engineering/data/processed/iod_dmi_processed_<YYYYMMDD>.csv`
* **Dataset Target**: `data-engineering/datasets/iod/iod_dmi_<YYYYMMDD>.csv`
