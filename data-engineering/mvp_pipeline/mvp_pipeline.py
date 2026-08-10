"""
FireFusion MVP ETL Pipeline

Purpose:
  Transform raw Victoria fire, weather, and environmental data into a 
  Hub & Spoke schema for analysis and AI model training.

Architecture:
  Hub Tables (Centers):
    - location_registry: Snapped coordinates to 0.1° grid cells
    - time_registry: Hourly batches with seasonal mapping
  
  Observation Tables (Spokes):
    - fire_incident_record: Fire incidents with location_id, time_id
    - weather_observation: Weather data with location_id, time_id
    - vegetation_condition: Vegetation dryness with location_id, time_id
  
  Static Tables:
    - topography_profile: Elevation, slope (location_id only)
    - infrastructure_asset: Facilities, risk category (location_id only)

Process:
  1. Load raw input CSVs
  2. Grid Snap: Convert raw lat/lon to location_id
  3. Time Register: Convert datetime to time_id + season
  4. Validate: Check for nulls, duplicates, bounds
  5. Save: Output aligned tables to CSV

Dependencies:
  pandas, numpy, os, json, datetime
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os


class GridSnapper:
    """
    Snaps raw coordinates to 0.1 degree grid cells (approximately 11km).
    Enables alignment across different data sources with varying coordinate precision.
    
    Victoria bounds:
      North: -33.98, South: -39.20, West: 141.00, East: 150.00
    """
    
    def __init__(self):
        self.grid_size = 0.1
        self.vic_bounds = {
            'min_lat': -39.20,
            'max_lat': -33.98,
            'min_lon': 141.00,
            'max_lon': 150.00
        }
        self.location_registry = {}
        self.next_location_id = 1
    
    def snap(self, lat, lon):
        """
        Snap coordinate to nearest grid cell.
        Returns location_id or None if outside Victoria bounds.
        """
        if not (self.vic_bounds['min_lat'] <= lat <= self.vic_bounds['max_lat'] and
                self.vic_bounds['min_lon'] <= lon <= self.vic_bounds['max_lon']):
            return None
        
        grid_lat = round(lat / self.grid_size) * self.grid_size
        grid_lon = round(lon / self.grid_size) * self.grid_size
        key = (grid_lat, grid_lon)
        
        if key not in self.location_registry:
            self.location_registry[key] = {
                'location_id': self.next_location_id,
                'grid_latitude': grid_lat,
                'grid_longitude': grid_lon,
                'region_name': self._get_region(grid_lat, grid_lon)
            }
            self.next_location_id += 1
        
        return self.location_registry[key]['location_id']
    
    def _get_region(self, lat, lon):
        """Determine Victoria region from grid coordinates."""
        regions = {
            (-37.8, 145.1): "Melbourne",
            (-38.2, 144.4): "Geelong",
            (-36.8, 144.3): "Bendigo",
            (-37.6, 143.9): "Ballarat",
            (-36.1, 147.0): "Wodonga",
            (-38.3, 141.6): "Warrnambool",
        }
        
        min_dist = float('inf')
        closest = "Regional Victoria"
        for (r_lat, r_lon), name in regions.items():
            dist = ((lat - r_lat)**2 + (lon - r_lon)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest = name
        return closest
    
    def to_dataframe(self):
        """Export location registry as DataFrame."""
        data = list(self.location_registry.values())
        return pd.DataFrame(data)


class TimeRegistry:
    """
    Maps raw timestamps to time_id with hourly batching and seasonal mapping.
    Single source of truth for temporal alignment across all observation tables.
    """
    
    def __init__(self):
        self.time_registry = {}
        self.next_time_id = 1
    
    def get_season(self, month):
        """Map month to season (Southern Hemisphere)."""
        if month in [12, 1, 2]:
            return "Summer"
        elif month in [3, 4, 5]:
            return "Autumn"
        elif month in [6, 7, 8]:
            return "Winter"
        else:
            return "Spring"
    
    def register(self, datetime_str):
        """Register timestamp, return time_id."""
        dt = pd.to_datetime(datetime_str)
        hour_batch = dt.replace(minute=0, second=0, microsecond=0)
        key = hour_batch.isoformat()
        
        if key not in self.time_registry:
            self.time_registry[key] = {
                'time_id': self.next_time_id,
                'datetime_record': key,
                'season': self.get_season(dt.month)
            }
            self.next_time_id += 1
        
        return self.time_registry[key]['time_id']
    
    def to_dataframe(self):
        """Export time registry as DataFrame."""
        data = list(self.time_registry.values())
        df = pd.DataFrame(data)
        df = df.sort_values('time_id').reset_index(drop=True)
        return df


class MVPPipeline:
    """
    Main ETL orchestrator.
    Loads raw data, applies Grid Snapper and Time Registry,
    validates output, and saves aligned tables.
    """
    
    def __init__(self, input_dir="input", output_dir="output"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.grid_snapper = GridSnapper()
        self.time_registry = TimeRegistry()
        self.report = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self):
        """Load all input CSV files."""
        print("STEP 1: Loading input data")
        
        self.weather_raw = self._load_csv("weather_sample.csv")
        self.fire_raw = self._load_csv("fire_sample.csv")
        self.vegetation_raw = self._load_csv("vegetation_sample.csv")
        self.topography_raw = self._load_csv("topography_sample.csv")
        self.infrastructure_raw = self._load_csv("infrastructure_sample.csv")
        
        print("  Weather: {} records".format(len(self.weather_raw)))
        print("  Fire: {} records".format(len(self.fire_raw)))
        print("  Vegetation: {} records".format(len(self.vegetation_raw)))
        print("  Topography: {} records".format(len(self.topography_raw)))
        print("  Infrastructure: {} records".format(len(self.infrastructure_raw)))
    
    def _load_csv(self, filename):
        """Load CSV file, return empty DataFrame if not found."""
        path = os.path.join(self.input_dir, filename)
        if os.path.exists(path):
            return pd.read_csv(path)
        else:
            print("  Warning: {} not found".format(filename))
            return pd.DataFrame()
    
    def transform_data(self):
        """Apply Grid Snap and Time Register to all tables."""
        print("\nSTEP 2: Transforming data (Grid Snap + Time Register)")
        
        self.fire_aligned = self._transform_observation(
            self.fire_raw, "incident_id",
            ["original_latitude", "original_longitude", "confidence_score", 
             "source_system", "datetime_record"]
        )
        print("  Fire: {} aligned | {} dropped".format(
            len(self.fire_aligned), len(self.fire_raw) - len(self.fire_aligned)))
        
        self.weather_aligned = self._transform_observation(
            self.weather_raw, "weather_id",
            ["original_latitude", "original_longitude", "temperature_c", 
             "wind_speed_kmh", "relative_humidity", "source_system", "datetime_record"]
        )
        print("  Weather: {} aligned | {} dropped".format(
            len(self.weather_aligned), len(self.weather_raw) - len(self.weather_aligned)))
        
        self.vegetation_aligned = self._transform_observation(
            self.vegetation_raw, "veg_condition_id",
            ["original_latitude", "original_longitude", "dryness_index", 
             "soil_moisture", "vegetation_class", "source_system", "datetime_record"]
        )
        print("  Vegetation: {} aligned | {} dropped".format(
            len(self.vegetation_aligned), len(self.vegetation_raw) - len(self.vegetation_aligned)))
        
        self.topography_aligned = self._transform_static(
            self.topography_raw, "topo_id",
            ["original_latitude", "original_longitude", "elevation_m", "slope_angle"]
        )
        print("  Topography: {} aligned | {} dropped".format(
            len(self.topography_aligned), len(self.topography_raw) - len(self.topography_aligned)))
        
        self.infrastructure_aligned = self._transform_static(
            self.infrastructure_raw, "asset_id",
            ["original_latitude", "original_longitude", "facility_name", "risk_category"]
        )
        print("  Infrastructure: {} aligned | {} dropped".format(
            len(self.infrastructure_aligned), len(self.infrastructure_raw) - len(self.infrastructure_aligned)))
    
    def _transform_observation(self, df, id_col, keep_cols):
        """Transform observation tables (with datetime)."""
        if df.empty:
            return pd.DataFrame()
        
        result = []
        for _, row in df.iterrows():
            lat, lon = row['original_latitude'], row['original_longitude']
            location_id = self.grid_snapper.snap(lat, lon)
            
            if location_id is None:
                continue
            
            time_id = self.time_registry.register(row['datetime_record'])
            
            record = {
                id_col: row[id_col],
                'location_id': location_id,
                'time_id': time_id,
            }
            record.update(row[keep_cols].to_dict())
            result.append(record)
        
        return pd.DataFrame(result)
    
    def _transform_static(self, df, id_col, keep_cols):
        """Transform static tables (no datetime)."""
        if df.empty:
            return pd.DataFrame()
        
        result = []
        for _, row in df.iterrows():
            lat, lon = row['original_latitude'], row['original_longitude']
            location_id = self.grid_snapper.snap(lat, lon)
            
            if location_id is None:
                continue
            
            record = {
                id_col: row[id_col],
                'location_id': location_id,
            }
            record.update(row[keep_cols].to_dict())
            result.append(record)
        
        return pd.DataFrame(result)
    
    def validate(self):
        """Perform data quality checks."""
        print("\nSTEP 3: Validating data quality")
        
        for name, df in [
            ("Fire", self.fire_aligned),
            ("Weather", self.weather_aligned),
            ("Vegetation", self.vegetation_aligned),
            ("Topography", self.topography_aligned),
            ("Infrastructure", self.infrastructure_aligned),
        ]:
            if df.empty:
                print("  {}: No data".format(name))
                continue
            
            checks = {
                'nulls': df.isnull().sum().sum() == 0,
                'location_id': df['location_id'].notna().all(),
                'pk_unique': df.iloc[:, 0].is_unique,
            }
            
            status = "PASSED" if all(checks.values()) else "FAILED"
            print("  {}: {}".format(name, status))
    
    def save_outputs(self):
        """Save aligned tables and registries to CSV."""
        print("\nSTEP 4: Saving outputs")
        
        self._save_csv(self.fire_aligned, "fire_aligned.csv")
        self._save_csv(self.weather_aligned, "weather_aligned.csv")
        self._save_csv(self.vegetation_aligned, "vegetation_aligned.csv")
        self._save_csv(self.topography_aligned, "topography_aligned.csv")
        self._save_csv(self.infrastructure_aligned, "infrastructure_aligned.csv")
        
        location_df = self.grid_snapper.to_dataframe()
        self._save_csv(location_df, "location_registry.csv")
        print("  location_registry.csv ({} grid cells)".format(len(location_df)))
        
        time_df = self.time_registry.to_dataframe()
        self._save_csv(time_df, "time_registry.csv")
        print("  time_registry.csv ({} time periods)".format(len(time_df)))
    
    def _save_csv(self, df, filename):
        """Save DataFrame to CSV."""
        path = os.path.join(self.output_dir, filename)
        df.to_csv(path, index=False)
        print("  {} ({} records)".format(filename, len(df)))
    
    def generate_report(self):
        """Generate pipeline execution report."""
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'input_records': {
                'fire': len(self.fire_raw),
                'weather': len(self.weather_raw),
                'vegetation': len(self.vegetation_raw),
                'topography': len(self.topography_raw),
                'infrastructure': len(self.infrastructure_raw),
            },
            'output_records': {
                'fire': len(self.fire_aligned),
                'weather': len(self.weather_aligned),
                'vegetation': len(self.vegetation_aligned),
                'topography': len(self.topography_aligned),
                'infrastructure': len(self.infrastructure_aligned),
            },
            'registries': {
                'location_ids': len(self.grid_snapper.location_registry),
                'time_ids': len(self.time_registry.time_registry),
            }
        }
        
        report_path = os.path.join(self.output_dir, "pipeline_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print("\nPipeline Report:")
        print("  Grid cells created: {}".format(self.report['registries']['location_ids']))
        print("  Time periods: {}".format(self.report['registries']['time_ids']))
    
    def run(self):
        """Execute full pipeline."""
        print("=" * 70)
        print("FireFusion MVP ETL Pipeline")
        print("=" * 70)
        
        self.load_data()
        self.transform_data()
        self.validate()
        self.save_outputs()
        self.generate_report()
        
        print("\n" + "=" * 70)
        print("Pipeline execution complete")
        print("=" * 70)


if __name__ == "__main__":
    pipeline = MVPPipeline()
    pipeline.run()