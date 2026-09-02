"""
Dataset Validation Module for AI Feature Pipeline

Comprehensive validation of environmental dataset for AI model consumption.
Includes spatial validation, data quality checks, and consistency validation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from config.processing_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=DEFAULT_CONFIG.log_level,
    format=DEFAULT_CONFIG.log_format
)
logger = logging.getLogger(__name__)


class DatasetValidator:
    """Validates dataset quality and consistency for AI model requirements."""
    
    def __init__(self, config: Optional[Any] = None):
        """Initialize validator with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.validation_results = {
            'total_rows': 0,
            'passed_rows': 0,
            'failed_rows': 0,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
    
    def validate_chunk(self, df, chunk_id: int = 0) -> Dict[str, Any]:
        """
        Validate a single chunk of data.
        
        Args:
            df: DataFrame chunk to validate
            chunk_id: Identifier for the chunk
            
        Returns:
            Validation results for this chunk.
        """
        # Validate input type
        if not isinstance(df, pd.DataFrame):
            logger.error(f"Expected DataFrame, got {type(df)}")
            return {
                'chunk_id': chunk_id,
                'input_rows': 0,
                'output_rows': 0,
                'removed_rows': 0,
                'errors': [f"Expected DataFrame, got {type(df)}"],
                'warnings': [],
                'statistics': {},
                'schema_validation': {'passed': False, 'errors': ["Invalid input type"]},
                'spatial_validation': {'passed': False, 'errors': ["Invalid input type"]},
                'quality_validation': {'passed': False, 'errors': ["Invalid input type"]},
                'feature_validation': {'passed': False, 'errors': ["Invalid input type"]},
                'duplicate_validation': {'passed': False, 'errors': ["Invalid input type"]},
            }
        
        logger.info(f"Validating chunk {chunk_id} with {len(df)} rows")
        
        chunk_results = {
            'chunk_id': chunk_id,
            'input_rows': len(df),
            'output_rows': len(df),
            'removed_rows': 0,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 1. Schema validation
        schema_results = self._validate_schema(df)
        chunk_results['schema_validation'] = schema_results
        
        if not schema_results['passed']:
            chunk_results['errors'].extend(schema_results['errors'])
        
        # 2. Spatial validation
        spatial_results = self._validate_spatial_coordinates(df)
        chunk_results['spatial_validation'] = spatial_results
        chunk_results['statistics']['invalid_coordinates'] = spatial_results['invalid_count']
        
        # 3. Data quality validation
        quality_results = self._validate_data_quality(df)
        chunk_results['quality_validation'] = quality_results
        chunk_results['statistics'].update(quality_results['statistics'])
        
        # 4. Feature validation for AI model
        feature_results = self._validate_ai_features(df)
        chunk_results['feature_validation'] = feature_results
        
        # 5. Duplicate validation
        duplicate_results = self._validate_duplicates(df)
        chunk_results['duplicate_validation'] = duplicate_results
        chunk_results['statistics']['duplicates'] = duplicate_results['duplicate_count']
        
        # Aggregate errors and warnings
        chunk_results['errors'].extend(spatial_results['errors'])
        chunk_results['errors'].extend(quality_results['errors'])
        chunk_results['errors'].extend(feature_results['errors'])
        
        chunk_results['warnings'].extend(spatial_results['warnings'])
        chunk_results['warnings'].extend(quality_results['warnings'])
        chunk_results['warnings'].extend(feature_results['warnings'])
        
        # Calculate final row count after removing invalid rows
        if self.config.validation_strict:
            valid_rows = len(df) - chunk_results['statistics']['invalid_coordinates']
            chunk_results['output_rows'] = valid_rows
            chunk_results['removed_rows'] = len(df) - valid_rows
        
        logger.info(f"Chunk {chunk_id} validation complete: {chunk_results['output_rows']}/{chunk_results['input_rows']} rows valid")
        
        return chunk_results
    
    def _validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate DataFrame schema against expected columns and types."""
        results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'missing_columns': [],
            'extra_columns': [],
            'dtype_mismatches': []
        }
        
        # Check required columns
        expected_columns = set(self.config.required_columns)
        actual_columns = set(df.columns)
        
        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns
        
        if missing_columns:
            results['missing_columns'] = list(missing_columns)
            results['errors'].append(f"Missing required columns: {missing_columns}")
            results['passed'] = False
        
        if extra_columns:
            results['extra_columns'] = list(extra_columns)
            results['warnings'].append(f"Extra columns found: {extra_columns}")
        
        # Check data types (skip if expected_dtypes is None)
        if hasattr(self.config, 'expected_dtypes') and self.config.expected_dtypes is not None:
            for col in self.config.required_columns:
                if col in df.columns:
                    expected_dtype = self.config.expected_dtypes.get(col)
                    if expected_dtype:
                        actual_dtype = str(df[col].dtype)
                        if actual_dtype != expected_dtype:
                            results['dtype_mismatches'].append({
                                'column': col,
                                'expected': expected_dtype,
                                'actual': actual_dtype
                            })
                            if self.config.validation_strict:
                                results['errors'].append(f"Type mismatch for {col}: expected {expected_dtype}, got {actual_dtype}")
                                results['passed'] = False
                            else:
                                results['warnings'].append(f"Type mismatch for {col}: expected {expected_dtype}, got {actual_dtype}")
        
        return results
    
    def _validate_spatial_coordinates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate latitude and longitude coordinates."""
        results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'invalid_count': 0,
            'invalid_lat_count': 0,
            'invalid_lon_count': 0,
            'out_of_victoria_count': 0
        }
        
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            results['errors'].append("Missing latitude or longitude columns")
            results['passed'] = False
            return results
        
        # Latitude validation
        lat_invalid = df['latitude'].isna() | (df['latitude'] < -90) | (df['latitude'] > 90)
        results['invalid_lat_count'] = lat_invalid.sum()
        
        # Longitude validation
        lon_invalid = df['longitude'].isna() | (df['longitude'] < -180) | (df['longitude'] > 180)
        results['invalid_lon_count'] = lon_invalid.sum()
        
        # Victoria region validation (optional warning)
        victoria_lat_invalid = (df['latitude'] < self.config.validation_thresholds['victoria_latitude']['min']) | \
                              (df['latitude'] > self.config.validation_thresholds['victoria_latitude']['max'])
        victoria_lon_invalid = (df['longitude'] < self.config.validation_thresholds['victoria_longitude']['min']) | \
                              (df['longitude'] > self.config.validation_thresholds['victoria_longitude']['max'])
        
        results['out_of_victoria_count'] = (victoria_lat_invalid | victoria_lon_invalid).sum()
        
        # Total invalid coordinates
        invalid_coords = lat_invalid | lon_invalid
        results['invalid_count'] = invalid_coords.sum()
        
        # Generate messages
        if results['invalid_lat_count'] > 0:
            results['errors'].append(f"Invalid latitude values: {results['invalid_lat_count']} rows")
            results['passed'] = False
        
        if results['invalid_lon_count'] > 0:
            results['errors'].append(f"Invalid longitude values: {results['invalid_lon_count']} rows")
            results['passed'] = False
        
        if results['out_of_victoria_count'] > 0:
            results['warnings'].append(f"Points outside Victoria region: {results['out_of_victoria_count']} rows")
        
        return results
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data quality including missing values and ranges."""
        results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'statistics': {
                'missing_values': {},
                'out_of_range_values': {},
                'null_fire_labels': 0
            }
        }
        
        # Check missing values in critical columns
        critical_columns = self.config.ai_features + ['fire_label', 'latitude', 'longitude']
        
        for col in critical_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    results['statistics']['missing_values'][col] = missing_count
                    if col in self.config.ai_features:
                        results['errors'].append(f"Missing values in critical feature {col}: {missing_count} rows")
                        results['passed'] = False
                    else:
                        results['warnings'].append(f"Missing values in {col}: {missing_count} rows")
        
        # Check fire label validity
        if 'fire_label' in df.columns:
            invalid_labels = ~df['fire_label'].isin([0, 1])
            invalid_count = invalid_labels.sum()
            if invalid_count > 0:
                results['errors'].append(f"Invalid fire labels: {invalid_count} rows")
                results['passed'] = False
        
        # Check reasonable ranges for environmental features
        range_checks = {
            'temp_2m_c': ('temperature_min', 'temperature_max'),
            'skin_temp_c': ('temperature_min', 'temperature_max'),
            'soil_temp_c': ('temperature_min', 'temperature_max'),
        }
        
        for col, (min_key, max_key) in range_checks.items():
            if col in df.columns:
                min_val = self.config.validation_thresholds[min_key]
                max_val = self.config.validation_thresholds[max_key]
                
                out_of_range = (df[col] < min_val) | (df[col] > max_val)
                out_of_range_count = out_of_range.sum()
                
                if out_of_range_count > 0:
                    results['statistics']['out_of_range_values'][col] = out_of_range_count
                    results['warnings'].append(f"Out of range values in {col}: {out_of_range_count} rows")
        
        return results
    
    def _validate_ai_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate that all required AI features are present and valid."""
        results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'missing_features': [],
            'invalid_features': []
        }
        
        # Check for missing AI features
        for feature in self.config.ai_features:
            if feature not in df.columns:
                results['missing_features'].append(feature)
                results['errors'].append(f"Missing AI feature: {feature}")
                results['passed'] = False
            else:
                # Check for null values in features
                null_count = df[feature].isna().sum()
                if null_count > 0:
                    results['invalid_features'].append({
                        'feature': feature,
                        'null_count': null_count
                    })
                    results['errors'].append(f"Null values in AI feature {feature}: {null_count} rows")
                    results['passed'] = False
        
        return results
    
    def _validate_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate for duplicate records."""
        results = {
            'passed': True,
            'errors': [],
            'warnings': [],
            'duplicate_count': 0,
            'duplicate_keys': []
        }
        
        # Check duplicates based on universal_key if available
        if 'universal_key' in df.columns:
            duplicate_mask = df.duplicated(subset=['universal_key'], keep=False)
            results['duplicate_count'] = duplicate_mask.sum()
            
            if results['duplicate_count'] > 0:
                duplicates = df[duplicate_mask]['universal_key'].unique()
                results['duplicate_keys'] = list(duplicates[:10])  # Show first 10
                
                if self.config.validation_strict:
                    results['errors'].append(f"Found {results['duplicate_count']} duplicate records")
                    results['passed'] = False
                else:
                    results['warnings'].append(f"Found {results['duplicate_count']} duplicate records")
        
        return results
    
    def generate_validation_report(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive validation report from all chunks.
        
        Args:
            chunk_results: List of validation results from each chunk
            
        Returns:
            Comprehensive validation report.
        """
        logger.info("Generating validation report...")
        
        total_input_rows = sum(cr['input_rows'] for cr in chunk_results)
        total_output_rows = sum(cr['output_rows'] for cr in chunk_results)
        total_removed_rows = sum(cr['removed_rows'] for cr in chunk_results)
        
        # Aggregate statistics
        all_statistics = {}
        for cr in chunk_results:
            for key, value in cr['statistics'].items():
                if key not in all_statistics:
                    all_statistics[key] = 0
                if isinstance(value, (int, float)):
                    all_statistics[key] += value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        full_key = f"{key}_{sub_key}"
                        if full_key not in all_statistics:
                            all_statistics[full_key] = 0
                        if isinstance(sub_value, (int, float)):
                            all_statistics[full_key] += sub_value
        
        # Aggregate errors and warnings
        all_errors = []
        all_warnings = []
        
        for cr in chunk_results:
            all_errors.extend(cr['errors'])
            all_warnings.extend(cr['warnings'])
        
        # Error summary
        error_summary = {}
        for error in all_errors:
            error_type = error.split(':')[0] if ':' in error else 'general'
            error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        report = {
            'validation_summary': {
                'total_chunks': len(chunk_results),
                'total_input_rows': total_input_rows,
                'total_output_rows': total_output_rows,
                'total_removed_rows': total_removed_rows,
                'validation_passed': len(all_errors) == 0,
                'data_quality_score': (total_output_rows / total_input_rows * 100) if total_input_rows > 0 else 0
            },
            'statistics': all_statistics,
            'error_summary': error_summary,
            'all_errors': all_errors,
            'all_warnings': all_warnings,
            'recommendations': self._generate_recommendations(error_summary, all_statistics)
        }
        
        return report
    
    def _generate_recommendations(self, error_summary: Dict[str, int], statistics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if error_summary.get('Invalid latitude values', 0) > 0:
            recommendations.append("Review latitude coordinate validation and data source")
        
        if error_summary.get('Invalid longitude values', 0) > 0:
            recommendations.append("Review longitude coordinate validation and data source")
        
        if error_summary.get('Missing AI feature', 0) > 0:
            recommendations.append("Ensure all required AI features are present in the dataset")
        
        if statistics.get('duplicates', 0) > 0:
            recommendations.append("Consider removing duplicate records based on universal_key")
        
        if any('Missing values' in error for error in error_summary):
            recommendations.append("Implement missing value imputation strategy for environmental features")
        
        if len(recommendations) == 0:
            recommendations.append("Dataset validation passed - no immediate actions required")
        
        return recommendations


def validate_master_dataset(dataset_path: str, config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Validate the master dataset end-to-end.
    
    Args:
        dataset_path: Path to the master dataset
        config: Processing configuration
        
    Returns:
        Comprehensive validation results.
    """
    validator = DatasetValidator(config)
    
    # Quick validation using sample
    logger.info(f"Performing validation on {dataset_path}")
    
    try:
        # Read sample for quick validation
        sample_df = pd.read_csv(dataset_path, nrows=10000)
        sample_results = validator.validate_chunk(sample_df, chunk_id=0)
        
        # Generate report
        report = validator.generate_validation_report([sample_results])
        
        logger.info(f"Validation complete: {report['validation_summary']['validation_passed']}")
        
        return report
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    # Run validation when executed directly
    logger.info("Running dataset validation...")
    
    try:
        dataset_path = str(DEFAULT_CONFIG.input_dataset)
        results = validate_master_dataset(dataset_path)
        
        print("\n=== VALIDATION REPORT ===")
        print(f"Validation Passed: {results['validation_summary']['validation_passed']}")
        print(f"Data Quality Score: {results['validation_summary']['data_quality_score']:.1f}%")
        print(f"Total Rows: {results['validation_summary']['total_input_rows']:,}")
        print(f"Valid Rows: {results['validation_summary']['total_output_rows']:,}")
        
        if results['all_errors']:
            print(f"\nErrors Found: {len(results['all_errors'])}")
            for error in results['all_errors'][:5]:  # Show first 5
                print(f"  - {error}")
        
        if results['all_warnings']:
            print(f"\nWarnings: {len(results['all_warnings'])}")
            for warning in results['all_warnings'][:3]:  # Show first 3
                print(f"  - {warning}")
        
        print(f"\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  - {rec}")
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise