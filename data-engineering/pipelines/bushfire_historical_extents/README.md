# Bushfire Historical Extents Pipeline



## Overview

This pipeline extracts and transforms historical bushfire extent data for Victoria from the Australian Digital Atlas. It produces two cleaned GeoJSON files for use in the FireFusion fire-spread forecasting model.



## Data Source

- **Provider:** Australian Digital Atlas (Geoscience Australia)

- **URL:** https://digital.atlas.gov.au/datasets/524e2962bd8b4968b8df9f9774345926/about

- **Format:** Geodatabase (.gdb)

- **Note:** No API is available for this dataset. It must be manually downloaded as a bulk file.



## Setup

Install the required dependencies:

```
pip install -r requirements.txt

```



## Usage

1. Download the dataset from the URL above

2. Place the `.gdb` file in the same folder as the script

3. Run the script:

```
python extract_bushfire_historical.py
```



## Output

Two GeoJSON files will be generated:

- `victoria_bushfire_historical.geojson` — All Victorian records (87,771)

- `victoria_bushfire_black_summer.geojson` — Black Summer 2019-2020 records (16,154)