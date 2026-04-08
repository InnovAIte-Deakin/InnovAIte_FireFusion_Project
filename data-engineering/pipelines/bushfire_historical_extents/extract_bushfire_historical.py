import geopandas as gpd

def extract():
    """Load the raw Geodatabase file"""
    print("Loading dataset...")
    gdf = gpd.read_file(
        "Bushfire Extents - Historical (2025).gdb",
        layer="National_Historical_Bushfire_Extents_v4"
    )
    print(f"Total records loaded: {len(gdf)}")
    return gdf

def transform(gdf):
    """Clean and filter the dataset"""
    # Filter to Victoria
    print("Filtering to Victoria...")
    vic = gdf[gdf['state'] == 'VIC (Victoria)'].copy()
    print(f"Victorian records: {len(vic)}")

    # Drop unnecessary columns
    vic = vic.drop(columns=['SHAPE_Length', 'SHAPE_Area', 'capt_method', 'agency'])

    # Fill missing values
    vic['fire_id'] = vic['fire_id'].fillna('Unknown')
    vic['ignition_cause'] = vic['ignition_cause'].fillna('Unknown')

    # Convert date columns to string
    vic['ignition_date'] = vic['ignition_date'].astype(str)
    vic['extinguish_date'] = vic['extinguish_date'].astype(str)
    vic['capture_date'] = vic['capture_date'].astype(str)

    # Filter to Black Summer (2019-2020)
    black_summer = vic[vic['ignition_date'].str.startswith(('2019', '2020'))].copy()
    print(f"Black Summer records (2019-2020): {len(black_summer)}")

    return vic, black_summer

def load(vic, black_summer):
    """Save the cleaned datasets as GeoJSON"""
    print("Saving files...")
    vic.to_file("victoria_bushfire_historical.geojson", driver="GeoJSON")
    black_summer.to_file("victoria_bushfire_black_summer.geojson", driver="GeoJSON")
    print("Done!")

if __name__ == "__main__":
    gdf = extract()
    vic, black_summer = transform(gdf)
    load(vic, black_summer)