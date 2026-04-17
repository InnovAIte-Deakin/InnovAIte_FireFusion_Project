# FireFusion Aspect Pipeline

## Overview
This is my topography contribution for the FireFusion project.
My focus is on the aspect feature.

## Objective
The objective of this pipeline is to:
1. download DEM data for a sample area,
2. generate an aspect raster from the DEM,
3. export sample aspect values to a CSV file,
4. validate the output for downstream use.

## Dataset Used
- Base DEM source: SRTM1 DEM downloaded using `eio`
- Derived output: Aspect raster generated using `gdaldem aspect`

## Files Produced
- `data/dem_sample.tif`
- `data/aspect_sample.tif`
- `data/aspect_sample_points.csv`
- `reports/aspect_validation_report.json`
- `schema/aspect_schema.sql`

## Workflow
1. Download DEM using `eio`
2. Generate aspect raster using `gdaldem`
3. Export sample point values to CSV
4. Validate output values and metadata
5. Prepare schema and report files for handoff

## Outcome
This provides a working MVP for the aspect feature and can later be integrated into the broader FireFusion ETL workflow.