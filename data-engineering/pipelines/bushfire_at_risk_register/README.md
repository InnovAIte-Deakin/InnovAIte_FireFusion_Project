# DE 2025–2026 Bushfire At-Risk Register Data Pipeline

## Overview
This project is a simple Python-based data pipeline that fetches and combines two Victorian Government open datasets related to bushfire risk for schools and early childhood services.

The pipeline:
- extracts data from two API endpoints
- merges the records into one dataset
- reassigns continuous `_id` values
- saves the final combined output as a JSON file

This is an MVP version intended to demonstrate the core ETL flow.

---

## Data Sources

### 1. Bushfire At-Risk Register (BARR) – February 2026
This dataset contains schools, kindergartens, and early childhood services assessed to be at the highest bushfire risk, including categories 0, 1, 2, and 3.

API resource:
- `a927e847-5818-43e2-8fe6-ad7e469fabd1`

### 2. Schools and Early Childhood Services at Risk of Grassfire – Category 4 – February 2026
This dataset contains facilities assessed as Category 4 risk.

API resource:
- `39f89a56-af38-49cf-98d3-26eca92c4466`

---

## Project Structure

```bash
.
├── bushfire_at_risk_register.py
├── bushfire_at_risk_register.json
└── README.md
```

---

## Requirements

* Python 3.x

This project uses only Python standard libraries:

* `urllib.request`
* `json`

No external packages are required.

---

## How It Works

The script performs the following steps:

1. Sends API requests to both dataset endpoints
2. Loads the JSON responses into Python objects
3. Extends the first dataset with records from the second dataset
4. Reassigns `_id` values so the merged records have continuous numbering
5. Writes the final combined dataset to a local JSON file

---

## Run the Pipeline

```bash
python bushfire_at_risk_register.py
```

After execution, the output file will be created:

```bash
bushfire_at_risk_register.json
```

---

## Output

The output is a single JSON file containing the combined records from both datasets.

### Sample record

```json
{
  "_id": 1,
  "Fire risk category 2025-26": "CAT 3",
  "Facility name": "3C Kidz Care - Edinburgh College",
  "Education sector": "Early Childhood Services",
  "Facility address": "33-61 Edinburgh Rd",
  "Town/Suburb": "Lilydale",
  "LGA": "Yarra Ranges",
  "Fire weather district": "Central"
}
```

---

## Output Fields

The merged dataset includes fields such as:

* `_id`
* `Fire risk category 2025-26`
* `Facility name`
* `Education sector`
* `Facility address`
* `Town/Suburb`
* `LGA`
* `Fire weather district`

---

## Limitations

This MVP pipeline has a few limitations:

* the API query uses `limit=1000`, so pagination is not handled
* there is no error handling for failed API requests
* there is no schema validation or data cleaning
* the output is stored locally only
* duplicate checking is not implemented

---

## Future Improvements

Possible next steps for this project:

* add API pagination to ensure all records are collected
* include exception handling for network or API errors
* validate schema consistency between datasets
* store the output in a database instead of a local JSON file
* add logging for monitoring pipeline execution
* schedule the pipeline for regular updates
* transform the data into CSV or Parquet for analytics workflows

---

## Use Case

This combined dataset can support:

* bushfire risk monitoring
* reporting and dashboard development
* mapping of at-risk education facilities
* downstream analytics and data engineering workflows
* integration with fire weather or emergency alert systems
