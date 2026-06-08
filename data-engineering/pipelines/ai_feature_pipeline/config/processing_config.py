"""
Processing Configuration for AI Feature Pipeline

Central configuration management for the FireFusion AI feature processing pipeline.
Includes paths, processing parameters, and validation settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, List

class ProcessingConfig:
    """Configuration settings for AI feature pipeline processing."""
    
    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.parent.parent.parent.parent
        self.pipeline_dir = Path(__file__).parent.parent
        self.data_dir = self.pipeline_dir / "data"
        self.logs_dir = self.pipeline_dir / "logs"
        self.output_dir = self.pipeline_dir / "output"
        
        # Input/Output file paths
        self.input_dataset = self.base_dir.parent / "FireFusion_Master_Dataset.csv"
        self.output_dataset = self.output_dir / "processed_master_dataset.csv"
        self.validation_report = self.logs_dir / "validation_report.json"
        self.processing_log = self.logs_dir / "processing.log"
        
        # Processing parameters
        self.chunksize = 100000  # Rows per chunk for memory efficiency
        self.max_workers = 4      # Parallel processing workers
        self.validation_strict = True  # Strict validation mode
        
        # Feature mapping: master_dataset -> ai_model_expected
        self.feature_mapping = {
            'temp_2m_c': 'temperature_2m_c',
            'skin_temp_c': 'skin_temperature_c',
            'soil_temp_c': 'soil_temperature_level_1_c',
            'surface_solar_radiation_downwards': 'surface_solar_radiation_downwards',
            'surface_thermal_radiation_downwards': 'surface_thermal_radiation_downwards',
            'u_component_of_wind_10m': 'u_component_of_wind_10m',
            'v_component_of_wind_10m': 'v_component_of_wind_10m',
        }
        
        # Required columns for validation
        self.required_columns = [
            'system:index', 'fire_label', 'fire_temp_raw', 'latitude', 'longitude',
            'skin_temp_c', 'soil_moist_root', 'soil_moist_surf', 'soil_temp_c',
            'stable_grid_id', 'surface_solar_radiation_downwards',
            'surface_thermal_radiation_downwards', 'temp_2m_c', 'total_precip_mm',
            'u_component_of_wind_10m', 'universal_key', 'v_component_of_wind_10m'
        ]
        
        # AI model features (output columns)
        self.ai_features = list(self.feature_mapping.keys())
        self.ai_feature_names = list(self.feature_mapping.values())
        
        # Validation thresholds
        self.validation_thresholds = {
            'latitude': {'min': -90, 'max': 90},
            'longitude': {'min': -180, 'max': 180},
            'victoria_latitude': {'min': -40, 'max': -37},  # Victoria region
            'victoria_longitude': {'min': 140, 'max': 151},
            'fire_label': {'values': [0, 1]},
            'relative_humidity_max': 100,  # If humidity column exists
            'temperature_min': -50,         # Realistic temperature range
            'temperature_max': 60,
        }
        
        # Data type expectations
        self.expected_dtypes = None
        
        # Processing options
        self.remove_duplicates = True
        self.handle_missing = 'drop'  # 'drop' or 'fill'
        self.fill_values = {}  # For fill strategy
        
        # Export settings
        self.export_format = 'csv'
        self.include_index = False
        self.compression = None  # 'gzip', 'bz2', etc.
        
        # Logging configuration
        self.log_level = 'INFO'
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.data_dir, self.logs_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_ai_feature_columns(self) -> List[str]:
        """Get the list of feature columns expected by AI model."""
        return self.ai_feature_names.copy()
    
    def get_master_feature_columns(self) -> List[str]:
        """Get the list of corresponding columns in master dataset."""
        return self.ai_features.copy()
    
    def get_feature_mapping_dict(self) -> Dict[str, str]:
        """Get the feature mapping dictionary."""
        return self.feature_mapping.copy()
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that input paths exist and are accessible."""
        return {
            'input_dataset_exists': self.input_dataset.exists(),
            'base_dir_exists': self.base_dir.exists(),
            'pipeline_dir_exists': self.pipeline_dir.exists(),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'chunksize': self.chunksize,
            'max_workers': self.max_workers,
            'validation_strict': self.validation_strict,
            'feature_mapping': self.feature_mapping,
            'required_columns': self.required_columns,
            'ai_features': self.ai_features,
            'validation_thresholds': self.validation_thresholds,
            'expected_dtypes': self.expected_dtypes,
            'remove_duplicates': self.remove_duplicates,
            'handle_missing': self.handle_missing,
            'export_format': self.export_format,
            'log_level': self.log_level,
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"ProcessingConfig(chunksize={self.chunksize}, validation_strict={self.validation_strict})"

# Default configuration instance
DEFAULT_CONFIG = ProcessingConfig()

# Environment-specific configurations
DEVELOPMENT_CONFIG = ProcessingConfig()
DEVELOPMENT_CONFIG.chunksize = 10000  # Smaller chunks for development
DEVELOPMENT_CONFIG.validation_strict = False

PRODUCTION_CONFIG = ProcessingConfig()
PRODUCTION_CONFIG.chunksize = 200000  # Larger chunks for production
PRODUCTION_CONFIG.max_workers = 8      # More workers for production