"""
Dataset Preprocessing Module for AI Feature Pipeline

Handles data cleaning, standardization, and preparation for AI model consumption.
Includes column mapping, type conversion, and data quality improvements.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from config.processing_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=DEFAULT_CONFIG.log_level,
    format=DEFAULT_CONFIG.log_format
)
logger = logging.getLogger(__name__)


class DatasetPreprocessor:
    """Preprocesses dataset for AI model compatibility and data quality."""
    
    def __init__(self, config: Optional[Any] = None):
        """Initialize preprocessor with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.preprocessing_stats = {
            'total_rows_processed': 0,
            'rows_removed': 0,
            'rows_kept': 0,
            'columns_processed': 0,
            'transformations_applied': []
        }
    
    def preprocess_chunk(self, df: pd.DataFrame, chunk_id: int = 0) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess a single chunk of data.
        
        Args:
            df: DataFrame chunk to preprocess
            chunk_id: Identifier for the chunk
            
        Returns:
            Tuple of (preprocessed DataFrame, preprocessing statistics)
        """
        logger.info(f"Preprocessing chunk {chunk_id} with {len(df)} rows")
        
        chunk_stats = {
            'chunk_id': chunk_id,
            'input_rows': len(df),
            'output_rows': len(df),
            'removed_rows': 0,
            'transformations': [],
            'column_changes': {}
        }
        
        df_processed = df.copy()
        original_rows = len(df_processed)
        
        # 1. Handle missing values
        if self.config.handle_missing == 'drop':
            df_processed, missing_stats = self._handle_missing_values(df_processed)
            chunk_stats['transformations'].append('missing_values_dropped')
            chunk_stats['column_changes']['missing_values_removed'] = missing_stats
        
        # 2. Remove duplicates
        if self.config.remove_duplicates:
            df_processed, duplicate_stats = self._remove_duplicates(df_processed)
            chunk_stats['transformations'].append('duplicates_removed')
            chunk_stats['column_changes']['duplicates_removed'] = duplicate_stats
        
        # 3. Standardize column names for AI model
        df_processed, column_mapping = self._map_ai_features(df_processed)
        chunk_stats['transformations'].append('ai_features_mapped')
        chunk_stats['column_changes']['feature_mapping'] = column_mapping
        
        # 4. Data type standardization
        df_processed, dtype_changes = self._standardize_data_types(df_processed)
        chunk_stats['transformations'].append('data_types_standardized')
        chunk_stats['column_changes']['dtype_changes'] = dtype_changes
        
        # 5. Extract temporal information
        df_processed, temporal_stats = self._extract_temporal_features(df_processed)
        if temporal_stats['features_extracted']:
            chunk_stats['transformations'].append('temporal_features_extracted')
            chunk_stats['column_changes']['temporal_features'] = temporal_stats
        
        # 6. Clean and validate coordinates
        df_processed, coord_stats = self._clean_coordinates(df_processed)
        if coord_stats['cleaned']:
            chunk_stats['transformations'].append('coordinates_cleaned')
            chunk_stats['column_changes']['coordinate_cleaning'] = coord_stats
        
        # Calculate final statistics
        chunk_stats['output_rows'] = len(df_processed)
        chunk_stats['removed_rows'] = original_rows - len(df_processed)
        
        logger.info(f"Chunk {chunk_id} preprocessing complete: {chunk_stats['output_rows']}/{chunk_stats['input_rows']} rows kept")
        
        return df_processed, chunk_stats
    
    def _handle_missing_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Handle missing values according to configuration."""
        stats = {}
        
        if self.config.handle_missing == 'drop':
            # Count missing values before dropping
            missing_counts = df[self.config.ai_features].isna().sum()
            stats = {col: int(count) for col, count in missing_counts.items() if count > 0}
            
            # Drop rows with missing values in critical features
            critical_features = self.config.ai_features + ['fire_label', 'latitude', 'longitude']
            df_clean = df.dropna(subset=critical_features)
            
            logger.info(f"Dropped {len(df) - len(df_clean)} rows with missing values")
            return df_clean, stats
        
        elif self.config.handle_missing == 'fill':
            # Fill missing values with configured fill values
            df_filled = df.copy()
            
            for col, fill_value in self.config.fill_values.items():
                if col in df_filled.columns:
                    missing_count = df_filled[col].isna().sum()
                    if missing_count > 0:
                        df_filled[col] = df_filled[col].fillna(fill_value)
                        stats[col] = int(missing_count)
            
            return df_filled, stats
        
        else:
            return df, stats
    
    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Remove duplicate records based on universal_key."""
        stats = {'duplicates_removed': 0}
        
        if 'universal_key' in df.columns:
            original_count = len(df)
            df_clean = df.drop_duplicates(subset=['universal_key'], keep='first')
            stats['duplicates_removed'] = original_count - len(df_clean)
            
            if stats['duplicates_removed'] > 0:
                logger.info(f"Removed {stats['duplicates_removed']} duplicate records")
        
        return df, stats
    
    def _map_ai_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Map master dataset column names to AI model expected names."""
        column_mapping = {}
        df_mapped = df.copy()
        
        for master_col, ai_col in self.config.feature_mapping.items():
            if master_col in df.columns:
                df_mapped[ai_col] = df[master_col].copy()
                column_mapping[master_col] = ai_col
        
        logger.info(f"Mapped {len(column_mapping)} features for AI model compatibility")
        return df_mapped, column_mapping
    
    def _standardize_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Standardize data types for consistency."""
        dtype_changes = {}
        df_standardized = df.copy()
        
        # Ensure critical columns have correct types
        type_mapping = {
            'fire_label': 'int64',
            'latitude': 'float64',
            'longitude': 'float64',
            'temperature_2m_c': 'float64',
            'skin_temperature_c': 'float64',
            'soil_temperature_level_1_c': 'float64',
            'surface_solar_radiation_downwards': 'float64',
            'surface_thermal_radiation_downwards': 'float64',
            'u_component_of_wind_10m': 'float64',
            'v_component_of_wind_10m': 'float64',
        }
        
        for col, target_type in type_mapping.items():
            if col in df_standardized.columns:
                try:
                    if target_type == 'int64':
                        df_standardized[col] = pd.to_numeric(df_standardized[col], errors='coerce').astype('Int64')
                    else:
                        df_standardized[col] = pd.to_numeric(df_standardized[col], errors='coerce').astype(target_type)
                    
                    original_type = str(df[col].dtype)
                    if original_type != target_type:
                        dtype_changes[col] = f"{original_type} -> {target_type}"
                        
                except Exception as e:
                    logger.warning(f"Could not convert {col} to {target_type}: {e}")
        
        return df_standardized, dtype_changes
    
    def _extract_temporal_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Extract temporal features from universal_key."""
        temporal_stats = {'features_extracted': [], 'extraction_errors': 0}
        df_temporal = df.copy()
        
        if 'universal_key' in df.columns:
            try:
                # Extract timestamp from universal_key format: "{lon}_{lat}_{timestamp}"
                def extract_timestamp(key_str):
                    try:
                        parts = str(key_str).split('_')
                        if len(parts) >= 3:
                            timestamp_part = '_'.join(parts[2:])  # Handle timestamps with underscores
                            # Parse timestamp (assuming format like YYYYMMDD_HHMM)
                            if len(timestamp_part) >= 8:
                                year = int(timestamp_part[:4])
                                month = int(timestamp_part[4:6])
                                day = int(timestamp_part[6:8])
                                hour = int(timestamp_part[9:11]) if len(timestamp_part) > 9 else 0
                                return pd.Timestamp(year=year, month=month, day=day, hour=hour)
                        return pd.NaT
                    except:
                        return pd.NaT
                
                # Extract timestamp
                df_temporal['timestamp'] = df_temporal['universal_key'].apply(extract_timestamp)
                
                # Extract temporal features
                valid_timestamps = df_temporal['timestamp'].notna()
                if valid_timestamps.any():
                    df_temporal.loc[valid_timestamps, 'year'] = df_temporal.loc[valid_timestamps, 'timestamp'].dt.year
                    df_temporal.loc[valid_timestamps, 'month'] = df_temporal.loc[valid_timestamps, 'timestamp'].dt.month
                    df_temporal.loc[valid_timestamps, 'day'] = df_temporal.loc[valid_timestamps, 'timestamp'].dt.day
                    df_temporal.loc[valid_timestamps, 'hour'] = df_temporal.loc[valid_timestamps, 'timestamp'].dt.hour
                    df_temporal.loc[valid_timestamps, 'day_of_year'] = df_temporal.loc[valid_timestamps, 'timestamp'].dt.dayofyear
                    df_temporal.loc[valid_timestamps, 'season'] = df_temporal.loc[valid_timestamps, 'month'].apply(self._get_season)
                    
                    temporal_stats['features_extracted'] = ['timestamp', 'year', 'month', 'day', 'hour', 'day_of_year', 'season']
                    logger.info(f"Extracted temporal features for {valid_timestamps.sum()} records")
                
            except Exception as e:
                logger.error(f"Error extracting temporal features: {e}")
                temporal_stats['extraction_errors'] = 1
        
        return df_temporal, temporal_stats
    
    def _get_season(self, month: int) -> str:
        """Get season from month (Southern Hemisphere)."""
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        elif month in [9, 10, 11]:
            return 'spring'
        else:
            return 'unknown'
    
    def _clean_coordinates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Clean and validate coordinate data."""
        coord_stats = {'cleaned': False, 'invalid_coords_removed': 0}
        df_clean = df.copy()
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Remove invalid coordinates
            valid_coords = (
                (df_clean['latitude'].between(-90, 90)) &
                (df_clean['longitude'].between(-180, 180)) &
                (df_clean['latitude'].notna()) &
                (df_clean['longitude'].notna())
            )
            
            invalid_count = len(df_clean) - valid_coords.sum()
            if invalid_count > 0:
                df_clean = df_clean[valid_coords]
                coord_stats['cleaned'] = True
                coord_stats['invalid_coords_removed'] = invalid_count
                logger.info(f"Removed {invalid_count} records with invalid coordinates")
        
        return df_clean, coord_stats
    
    def generate_preprocessing_report(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive preprocessing report.
        
        Args:
            chunk_results: List of preprocessing results from each chunk
            
        Returns:
            Comprehensive preprocessing report.
        """
        logger.info("Generating preprocessing report...")
        
        total_input_rows = sum(cr['input_rows'] for cr in chunk_results)
        total_output_rows = sum(cr['output_rows'] for cr in chunk_results)
        total_removed_rows = sum(cr['removed_rows'] for cr in chunk_results)
        
        # Aggregate transformations
        all_transformations = []
        for cr in chunk_results:
            all_transformations.extend(cr['transformations'])
        
        transformation_counts = {}
        for transform in all_transformations:
            transformation_counts[transform] = transformation_counts.get(transform, 0) + 1
        
        # Aggregate column changes
        all_column_changes = {}
        for cr in chunk_results:
            for change_type, change_data in cr['column_changes'].items():
                if change_type not in all_column_changes:
                    all_column_changes[change_type] = {}
                
                if isinstance(change_data, dict):
                    for key, value in change_data.items():
                        if isinstance(value, (int, float)):
                            all_column_changes[change_type][key] = all_column_changes[change_type].get(key, 0) + value
        
        report = {
            'preprocessing_summary': {
                'total_chunks': len(chunk_results),
                'total_input_rows': total_input_rows,
                'total_output_rows': total_output_rows,
                'total_removed_rows': total_removed_rows,
                'retention_rate': (total_output_rows / total_input_rows * 100) if total_input_rows > 0 else 0
            },
            'transformations_applied': transformation_counts,
            'column_changes': all_column_changes,
            'quality_metrics': {
                'data_completeness': (total_output_rows / total_input_rows * 100) if total_input_rows > 0 else 0,
                'processing_efficiency': 'high' if total_removed_rows < total_input_rows * 0.1 else 'medium'
            }
        }
        
        return report


def preprocess_master_dataset(dataset_path: str, config: Optional[Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Preprocess the master dataset end-to-end.
    
    Args:
        dataset_path: Path to the master dataset
        config: Processing configuration
        
    Returns:
        Tuple of (preprocessed DataFrame, preprocessing report)
    """
    preprocessor = DatasetPreprocessor(config)
    
    logger.info(f"Preprocessing {dataset_path}")
    
    try:
        # For demonstration, process a sample
        logger.info("Processing sample dataset...")
        sample_df = pd.read_csv(dataset_path, nrows=10000)
        
        processed_df, sample_stats = preprocessor.preprocess_chunk(sample_df, chunk_id=0)
        
        # Generate report
        report = preprocessor.generate_preprocessing_report([sample_stats])
        
        logger.info(f"Preprocessing complete: {report['preprocessing_summary']['retention_rate']:.1f}% retention rate")
        
        return processed_df, report
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise


if __name__ == "__main__":
    # Run preprocessing when executed directly
    logger.info("Running dataset preprocessing...")
    
    try:
        dataset_path = str(DEFAULT_CONFIG.input_dataset)
        processed_df, results = preprocess_master_dataset(dataset_path)
        
        print("\n=== PREPROCESSING REPORT ===")
        print(f"Input Rows: {results['preprocessing_summary']['total_input_rows']:,}")
        print(f"Output Rows: {results['preprocessing_summary']['total_output_rows']:,}")
        print(f"Retention Rate: {results['preprocessing_summary']['retention_rate']:.1f}%")
        
        print(f"\nTransformations Applied:")
        for transform, count in results['transformations_applied'].items():
            print(f"  - {transform}: {count} chunks")
        
        print(f"\nProcessed Data Shape: {processed_df.shape}")
        print(f"AI Features Available: {len(DEFAULT_CONFIG.ai_feature_names)}")
        
        print(f"\nSample of processed data:")
        print(processed_df[DEFAULT_CONFIG.ai_feature_names + ['fire_label']].head())
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise