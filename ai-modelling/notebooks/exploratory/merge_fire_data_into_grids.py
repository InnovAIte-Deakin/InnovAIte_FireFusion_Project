"""
Merge Historic Bushfire Events into Grid Cells
Spatially join fire polygons to grid cells and aggregate fire statistics.
Output: grid cells with fire data attributes (count, total area, severity measures)
"""

import os
import pandas as pd
import geopandas as gpd
import numpy as np


# ── Configuration ──────────────────────────────────────────────────────────
GRID_SIZE_M = 5000  # Must match the grid generation cell size
GRID_FILE = f"../../src/data/victoria_grid_{GRID_SIZE_M}m.geojson"
FIRE_DATASET_FILE = "../../src/data/unified_historic_fire_dataset.geojson"

OUTPUT_FILE = f"grid_with_fire_data_{GRID_SIZE_M}m.geojson"
OUTPUT_CSV = f"grid_with_fire_data_{GRID_SIZE_M}m.csv"


def load_grid_and_fires(grid_path, fire_path):
    """
    Load grid and fire datasets as GeoDataFrames.
    
    Parameters:
        grid_path (str): Path to grid GeoJSON file
        fire_path (str): Path to fire dataset GeoJSON file
    
    Returns:
        grid_gdf (GeoDataFrame): Grid cells with CRS EPSG:4326
        fire_gdf (GeoDataFrame): Fire polygons with CRS EPSG:4326
    """
    print(f"Loading grid from {grid_path}...")
    grid_gdf = gpd.read_file(grid_path)
    print(f"  Loaded {len(grid_gdf):,} grid cells")
    
    print(f"Loading fire dataset from {fire_path}...")
    fire_gdf = gpd.read_file(fire_path)
    print(f"  Loaded {len(fire_gdf):,} fire records")
    
    # Ensure consistent CRS
    if grid_gdf.crs != "EPSG:4326":
        grid_gdf = grid_gdf.to_crs("EPSG:4326")
    if fire_gdf.crs != "EPSG:4326":
        fire_gdf = fire_gdf.to_crs("EPSG:4326")
    
    return grid_gdf, fire_gdf


def spatial_join_fires_to_grid(grid_gdf, fire_gdf):
    """
    Perform spatial join between fires and grid cells.
    
    Parameters:
        grid_gdf (GeoDataFrame): Grid cells with geometry
        fire_gdf (GeoDataFrame): Fire polygons with geometry
    
    Returns:
        joined (GeoDataFrame): Grid cells with matched fire attributes
    """
    print("Performing spatial join...")
    
    # Spatial join: each fire matched to all cells it intersects
    joined = gpd.sjoin(
        fire_gdf[["fire_id", "fire_name", "ignition_date", "extinguish_date", 
                   "duration_days", "peak_frp", "cumulative_frp", "detection_status",
                   "area_ha", "season", "fire_type", "size_class", "geometry"]],
        grid_gdf[["cell_id", "centroid_lon", "centroid_lat", "geometry"]],
        how="inner",
        predicate="intersects"
    )
    
    print(f"  Spatial join result: {len(joined):,} fire-cell intersections")
    return joined


def aggregate_fires_by_cell(joined, fire_gdf):
    """
    Aggregate fire statistics by grid cell.
    
    Parameters:
        joined (GeoDataFrame): Spatial join result from spatial_join_fires_to_grid()
        fire_gdf (GeoDataFrame): Original fire dataset (for reference)
    
    Returns:
        fire_stats (DataFrame): Fire statistics grouped by cell_id with columns:
            - fire_count: number of unique fires intersecting cell
            - total_area_burned_ha: sum of fire areas
            - max_peak_frp: maximum peak FRP across fires
            - total_cumulative_frp: sum of cumulative FRP
            - fires_detected: count of fires with detection_status='detected'
            - fires_undetected: count with detection_status='imputed_same_day' or 'coverage_gap'
            - dominant_season: most common season
            - avg_duration_days: mean burn duration
    """
    print("Aggregating fire statistics by grid cell...")
    
    fire_stats = joined.groupby("cell_id").agg({
        "fire_id": "nunique",  # Unique fire count
        "area_ha": "sum",  # Total burned area
        "peak_frp": "max",  # Maximum severity
        "cumulative_frp": "sum",  # Total cumulative FRP
        "duration_days": "mean",  # Average duration
    }).rename(columns={
        "fire_id": "fire_count",
        "area_ha": "total_area_burned_ha",
        "peak_frp": "max_peak_frp",
        "cumulative_frp": "total_cumulative_frp",
        "duration_days": "avg_duration_days",
    })
    
    # Detection status breakdown
    detected = joined[joined["detection_status"] == "detected"].groupby("cell_id").size()
    fire_stats["fires_detected"] = detected
    
    undetected = joined[joined["detection_status"].isin(["imputed_same_day", "coverage_gap"])].groupby("cell_id").size()
    fire_stats["fires_undetected"] = undetected
    
    # Fill NaN with 0 for detection counts
    fire_stats["fires_detected"] = fire_stats["fires_detected"].fillna(0).astype(int)
    fire_stats["fires_undetected"] = fire_stats["fires_undetected"].fillna(0).astype(int)
    
    # Dominant season
    dominant_season = joined.groupby("cell_id")["season"].apply(
        lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown"
    )
    fire_stats["dominant_season"] = dominant_season
    
    # Round numeric columns
    for col in ["total_area_burned_ha", "max_peak_frp", "total_cumulative_frp", "avg_duration_days"]:
        if col in fire_stats.columns:
            fire_stats[col] = fire_stats[col].round(2)
    
    fire_stats = fire_stats.reset_index()
    
    print(f"  Aggregated into {len(fire_stats):,} cells with fire data")
    return fire_stats


def merge_stats_with_grid(grid_gdf, fire_stats):
    """
    Merge fire statistics back onto full grid.
    
    Parameters:
        grid_gdf (GeoDataFrame): Original grid cells
        fire_stats (DataFrame): Aggregated fire statistics from aggregate_fires_by_cell()
    
    Returns:
        grid_with_fires (GeoDataFrame): Grid cells with fire data merged (NaN for cells with no fires)
    """
    print("Merging fire statistics with grid...")
    
    grid_with_fires = grid_gdf.merge(fire_stats, on="cell_id", how="left")
    
    # Fill NaN for cells with no fires
    numeric_cols = ["fire_count", "total_area_burned_ha", "max_peak_frp", 
                    "total_cumulative_frp", "fires_detected", "fires_undetected"]
    for col in numeric_cols:
        if col in grid_with_fires.columns:
            grid_with_fires[col] = grid_with_fires[col].fillna(0).astype(int)
    
    # Use 0 for string columns (no fires = no season)
    grid_with_fires["dominant_season"] = grid_with_fires["dominant_season"].fillna("None")
    
    # Handle avg_duration_days
    grid_with_fires["avg_duration_days"] = grid_with_fires["avg_duration_days"].fillna(0.0).round(2)
    
    print(f"  Grid merged: {len(grid_with_fires):,} cells total, "
          f"{(grid_with_fires['fire_count'] > 0).sum():,} cells with fires")
    
    return grid_with_fires


def export_results(grid_with_fires, output_geojson, output_csv):
    """
    Export merged grid with fire data.
    
    Parameters:
        grid_with_fires (GeoDataFrame): Grid cells with fire attributes
        output_geojson (str): Output GeoJSON path
        output_csv (str): Output CSV path
    
    Returns:
        None; writes files to disk and prints confirmation
    """
    print("Exporting results...")
    
    # Reorder columns for clarity
    column_order = [
        "cell_id", "row", "col", "centroid_lon", "centroid_lat", "cell_area_ha",
        "fire_count", "total_area_burned_ha", "max_peak_frp", "total_cumulative_frp",
        "fires_detected", "fires_undetected", "avg_duration_days", "dominant_season",
        "geometry"
    ]
    
    # Keep only columns that exist
    column_order = [col for col in column_order if col in grid_with_fires.columns]
    grid_with_fires = grid_with_fires[column_order]
    
    # Export GeoJSON
    grid_with_fires.to_file(output_geojson, driver="GeoJSON")
    print(f"  ✓ Exported GeoJSON: {output_geojson}")
    
    # Export CSV (without geometry for readability)
    grid_with_fires.drop(columns="geometry").to_csv(output_csv, index=False)
    print(f"  ✓ Exported CSV: {output_csv}")


def print_summary(grid_with_fires):
    """
    Print summary statistics of the merged dataset.
    
    Parameters:
        grid_with_fires (GeoDataFrame): Final merged grid with fire data
    
    Returns:
        None; prints statistics to stdout
    """
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    cells_with_fires = (grid_with_fires["fire_count"] > 0).sum()
    total_fires = grid_with_fires["fire_count"].sum()
    total_area = grid_with_fires["total_area_burned_ha"].sum()
    
    print(f"Total grid cells: {len(grid_with_fires):,}")
    print(f"Cells with fire history: {cells_with_fires:,} ({cells_with_fires/len(grid_with_fires)*100:.1f}%)")
    print(f"Total unique fires in grid: {total_fires:,.0f}")
    print(f"Total area burned: {total_area:,.0f} hectares")
    print(f"Average fires per cell (cells with fires): {total_fires/cells_with_fires:.1f}")
    
    print(f"\nTop 10 cells by fire count:")
    top_cells = grid_with_fires.nlargest(10, "fire_count")[["cell_id", "fire_count", "total_area_burned_ha"]]
    for idx, row in top_cells.iterrows():
        print(f"  {row['cell_id']}: {int(row['fire_count'])} fires, {row['total_area_burned_ha']:.0f} ha")
    
    print(f"\nFire detection status breakdown:")
    print(f"  Detected fires: {grid_with_fires['fires_detected'].sum():,.0f}")
    print(f"  Undetected/imputed fires: {grid_with_fires['fires_undetected'].sum():,.0f}")
    
    season_counts = grid_with_fires[grid_with_fires["dominant_season"] != "None"]["dominant_season"].value_counts()
    print(f"\nDominant seasons in cells with fires:")
    for season, count in season_counts.items():
        print(f"  {season}: {count:,} cells")
    
    print("\n" + "="*70)


def main(grid_path=GRID_FILE, fire_path=FIRE_DATASET_FILE, 
         output_geojson=OUTPUT_FILE, output_csv=OUTPUT_CSV):
    """
    Execute complete pipeline: load data → spatial join → aggregate → merge → export.
    
    Parameters:
        grid_path (str): Path to grid GeoJSON file
        fire_path (str): Path to fire dataset GeoJSON file
        output_geojson (str): Output GeoJSON filename
        output_csv (str): Output CSV filename
    
    Returns:
        grid_with_fires (GeoDataFrame): Final merged grid with fire attributes
    """
    
    # Resolve paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    grid_path = os.path.join(script_dir, grid_path)
    fire_path = os.path.join(script_dir, fire_path)
    output_geojson = os.path.join(script_dir, output_geojson)
    output_csv = os.path.join(script_dir, output_csv)
    
    print("="*70)
    print("MERGE FIRE DATA INTO GRID CELLS")
    print("="*70)
    
    # Pipeline steps
    grid_gdf, fire_gdf = load_grid_and_fires(grid_path, fire_path)
    joined = spatial_join_fires_to_grid(grid_gdf, fire_gdf)
    fire_stats = aggregate_fires_by_cell(joined, fire_gdf)
    grid_with_fires = merge_stats_with_grid(grid_gdf, fire_stats)
    export_results(grid_with_fires, output_geojson, output_csv)
    print_summary(grid_with_fires)
    
    return grid_with_fires


if __name__ == "__main__":
    result = main()
    print("\nProcessing complete!")
