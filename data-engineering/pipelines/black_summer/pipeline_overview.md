# Black Summer Data Pipeline Overview

## Overview

This pipeline extracts and processes **Black Summer bushfire data (2019–2020)** from Australian bushfire datasets.

The pipeline follows ETL architecture:

Extract → Transform → Load

---

# Pipeline Workflow

Raw Bushfire Dataset (.gdb)
↓
Extract Layers
↓
Filter Black Summer Fires
↓
Extract Geometry
↓
Load to PostgreSQL

---

# Step 1 — Extract Layers

Script:

```
extract_layers.py
```

Purpose:

* Load dataset
* Inspect available layers
* Identify bushfire data

Output:

* Column names
* Dataset preview

---

# Step 2 — Filter Black Summer Fires

Script:

```
extract_black_summer.py
```

Filter Criteria:

* Date Range: 2019-06-01 to 2020-05-31
* Remove invalid records

Output:

```
black_summer.csv
```

---

# Step 3 — Extract Geometry

Script:

```
extract_black_summer_geo.py
```

Purpose:

* Load filtered dataset
* Extract fire boundaries
* Export GeoJSON

Output:

```
black_summer.geojson
```

---

# Step 4 — Load to Database

Script:

```
load_to_postgres.py
```

Operations:

* Connect PostgreSQL
* Upload dataset
* Create table

Final Table:

```
bushfire_black_summer
```

---

# Data Issues Handled

* Missing fire names
* Large polygon warnings
* Null values
* Geometry extraction

---

# Final Output

Database:

PostgreSQL + PostGIS

Table:

```
bushfire_black_summer
```

---

# Pipeline Status

✔ Data Extracted
✔ Data Filtered
✔ Geometry Processed
✔ Database Loaded

---

# Author

Palak Rani
FireFusion Data Engineering
InnovAIte Project
