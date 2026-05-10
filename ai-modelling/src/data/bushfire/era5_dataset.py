import ee

ee.Authenticate()

ee.Initialize(project='project-id')

"""# Step 2: Load Victoria Boundary

In this step, we load the official boundary of Victoria, Australia using the FAO GAUL administrative boundaries dataset available in Google Earth Engine.

This boundary will be used as the study region for our ERA5 weather data extraction. Using a defined region helps ensure that only data relevant to Victoria is collected for the FireFusion bushfire forecasting project.
"""

# Load Australia state boundaries
states = ee.FeatureCollection("FAO/GAUL/2015/level1")

# Filter Victoria boundary
victoria = (
    states
    .filter(ee.Filter.eq("ADM0_NAME", "Australia"))
    .filter(ee.Filter.eq("ADM1_NAME", "Victoria"))
)

# Validate result
print("Victoria features:", victoria.size().getInfo())
print(victoria.first().getInfo())

"""# Step 3: Load ERA5 Weather Dataset

In this step, we connect to the ERA5 hourly reanalysis dataset from Google Earth Engine.

ERA5 provides historical weather variables such as:
- Air temperature
- Rainfall
- Wind
- Pressure
- Humidity-related variables

These features are useful for predicting wildfire risk.
"""

# Load ERA5 hourly dataset
era5 = (
    ee.ImageCollection("ECMWF/ERA5/HOURLY")
    .filterDate("2012-01-01", "2021-01-01")
    .filterBounds(victoria)
)

# Check collection size
print("ERA5 image count:", era5.size().getInfo())

# Show first image bands
first_image = era5.first()
print("Bands:", first_image.bandNames().getInfo())

"""# Step 4: Select Bushfire-Relevant ERA5 Variables

Instead of using all ERA5 bands, we select a smaller set of variables strongly linked to wildfire behaviour.

These variables help represent:
- Heat
- Dryness
- Rainfall
- Wind movement
- Atmospheric pressure
"""

selected_bands = [
    "temperature_2m",
    "dewpoint_temperature_2m",
    "total_precipitation",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
    "surface_pressure"
]

era5_selected = era5.select(selected_bands)

print("Selected bands:")
print(era5_selected.first().bandNames().getInfo())

"""# Step 5: Process ERA5 Weather Features

ERA5 stores temperature variables in Kelvin, so they need to be converted into Celsius for easier interpretation.

Wind is provided as two components:
- u wind = east/west direction
- v wind = north/south direction

For modelling, we create wind speed from both components because fire spread is strongly affected by wind strength.
"""

def process_era5_features(image):
    # Convert temperature from Kelvin to Celsius
    temperature_2m_c = (
        image.select("temperature_2m")
        .subtract(273.15)
        .rename("temperature_2m_c")
    )

    dewpoint_temperature_2m_c = (
        image.select("dewpoint_temperature_2m")
        .subtract(273.15)
        .rename("dewpoint_temperature_2m_c")
    )

    # Keep precipitation and pressure
    precipitation = image.select("total_precipitation")
    pressure = image.select("surface_pressure")

    # Wind components
    u_wind = image.select("u_component_of_wind_10m")
    v_wind = image.select("v_component_of_wind_10m")

    # Calculate wind speed
    wind_speed_10m = (
        u_wind.pow(2)
        .add(v_wind.pow(2))
        .sqrt()
        .rename("wind_speed_10m")
    )

    return (
        temperature_2m_c
        .addBands(dewpoint_temperature_2m_c)
        .addBands(precipitation)
        .addBands(pressure)
        .addBands(u_wind)
        .addBands(v_wind)
        .addBands(wind_speed_10m)
        .copyProperties(image, ["system:time_start"])
    )


era5_processed = era5_selected.map(process_era5_features)

print("Processed bands:")
print(era5_processed.first().bandNames().getInfo())

"""# Step 6: Aggregate Hourly ERA5 Data into 12-Hour Intervals

ERA5 provides hourly weather data. For FireFusion, the hourly values are aggregated into 12-hour intervals to create smoother and more model-ready features.

This reduces short-term noise and aligns the weather data with the project’s fire prediction timeline.
"""

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

        interval_collection = image_collection.filterDate(interval_start, interval_end)

        mean_image = (
            interval_collection.mean()
            .set("system:time_start", interval_start.millis())
            .set("interval_start", interval_start.format("YYYY-MM-dd HH:mm"))
            .set("interval_end", interval_end.format("YYYY-MM-dd HH:mm"))
        )

        return mean_image

    return ee.ImageCollection.fromImages(time_steps.map(create_interval))


era5_12hourly = aggregate_to_12_hourly(
    image_collection=era5_processed,
    start_date="2012-01-01",
    end_date="2021-01-01",
    interval_hours=12
)

print("12-hour image count:", era5_12hourly.size().getInfo())
print("Bands:", era5_12hourly.first().bandNames().getInfo())

"""# Step 7: Create 5 km x 5 km Spatial Grid

To support location-based wildfire prediction, Victoria is divided into 5 km grid cells.

Each cell receives:
- grid_id
- location geometry
- weather values later

This allows the model to learn where fires may occur, not only when.
"""

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


victoria_grid = create_victoria_grid(victoria, 5000)

print("Grid cell count:", victoria_grid.size().getInfo())

"""# Step 8: Extract ERA5 Features for Each Grid Cell

In this step, the 12-hour ERA5 images are reduced over each 5 km grid cell.

For each grid cell and each 12-hour interval, the script calculates the mean value of each ERA5 weather variable.

The output will be a table with:
- grid_id
- datetime
- interval_start
- interval_end
- temperature
- dewpoint temperature
- precipitation
- pressure
- wind components
- wind speed
"""

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

era5_export_collection = era5_12hourly.filterDate(
    "2012-01-01",
    "2012-02-01"
)

era5_grid_features = extract_grid_cell_features(
    era5_export_collection,
    victoria_grid
)

print("Extracted row count:", era5_grid_features.size().getInfo())
print("Sample row:")
print(era5_grid_features.first().getInfo())

"""# Step 9: Export ERA5 Grid Dataset to CSV

The extracted ERA5 grid-level dataset is exported to Google Drive as a CSV file.

This CSV can later be used for:
- data cleaning
- merging with VIIRS fire labels
- feature engineering
- LSTM or baseline model training
"""

export_name = "FireFusion_ERA5_Victoria_12Hourly_5kmGrid_2012_2020"

task = ee.batch.Export.table.toDrive(
    collection=era5_grid_features,
    description=export_name,
    fileNamePrefix=export_name,
    fileFormat="CSV"
)

task.start()