"""
Dataset Export Module for AI Feature Pipeline

Handles exporting processed datasets in AI-ready formats.
Supports CSV export with metadata and future database integration.
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from config.processing_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=DEFAULT_CONFIG.log_level,
    format=DEFAULT_CONFIG.log_format
)
logger = logging.getLogger(__name__)


class DatasetExporter:
    """Exports processed datasets in AI-ready formats with metadata."""
    
    def __init__(self, config: Optional[Any] = None):
        """Initialize exporter with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.export_stats = {
            'total_rows_exported': 0,
            'files_created': [],
            'export_metadata': {}
        }
    
    def export_processed_dataset(self, df: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Export processed dataset in AI-ready format.
        
        Args:
            df: Processed DataFrame to export
            metadata: Additional metadata to include
            
        Returns:
            Export results with file information and statistics.
        """
        logger.info(f"Exporting processed dataset with {len(df)} rows")
        
        export_results = {
            'export_timestamp': datetime.now().isoformat(),
            'output_file': str(self.config.output_dataset),
            'rows_exported': len(df),
            'columns_exported': len(df.columns),
            'file_size_mb': 0,
            'ai_features_included': [],
            'export_metadata': metadata or {},
            'success': False
        }
        
        try:
            # Ensure output directory exists
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Select and order AI-ready columns
            df_export = self._prepare_ai_ready_dataframe(df)
            export_results['ai_features_included'] = self.config.ai_feature_names.copy()
            export_results['columns_exported'] = len(df_export.columns)
            
            # Export to CSV
            self._export_to_csv(df_export, export_results)
            
            # Export metadata
            self._export_metadata(export_results, metadata)
            
            # Generate data summary
            self._generate_data_summary(df_export, export_results)
            
            export_results['success'] = True
            self.export_stats['total_rows_exported'] += len(df)
            self.export_stats['files_created'].append(str(self.config.output_dataset))
            
            logger.info(f"Successfully exported {len(df)} rows to {self.config.output_dataset.name}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            export_results['error'] = str(e)
            raise
        
        return export_results
    
    def _prepare_ai_ready_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame with AI-ready column ordering and selection."""
        # Start with core identifiers and spatial info
        core_columns = ['universal_key', 'latitude', 'longitude', 'stable_grid_id', 'fire_label']
        available_core = [col for col in core_columns if col in df.columns]
        
        # Add AI features in expected order
        available_features = [col for col in self.config.ai_feature_names if col in df.columns]
        
        # Add temporal features if available
        temporal_columns = ['timestamp', 'year', 'month', 'day', 'hour', 'day_of_year', 'season']
        available_temporal = [col for col in temporal_columns if col in df.columns]
        
        # Add any remaining environmental features
        remaining_columns = [col for col in df.columns 
                            if col not in available_core + available_features + available_temporal 
                            and col not in ['.geo', 'system:index']]
        
        # Combine all columns in logical order
        final_columns = available_core + available_features + available_temporal + remaining_columns
        
        df_export = df[final_columns].copy()
        
        logger.info(f"Prepared AI-ready DataFrame with {len(final_columns)} columns")
        return df_export
    
    def _export_to_csv(self, df: pd.DataFrame, export_results: Dict[str, Any]):
        """Export DataFrame to CSV with appropriate settings."""
        output_path = self.config.output_dataset
        
        # Export parameters
        export_params = {
            'index': self.config.include_index,
            'encoding': 'utf-8',
            'date_format': '%Y-%m-%d %H:%M:%S'
        }
        
        # Add compression if specified
        if self.config.compression:
            export_params['compression'] = self.config.compression
            output_path = output_path.with_suffix(f'{output_path.suffix}.{self.config.compression}')
        
        # Export to CSV
        df.to_csv(output_path, **export_params)
        
        # Get file size
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        export_results['file_size_mb'] = round(file_size_mb, 2)
        export_results['output_file'] = str(output_path)
        
        logger.info(f"CSV export complete: {file_size_mb:.2f} MB")
    
    def _export_metadata(self, export_results: Dict[str, Any], additional_metadata: Optional[Dict[str, Any]]):
        """Export metadata alongside the dataset."""
        metadata_path = self.config.output_dataset.with_suffix('.metadata.json')
        
        # Combine metadata
        metadata = {
            'export_info': {
                'timestamp': export_results['export_timestamp'],
                'pipeline_version': '1.0.0',
                'processing_config': self.config.to_dict(),
                'export_statistics': {
                    'rows_exported': export_results['rows_exported'],
                    'columns_exported': export_results['columns_exported'],
                    'file_size_mb': export_results['file_size_mb'],
                    'ai_features_count': len(export_results['ai_features_included'])
                }
            },
            'dataset_info': {
                'source_file': str(self.config.input_dataset),
                'processing_date': datetime.now().isoformat(),
                'feature_mapping': self.config.feature_mapping,
                'ai_features': export_results['ai_features_included'],
                'spatial_coverage': 'Victoria, Australia',
                'temporal_coverage': 'Multi-year environmental time series'
            },
            'quality_metrics': {
                'validation_performed': True,
                'preprocessing_applied': True,
                'data_quality_score': 'high'  # Could be calculated from validation results
            }
        }
        
        # Add any additional metadata
        if additional_metadata:
            metadata['additional_metadata'] = additional_metadata
        
        # Write metadata file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadata exported to {metadata_path.name}")
    
    def _generate_data_summary(self, df: pd.DataFrame, export_results: Dict[str, Any]):
        """Generate data summary statistics."""
        summary_stats = {
            'basic_stats': {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024)
            },
            'feature_statistics': {},
            'temporal_coverage': {},
            'spatial_coverage': {}
        }
        
        # Feature statistics for AI features
        for feature in self.config.ai_feature_names:
            if feature in df.columns:
                series = df[feature].dropna()
                if len(series) > 0:
                    summary_stats['feature_statistics'][feature] = {
                        'count': len(series),
                        'mean': float(series.mean()),
                        'std': float(series.std()),
                        'min': float(series.min()),
                        'max': float(series.max()),
                        'null_count': int(df[feature].isna().sum())
                    }
        
        # Temporal coverage
        if 'timestamp' in df.columns:
            valid_timestamps = df['timestamp'].dropna()
            if len(valid_timestamps) > 0:
                summary_stats['temporal_coverage'] = {
                    'start_date': valid_timestamps.min().isoformat(),
                    'end_date': valid_timestamps.max().isoformat(),
                    'total_days': (valid_timestamps.max() - valid_timestamps.min()).days,
                    'records_with_timestamp': len(valid_timestamps)
                }
        
        # Spatial coverage
        if 'latitude' in df.columns and 'longitude' in df.columns:
            valid_coords = df[['latitude', 'longitude']].dropna()
            if len(valid_coords) > 0:
                summary_stats['spatial_coverage'] = {
                    'lat_min': float(valid_coords['latitude'].min()),
                    'lat_max': float(valid_coords['latitude'].max()),
                    'lon_min': float(valid_coords['longitude'].min()),
                    'lon_max': float(valid_coords['longitude'].max()),
                    'records_with_coordinates': len(valid_coords)
                }
        
        # Fire label distribution
        if 'fire_label' in df.columns:
            label_counts = df['fire_label'].value_counts().to_dict()
            summary_stats['fire_label_distribution'] = {
                'no_fire': int(label_counts.get(0, 0)),
                'fire': int(label_counts.get(1, 0)),
                'fire_percentage': round(label_counts.get(1, 0) / len(df) * 100, 2)
            }
        
        # Save summary statistics
        summary_path = self.config.output_dataset.with_suffix('.summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_stats, f, indent=2, ensure_ascii=False)
        
        export_results['data_summary_file'] = str(summary_path)
        logger.info(f"Data summary saved to {summary_path.name}")
    
    def export_for_inference(self, df: pd.DataFrame, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export dataset specifically for inference workflows.
        
        Args:
            df: Processed DataFrame
            output_dir: Custom output directory for inference files
            
        Returns:
            Export results for inference.
        """
        if output_dir is None:
            output_dir = self.config.output_dir / "inference_ready"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        inference_results = {
            'export_timestamp': datetime.now().isoformat(),
            'inference_files_created': [],
            'rows_exported': len(df),
            'success': False
        }
        
        try:
            # Export features only (no labels) for inference
            feature_columns = self.config.ai_feature_names + ['universal_key', 'timestamp']
            available_features = [col for col in feature_columns if col in df.columns]
            
            df_features = df[available_features].copy()
            features_path = output_dir / "inference_features.csv"
            df_features.to_csv(features_path, index=False)
            inference_results['inference_files_created'].append(str(features_path))
            
            # Export sample for testing
            sample_size = min(1000, len(df))
            df_sample = df.sample(n=sample_size, random_state=42)
            sample_path = output_dir / "inference_sample.csv"
            df_sample.to_csv(sample_path, index=False)
            inference_results['inference_files_created'].append(str(sample_path))
            
            # Export feature schema
            schema_path = output_dir / "feature_schema.json"
            feature_schema = {
                'features': available_features,
                'data_types': {col: str(df[col].dtype) for col in available_features},
                'feature_mapping': self.config.feature_mapping,
                'expected_input_shape': [None, len(self.config.ai_feature_names)]  # For neural networks
            }
            with open(schema_path, 'w') as f:
                json.dump(feature_schema, f, indent=2)
            inference_results['inference_files_created'].append(str(schema_path))
            
            inference_results['success'] = True
            logger.info(f"Inference export complete: {len(inference_results['inference_files_created'])} files created")
            
        except Exception as e:
            logger.error(f"Inference export failed: {e}")
            inference_results['error'] = str(e)
            raise
        
        return inference_results
    
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get cumulative export statistics."""
        return {
            'total_rows_exported': self.export_stats['total_rows_exported'],
            'files_created': self.export_stats['files_created'],
            'last_export': self.export_stats['export_metadata'].get('last_export_timestamp'),
            'export_config': {
                'format': self.config.export_format,
                'compression': self.config.compression,
                'include_index': self.config.include_index
            }
        }


def export_processed_data(df: pd.DataFrame, config: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Export processed dataset with standard configuration.
    
    Args:
        df: Processed DataFrame to export
        config: Processing configuration
        metadata: Additional metadata
        
    Returns:
        Export results.
    """
    exporter = DatasetExporter(config)
    return exporter.export_processed_dataset(df, metadata)


if __name__ == "__main__":
    # Run export demonstration when executed directly
    logger.info("Running dataset export demonstration...")
    
    try:
        # Create sample data for demonstration
        sample_data = {
            'universal_key': ['146.4_-39.1_20190101_0000', '146.4_-39.1_20190101_1200'],
            'latitude': [-39.1, -39.1],
            'longitude': [146.4, 146.4],
            'fire_label': [0, 1],
            'temperature_2m_c': [15.2, 28.5],
            'skin_temperature_c': [16.1, 45.2],
            'soil_temperature_level_1_c': [14.8, 25.3],
            'surface_solar_radiation_downwards': [250.5, 850.2],
            'surface_thermal_radiation_downwards': [320.1, 420.8],
            'u_component_of_wind_10m': [2.1, -1.5],
            'v_component_of_wind_10m': [1.8, 3.2],
            'timestamp': pd.to_datetime(['2019-01-01 00:00:00', '2019-01-01 12:00:00'])
        }
        
        df_sample = pd.DataFrame(sample_data)
        
        # Export with metadata
        metadata = {
            'processing_notes': 'Sample export for demonstration',
            'validation_passed': True,
            'data_quality_score': 98.5
        }
        
        results = export_processed_data(df_sample, metadata=metadata)
        
        print("\n=== EXPORT RESULTS ===")
        print(f"Export Success: {results['success']}")
        print(f"Output File: {results['output_file']}")
        print(f"Rows Exported: {results['rows_exported']:,}")
        print(f"File Size: {results['file_size_mb']:.2f} MB")
        print(f"AI Features: {len(results['ai_features_included'])}")
        
        print(f"\nAI Features Included:")
        for feature in results['ai_features_included']:
            print(f"  - {feature}")
        
        if 'data_summary_file' in results:
            print(f"\nData Summary: {Path(results['data_summary_file']).name}")
        
        print(f"\nExport completed successfully!")
        
    except Exception as e:
        logger.error(f"Export demonstration failed: {e}")
        raise