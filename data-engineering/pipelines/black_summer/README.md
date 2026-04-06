# FireFusion — Black Summer Data Pipeline

## Overview

This module focuses on extracting and processing **Black Summer Bushfire (2019–2020)** data for the FireFusion project.

The goal of this pipeline is to:

* Extract bushfire data from geospatial dataset
* Filter Black Summer fires
* Process geometry data
* Load dataset into PostgreSQL/PostGIS
* Prepare data for analysis and visualization

---

## Dataset

Australian Bushfire Historical Dataset (.gdb)

Filtered Period:

* Start: June 2019
* End: May 2020

This corresponds to the **Black Summer Bushfires** in Australia.

---

## Tools Used

* Python
* GeoPandas
* Pandas
* PostgreSQL
* PostGIS
* SQLAlchemy

---

## Pipeline Steps

### Step 1 — Extract Dataset Layers

Script:

```bash
extract_layers.py
```

Purpose:

* Load .gdb dataset
* Inspect dataset structure
* Identify bushfire layer

---

### Step 2 — Filter Black Summer Fires

Script:

```bash
extract_black_summer.py
```

Operations:

* Filter fires between 2019–2020
* Clean dataset
* Export filtered fires

Output:

```
black_summer.csv
```

---

### Step 3 — Extract Geometry Data

Script:

```bash
extract_black_summer_geo.py
```

Operations:

* Load filtered fire IDs
* Extract geometry
* Convert to GeoJSON

Output:

```
black_summer.geojson
```

---

### Step 4 — Load to PostgreSQL

Script:

```bash
load_to_postgres.py
```

Operations:

* Connect PostgreSQL
* Create table
* Upload geospatial data

Final Table:

```
bushfire_black_summer
```

---

## Folder Structure

```
data-engineering/
│
├── pipelines/
│   └── black_summer/
│       ├── extract_layers.py
│       ├── extract_black_summer.py
│       ├── extract_black_summer_geo.py
│       └── load_to_postgres.py
│
├── database/
│   └── schema.sql
│
└── docs/
    └── pipeline_overview.md
```

---

## Output

Database Table:

```
bushfire_black_summer
```

Contains:

* Fire Name
* Fire Area
* State
* Fire Type
* Geometry

---

## Contribution

This pipeline prepares **Black Summer bushfire dataset** for:

* Risk analysis
* Visualization
* Machine learning models

---

## Author

Palak Rani
FireFusion — Data Engineering Team
