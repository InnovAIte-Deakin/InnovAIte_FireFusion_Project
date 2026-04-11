# Soil Moisture Pipeline Next Steps

## Contributor
Archit Chandna

## Dataset
NASA SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture Geophysical Data

## Work completed so far
- Downloaded and accessed SMAP HDF5 files from NASA Earthdata
- Extracted Australia-specific surface and root zone soil moisture data
- Created a cleaned dataset for Australia
- Generated visualisations for surface soil moisture, root zone soil moisture, and time-series trends
- Added the project files to the FireFusion GitHub repository
- Merged the initial soil moisture analysis contribution into the main branch

## Current goal
Extend the existing soil moisture pipeline so it is more aligned with the team’s Sprint 1 ETL and PostgreSQL workflow.

## Planned work
- Add dataset validation checks
  - duplicate checks
  - null checks
  - soil moisture range checks
  - Australia latitude/longitude boundary checks
- Save a validation report
- Save a processed validated CSV in a structured output folder
- Create a PostgreSQL-ready schema file for downstream integration
- Prepare the dataset output so it can be used by backend and AI modelling teams

## Why this matters for FireFusion
Soil moisture is an important dryness-related environmental factor. Low surface and root zone soil moisture can indicate drier land conditions, which may contribute to higher bushfire risk when combined with weather, vegetation, and other environmental variables. This work helps build a cleaner ETL-ready dataset for future bushfire risk modelling.

## Expected deliverables
- validated processed dataset
- validation report
- PostgreSQL schema file
- updated notebook / pipeline documentation
- follow-up pull request