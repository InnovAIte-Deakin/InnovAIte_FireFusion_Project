# CAMS Atmospheric Dataset Extraction Pipeline
#
# This script extracts CAMS atmospheric composition data from Google Earth Engine
# for Victoria, Australia. The selected variables are Aerosol Optical Depth at
# 550 nm and PM2.5, which provide smoke, aerosol, and air-quality context.
#
# CAMS is used as a complementary atmospheric dataset rather than the main
# ignition predictor. The extracted data is aligned with the ERA5 pipeline using
# the same 5 km spatial grid and 12-hour temporal interval, so both datasets can
# later be merged using grid_id and timestamp.

import ee

ee.Authenticate()
ee.Initialize(project='ee-juverianishath2001')

# =========================================================
# CONFIGURATION
# =========================================================
# Update these three values for each export chunk.
# Example chunks:
# 2021_H1: 2021-01-01 to 2021-07-01
# 2021_H2: 2021-07-01 to 2022-01-01
# 2022_H1: 2022-01-01 to 2022-07-01
# 2022_H2: 2022-07-01 to 2023-01-01

START_DATE = "2022-07-01"
END_DATE = "2023-01-01"
EXPORT_NAME = "FireFusion_CAMS_Victoria_12Hourly_5kmGrid_2022_H2"

GRID_SCALE = 5000
INTERVAL_HOURS = 12

# =========================================================
# Step 1: Load Victoria Boundary
# =========================================================
# The FAO GAUL administrative boundary dataset is used to define Victoria,
# Australia as the study region. Filtering the dataset to Victoria ensures that
# CAMS values are only extracted for the project area relevant to FireFusion.

states = ee.FeatureCollection("FAO/GAUL/2015/level1")

victoria = (
    states
    .filter(ee.Filter.eq("ADM0_NAME", "Australia"))
    .filter(ee.Filter.eq("ADM1_NAME", "Victoria"))
)

print("Victoria features:", victoria.size().getInfo())

# =========================================================
# Step 2: Load CAMS Dataset
# =========================================================
# The ECMWF CAMS Near Real-Time collection provides atmospheric composition
# variables. For this project, the dataset is filtered by date range and clipped
# conceptually to the Victoria study region using filterBounds.

cams = (
    ee.ImageCollection("ECMWF/CAMS/NRT")
    .filterDate(START_DATE, END_DATE)
    .filterBounds(victoria)
)

print("CAMS image count:", cams.size().getInfo())

# =========================================================
# Step 3: Select CAMS Bands
# =========================================================
# Only two CAMS variables are selected for the main dataset:
# 1. total_aerosol_optical_depth_at_550nm_surface
#    - represents aerosol/smoke/haze loading in the atmosphere.
# 2. particulate_matter_d_less_than_25_um_surface
#    - represents fine particulate matter, useful for smoke and air-quality impact.
#
# These features are kept together in one CAMS output table to support easier
# merging and interpretation.

selected_bands = [
    "total_aerosol_optical_depth_at_550nm_surface",
    "particulate_matter_d_less_than_25_um_surface"
]

cams_selected = cams.select(selected_bands)

print("Selected bands:")
print(cams_selected.first().bandNames().getInfo())

# =========================================================
# Step 4: Process CAMS Features
# =========================================================
# This function renames the long GEE band names into shorter project-specific
# feature names. The original system time is preserved so the images can later
# be aggregated and exported with consistent timestamps.

def process_cams_features(image):
    aod = (
        image
        .select("total_aerosol_optical_depth_at_550nm_surface")
        .rename("cams_aod_550")
    )

    pm25 = (
        image
        .select("particulate_matter_d_less_than_25_um_surface")
        .rename("cams_pm25")
    )

    return (
        aod
        .addBands(pm25)
        .copyProperties(image, ["system:time_start"])
    )

cams_processed = cams_selected.map(process_cams_features)

print("Processed bands:")
print(cams_processed.first().bandNames().getInfo())

# =========================================================
# Step 5: Aggregate CAMS into 12-Hour Intervals
# =========================================================
# CAMS contains frequent atmospheric observations. To match the ERA5 extraction
# approach and reduce short-term noise, this function groups images into
# fixed 12-hour windows and calculates the mean value for each window.
#
# Each aggregated image keeps:
# - system:time_start
# - interval_start
# - interval_end

def aggregate_to_12_hourly(image_collection, start_date, end_date, interval_hours=12):
    start = ee.Date(start_date)
    end = ee.Date(end_date)

    total_hours = end.difference(start, "hour")

    time_steps = ee.List.sequence(
        0,
        total_hours.subtract(interval_hours),
        interval_hours
    )

    def create_interval(hour_offset):
        interval_start = start.advance(hour_offset, "hour")
        interval_end = interval_start.advance(interval_hours, "hour")

        interval_collection = image_collection.filterDate(
            interval_start,
            interval_end
        )

        mean_image = (
            interval_collection.mean()
            .set("system:time_start", interval_start.millis())
            .set("interval_start", interval_start.format("YYYY-MM-dd HH:mm"))
            .set("interval_end", interval_end.format("YYYY-MM-dd HH:mm"))
        )

        return mean_image

    return ee.ImageCollection.fromImages(time_steps.map(create_interval))

cams_12hourly = aggregate_to_12_hourly(
    image_collection=cams_processed,
    start_date=START_DATE,
    end_date=END_DATE,
    interval_hours=INTERVAL_HOURS
)

print("12-hour image count:", cams_12hourly.size().getInfo())
print("Bands:", cams_12hourly.first().bandNames().getInfo())

# =========================================================
# Step 6: Create 5 km Grid
# =========================================================
# Victoria is divided into 5 km grid cells to support location-based modelling.
# This matches the ERA5 spatial extraction design and gives every cell a grid_id,
# which is used later as the spatial merge key.

def create_victoria_grid(region, grid_scale=5000):
    grid_projection = ee.Projection("EPSG:3857").atScale(grid_scale)

    grid_image = (
        ee.Image.random()
        .multiply(1000000)
        .toInt()
        .reproject(grid_projection)
    )

    grid = grid_image.reduceToVectors(
        geometry=region.geometry(),
        scale=grid_scale,
        geometryType="polygon",
        reducer=ee.Reducer.countEvery(),
        maxPixels=1e13
    )

    return grid.map(
        lambda feature: feature.set("grid_id", feature.id())
    )

victoria_grid = create_victoria_grid(victoria, GRID_SCALE)

print("Grid cell count:", victoria_grid.size().getInfo())

# =========================================================
# Step 7: Extract Grid Features
# =========================================================
# For each 12-hour CAMS image, the mean CAMS values are calculated for every
# 5 km grid cell. The output is flattened into a table where each row represents
# one grid cell at one 12-hour timestamp.
#
# Output columns include:
# - grid_id
# - datetime
# - timestamp
# - interval_start
# - interval_end
# - cams_aod_550
# - cams_pm25
#
# The reducer scale is kept consistent with the existing ERA5 extraction script.

def extract_grid_cell_features(image_collection, grid):
    def reduce_image(image):
        datetime = ee.Date(image.get("system:time_start"))

        reduced_grid = image.reduceRegions(
            collection=grid,
            reducer=ee.Reducer.mean(),
            scale=11132
        )

        return reduced_grid.map(
            lambda feature: feature
            .set("datetime", datetime.format("YYYY-MM-dd HH:mm"))
            .set("timestamp", datetime.millis())
            .set("interval_start", image.get("interval_start"))
            .set("interval_end", image.get("interval_end"))
        )

    return image_collection.map(reduce_image).flatten()

cams_grid_features = extract_grid_cell_features(
    cams_12hourly,
    victoria_grid
)

# Do not call cams_grid_features.size().getInfo() for 6-month exports.
# The output contains millions of rows, so forcing GEE to compute the size
# interactively can cause a timeout. The export task can still run successfully.

# =========================================================
# Step 8: Export CSV to Google Drive
# =========================================================
# The final grid-level CAMS feature table is exported to Google Drive as a CSV.
# For large time periods, data should be exported in chunks such as 6-month
# intervals to avoid export failures and make downstream handling easier.

task = ee.batch.Export.table.toDrive(
    collection=cams_grid_features,
    description=EXPORT_NAME,
    fileNamePrefix=EXPORT_NAME,
    fileFormat="CSV"
)

task.start()

print("Export task started!")
print(task.status())
