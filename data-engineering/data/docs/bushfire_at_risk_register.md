# DE 2025–2026 Bushfire At-Risk Register Data Pipeline (MVP)
*Trimester 1, 2026*

Planner task: [Link to MS Planner](https://planner.cloud.microsoft/webui/v1/plan/H6UJiW7Qd0-pqy0lPXGgZ8gADBxI/view/board/task/_TbgdLGkFU-7tO6T1dp32MgAG5kl?tid=d02378ec-1688-46d5-8540-1c28b5f470f6).  

**Project Leads:** THAI HA NGUYEN, WILSON DJUNAWAN and DHRUV HIREN SURTI 
**Document contribution:** THAI HA NGUYEN.

## 1. Overview

This work builds a **Minimum Viable Data Pipeline (MVP)** to ingest, combine, and store bushfire risk data for Victorian schools and early childhood services.

The pipeline integrates two official datasets from the Victorian Government:

* Bushfire At-Risk Register (BARR) – Categories 0–3
* Grassfire Risk List – Category 4

The final output is a **unified dataset** containing all facilities at bushfire risk across categories.


## 2. Data Sources

### 2.1 Bushfire At-Risk Register (BARR)

* Source: Victorian Government Open Data
* Includes: Schools and services in **Fire Risk Categories 0–3**
* Purpose:

  * Trigger relocation, closure, or remote learning
  * Pre-emptive closure on **Catastrophic Fire Danger Rating (FDR)** days

API Endpoint:

```
https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=a927e847-5818-43e2-8fe6-ad7e469fabd1
```

### 2.2 Grassfire Risk (Category 4)

* Source: Victorian Government Open Data
* Includes: Facilities in **Category 4 (lower risk)**
* Purpose:

  * Pre-emptive closure on **Catastrophic FDR days only**

API Endpoint:

```
https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=39f89a56-af38-49cf-98d3-26eca92c4466
```


## 3. Pipeline Architecture (MVP)

### Steps:

1. **Extract**

   * Fetch both datasets via API (JSON format)

2. **Transform**

   * Merge datasets into a single list
   * Standardise structure
   * Reassign unique `_id` values

3. **Load**

   * Save as a local JSON file


## 4. Implementation

### 4.1 Code

```python
import urllib.request
import json

# Step 1: Define API URLs
url_1 = 'https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=a927e847-5818-43e2-8fe6-ad7e469fabd1&limit=1000'
url_2 = 'https://discover.data.vic.gov.au/api/3/action/datastore_search?resource_id=39f89a56-af38-49cf-98d3-26eca92c4466&limit=1000'

# Step 2: Extract data from APIs
fileobj_1 = urllib.request.urlopen(url_1)
fileobj_2 = urllib.request.urlopen(url_2)

data_1 = json.load(fileobj_1)
data_2 = json.load(fileobj_2)

# Step 3: Combine datasets
data = data_1
data['result']['records'].extend(data_2['result']['records'])

records = data['result']['records']

# Step 4: Reassign continuous IDs
for i, record in enumerate(records, start=1):
    record['_id'] = i

# Step 5: Save to JSON file
with open('bushfire_at_risk_register.json', 'w') as f:
    json.dump(records, f)

print("Pipeline executed successfully. Data saved to bushfire_at_risk_register.json")
```


## 5. Output Schema

Each record contains:

| Field                        | Description                                   |
| ---------------------------- | --------------------------------------------- |
| `_id`                        | Unique identifier                             |
| `Fire risk category 2025-26` | Risk category (CAT 0–4)                       |
| `Facility name`              | Name of school/service                        |
| `Education sector`           | Government / Non-government / Early Childhood |
| `Facility address`           | Street address                                |
| `Town/Suburb`                | Location                                      |
| `LGA`                        | Local Government Area                         |
| `Fire weather district`      | Fire risk region                              |


## 6. Sample Output

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


## 7. Assumptions & Limitations

* API limit is set to **1000 records** (may require pagination in future)
* Schema consistency assumed between datasets
* No data validation or cleaning applied (MVP scope)
* Data is stored locally (no database yet)


## 8. Future Improvements

### Data Engineering Enhancements

* Implement **pagination handling** for full dataset ingestion
* Add **data validation & schema checks**
* Handle missing/null values

### Storage & Processing

* Store data in:

  * PostgreSQL / Data Warehouse
  * Data Lake (Azure Blob / S3)
* Convert to **Parquet/CSV** for analytics

### Automation

* Schedule pipeline using:

  * Airflow / Prefect / Cron
* Add logging and monitoring

### Analytics & Use Cases

* Risk mapping dashboard (Power BI / Tableau)
* Integration with **weather APIs**
* Predictive risk modeling (ML)


## 9. Conclusion

This MVP demonstrates a simple yet effective **ETL pipeline**:

* Integrates multiple government datasets
* Produces a unified bushfire risk dataset
* Provides a foundation for scalable data engineering and analytics
