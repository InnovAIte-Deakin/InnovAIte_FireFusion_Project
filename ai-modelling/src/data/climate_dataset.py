import ee

def initialize_earth_engine() -> None: 
  """
  Initialize Google Earth Engine.
  
  This function assumes authentication has already been completed using earthengine authenticate.

  Returns: 
    None
  """
  ee.Initialize()

def get_victoria_boundary() -> ee.FeatureCollection:
  """
  Load the Victoria boundary from the FAO GAUL dataset.

  The boundary is retrieved from the FAO GAUL level1 dataset and filtered to return only the state of Victoria, Australia.

  Returns: 
    ee.FeatureCollection: FeatureCollection representing Victoria boundary
  """
  states = ee.FeatureCollection("FAO/GAUL/2015/level1")
  victoria = (
    states
    .filter(ee.Filter.eq("ADM0_NAME", "Australia"))
    .filter(ee.Filter.eq("ADM1_NAME", "Victoria"))
  )
  return victoria

def load_climate_data(
  region: ee.FeatureCollection,
  start_date: str = "2012-01-01",
  end_date: str = "2020-12-31"
) -> ee.ImageCollection:
  """
  Load TerraClimate data for the selected region and date range.
  
  Selected variables:
  - soil: soil moisture
  - def: climatic water deficit
  - pr: precipitation
  
  This function is designed to be extended later to support:
  - ERA5-Land hourly datasets
  - ERA5 atmospheric variables
  - additional climate sources

  Parameters: 
    region (ee.FeatureCollection): Geographic region for filtering
    start_date (str): Start date (YYYY-MM-DD)
    end_date (str): End date (YYYY-MM-DD)

  Returns:
    ee.ImageCollection: Filtered TerraClimate dataset
  """
  # Narrow region to bounding box
  region_bounds = region.geometry().bounds()
  
  terraclimate = (
    ee.ImageCollection("IDAHO_EPSCOR/TERRACLIMATE")
    .filterDate(start_date, end_date)
    .filterBounds(region_bounds)
    .select(["soil", "def", "pr"])
  )
  return terraclimate

def print_dataset_summary(climate_data: ee.ImageCollection) -> None:
  """
  Print a simple summary of the dataset for quick checking.

  Displays:
  - number of images
  - selected bands
  - sample image id

  Parameters:
    climate_data (ee.ImageCollection): dataset to summarize

  Returns:
    None
  """
  first_image = climate_data.first()
  print("Climate dataset loaded successfully.")
  print("Number of images: ", climate_data.size().getInfo())
  print("Selected bands: ", first_image.bandNames().getInfo())
  print("Sample image ID: ", first_image.get("system:index").getInfo())

def main() -> None:
  """
  Main function for loading Victoria climate data.

  Steps: 
  1. Initialize Earth Engine
  2. Load Victoria boundary
  3. Load TerraClimate dataset
  4. Print dataset summary
  """
  initialize_earth_engine()
  victoria = get_victoria_boundary()
  climate_data = load_climate_data(victoria)
  print_dataset_summary(climate_data)

if __name__ == "__main__":
  main()
