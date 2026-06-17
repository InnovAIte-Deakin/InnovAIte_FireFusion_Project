# FireFusion Aspect Pipeline

## Overview
This repository contains my individual contribution to the FireFusion data engineering stream.

The focus of this work is the **aspect feature** from topography data. The pipeline follows the team’s data engineering standards and produces a structured, reproducible output for downstream use.

## Objective
The objective of this pipeline is to:
1. download DEM data for a sample area,
2. generate an aspect raster from the DEM,
3. export sample aspect values to a CSV file,
4. validate the output for downstream integration.

## Dataset Used
- Source: SRTM1 DEM
- Extraction: using `eio` / elevation
- Transformation: `gdaldem aspect`
- Output: aspect raster and structured CSV

## Repository Alignment
This work follows the FireFusion repository structure:

- `data/raw/` → DEM input (local only)
- `data/processed/` → generated outputs
- `pipelines/` → scripts for extraction and processing
- `reports/` → validation outputs
- `schema/` → database draft

Note: Raw and processed data are kept local and not pushed to GitHub.

## Files Produced
- `data/dem_sample.tif`
- `data/aspect_sample.tif`
- `data/aspect_sample_points.csv`
- `reports/aspect_validation_report.json`
- `schema/aspect_schema.sql`

## Workflow
1. Extract DEM data using `eio`
2. Transform DEM to aspect raster using `gdaldem`
3. Convert raster to structured CSV points
4. Validate raster and CSV outputs
5. Generate schema and report for handoff

Pipeline flow:
Extract → Transform → Validate → Output → Handoff

## Validation
- CRS, bounds, and raster shape checked
- NoData handled correctly
- Aspect values verified within 0–360 range
- CSV checked for duplicates and structure

## Outcome
This pipeline provides a working MVP for the aspect feature.

The output is:
- reproducible from raw input
- aligned with FireFusion structure
- ready for integration with other datasets (fire, weather, etc.)

## Contributor
Abdul Suboor Mohammed
