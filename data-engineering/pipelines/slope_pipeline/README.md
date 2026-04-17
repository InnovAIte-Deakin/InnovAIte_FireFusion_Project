# Terrain Slope Pipeline

Implements a topography data pipeline for the FireFusion project using SRTM elevation data.

---

## Pipeline

SRTM elevation data → grid generation → elevation extraction → data cleaning → slope computation → processed dataset

---

## Files

- slope_pipeline.py (main pipeline script)
- slope_pipeline.ipynb (development notebook)
- README.md (documentation)

---

## Purpose

Generate slope values across Victoria as a topographic feature for bushfire risk modelling.

Slope is important because fire spreads faster uphill, making it a key variable for prediction models.

---

## Data Source

- Dataset: SRTM (Shuttle Radar Topography Mission)
- Provider: NASA
- Type: Digital Elevation Model (DEM)

---

## Output

The pipeline generates a structured dataset with:
- latitude
- longitude
- elevation
- slope

---

## Notes

- Dataset output is not included due to repository data storage rules
- Pipeline is designed to be reusable and scalable

---

## Contributor

- Name: Nouman Ullah Khan
- Role: Data Engineer (Topography - Slope Dataset)
