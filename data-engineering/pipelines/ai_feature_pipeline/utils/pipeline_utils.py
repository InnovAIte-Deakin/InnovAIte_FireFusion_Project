"""
Pipeline Utilities for AI Feature Pipeline

Shared utility functions for data processing, validation, and pipeline orchestration.
Includes logging, error handling, and common data operations.
"""

import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import traceback

from config.processing_config import DEFAULT_CONFIG


class PipelineLogger:
    """Enhanced logging for pipeline operations."""
    
    def __init__(self, name: str = "ai_feature_pipeline", config: Optional[Any] = None):
        """Initialize logger with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.logger = logging.getLogger(name)
        
        # Configure logger if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config.log_format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, self.config.log_level))
    
    def log_pipeline_start(self, pipeline_name: str, **kwargs):
        """Log pipeline start with parameters."""
        self.logger.info(f"Starting {pipeline_name}")
        for key, value in kwargs.items():
            self.logger.info(f"  {key}: {value}")
    
    def log_pipeline_end(self, pipeline_name: str, duration: float, **kwargs):
        """Log pipeline completion with statistics."""
        self.logger.info(f"Completed {pipeline_name} in {duration:.2f}s")
        for key, value in kwargs.items():
            self.logger.info(f"  {key}: {value}")
    
    def log_chunk_progress(self, chunk_id: int, total_chunks, rows_processed: int, total_rows):
        """Log progress for chunked operations."""
        if total_chunks and total_chunks > 0:
            progress_pct = (chunk_id / total_chunks * 100)
            chunk_str = f"{chunk_id}/{total_chunks} ({progress_pct:.1f}%)"
        else:
            chunk_str = f"{chunk_id} (unknown total)"
        
        if total_rows and total_rows > 0:
            row_progress_pct = (rows_processed / total_rows * 100)
            row_str = f"{rows_processed:,}/{total_rows:,} ({row_progress_pct:.1f}%)"
        else:
            row_str = f"{rows_processed:,}/unknown"
        
        self.logger.info(f"Chunk {chunk_str} - Rows {row_str}")
    
    def log_error_with_traceback(self, error: Exception, context: str = ""):
        """Log error with full traceback."""
        self.logger.error(f"Error in {context}: {str(error)}")
        self.logger.debug(traceback.format_exc())


class DataProfiler:
    """Profiles data for quality assessment and reporting."""
    
    @staticmethod
    def profile_dataframe(df: pd.DataFrame, include_correlations: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive data profile.
        
        Args:
            df: DataFrame to profile
            include_correlations: Whether to compute correlation matrix
            
        Returns:
            Data profile dictionary.
        """
        profile = {
            'basic_info': {
                'shape': df.shape,
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'column_count': len(df.columns),
                'row_count': len(df)
            },
            'column_profiles': {},
            'missing_values': {},
            'data_types': df.dtypes.to_dict(),
            'duplicate_rows': df.duplicated().sum()
        }
        
        # Profile each column
        for col in df.columns:
            col_profile = DataProfiler._profile_column(df[col])
            profile['column_profiles'][col] = col_profile
            profile['missing_values'][col] = int(df[col].isna().sum())
        
        # Add correlations if requested and numeric columns exist
        if include_correlations:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                try:
                    correlations = df[numeric_cols].corr()
                    profile['correlations'] = correlations.to_dict()
                except Exception as e:
                    profile['correlations'] = {'error': str(e)}
        
        return profile
    
    @staticmethod
    def _profile_column(series: pd.Series) -> Dict[str, Any]:
        """Profile a single column."""
        profile = {
            'dtype': str(series.dtype),
            'non_null_count': series.count(),
            'null_count': series.isna().sum(),
            'unique_count': series.nunique()
        }
        
        if pd.api.types.is_numeric_dtype(series):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                profile.update({
                    'mean': float(non_null_series.mean()),
                    'std': float(non_null_series.std()),
                    'min': float(non_null_series.min()),
                    'max': float(non_null_series.max()),
                    'median': float(non_null_series.median()),
                    'q25': float(non_null_series.quantile(0.25)),
                    'q75': float(non_null_series.quantile(0.75))
                })
        
        elif pd.api.types.is_datetime64_any_dtype(series):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                profile.update({
                    'min_date': non_null_series.min().isoformat(),
                    'max_date': non_null_series.max().isoformat(),
                    'date_range_days': (non_null_series.max() - non_null_series.min()).days
                })
        
        elif pd.api.types.is_object_dtype(series):
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                value_counts = non_null_series.value_counts()
                profile.update({
                    'most_common': value_counts.head(5).to_dict(),
                    'avg_length': non_null_series.astype(str).str.len().mean()
                })
        
        return profile


class MemoryManager:
    """Manages memory usage for large dataset processing."""
    
    @staticmethod
    def estimate_memory_usage(df_shape: Tuple[int, int], dtype_sizes: Dict[str, int]) -> float:
        """
        Estimate memory usage for a DataFrame.
        
        Args:
            df_shape: (rows, columns) tuple
            dtype_sizes: Dictionary mapping dtypes to bytes per value
            
        Returns:
            Estimated memory usage in MB.
        """
        rows, cols = df_shape
        total_bytes = rows * cols * 8  # Default to 8 bytes per value
        return total_bytes / (1024 * 1024)
    
    @staticmethod
    def optimize_chunksize(file_size_mb: float, available_memory_mb: float = 8000) -> int:
        """
        Calculate optimal chunksize based on file size and available memory.
        
        Args:
            file_size_mb: File size in MB
            available_memory_mb: Available memory in MB
            
        Returns:
            Recommended chunksize.
        """
        # Use 25% of available memory for processing
        safe_memory_mb = available_memory_mb * 0.25
        
        # Estimate rows per MB (rough approximation)
        rows_per_mb = 1000  # Conservative estimate
        
        # Calculate chunksize
        chunksize = int(safe_memory_mb * rows_per_mb)
        
        # Ensure reasonable bounds
        chunksize = max(1000, min(chunksize, 500000))
        
        return chunksize
    
    @staticmethod
    def monitor_memory_usage() -> Dict[str, float]:
        """Monitor current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return {
                'process_memory_mb': memory_info.rss / (1024 * 1024),
                'system_memory_percent': system_memory.percent,
                'available_memory_mb': system_memory.available / (1024 * 1024)
            }
        except ImportError:
            return {'error': 'psutil not available for memory monitoring'}


class PipelineTimer:
    """Context manager for timing pipeline operations."""
    
    def __init__(self, operation_name: str, logger: Optional[PipelineLogger] = None):
        self.operation_name = operation_name
        self.logger = logger or PipelineLogger()
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log_pipeline_start(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.log_pipeline_end(self.operation_name, duration, status="success")
        else:
            self.logger.log_pipeline_end(self.operation_name, duration, status="failed", error=str(exc_val))
    
    def get_duration(self) -> float:
        """Get operation duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class ConfigValidator:
    """Validates pipeline configuration."""
    
    @staticmethod
    def validate_config(config: Any) -> Dict[str, Any]:
        """
        Validate pipeline configuration.
        
        Args:
            config: Processing configuration
            
        Returns:
            Validation results.
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check paths
        path_checks = config.validate_paths()
        if not path_checks['input_dataset_exists']:
            results['errors'].append("Input dataset file does not exist")
            results['valid'] = False
        
        # Check chunksize
        if config.chunksize <= 0:
            results['errors'].append("Chunksize must be positive")
            results['valid'] = False
        elif config.chunksize > 1000000:
            results['warnings'].append("Large chunksize may cause memory issues")
            results['recommendations'].append("Consider reducing chunksize to < 1M rows")
        
        # Check feature mapping
        if not config.feature_mapping:
            results['errors'].append("Feature mapping cannot be empty")
            results['valid'] = False
        
        # Check required columns
        if not config.required_columns:
            results['errors'].append("Required columns list cannot be empty")
            results['valid'] = False
        
        # Check AI features
        if not config.ai_features:
            results['errors'].append("AI features list cannot be empty")
            results['valid'] = False
        
        return results


class FileHelper:
    """Helper functions for file operations."""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_file_write(data: Any, file_path: Union[str, Path], mode: str = 'w') -> bool:
        """
        Safely write data to file with error handling.
        
        Args:
            data: Data to write
            file_path: Output file path
            mode: Write mode
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, mode, encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))
            
            return True
        except Exception as e:
            logging.error(f"Failed to write {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive file information."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'error': 'File does not exist'}
        
        stat = file_path.stat()
        
        return {
            'name': file_path.name,
            'path': str(file_path.absolute()),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_file': file_path.is_file(),
            'extension': file_path.suffix
        }


def create_pipeline_report(pipeline_results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Create comprehensive pipeline report.
    
    Args:
        pipeline_results: Dictionary with all pipeline results
        output_path: Optional custom output path
        
    Returns:
        Path to generated report file.
    """
    if output_path is None:
        output_path = Path("pipeline_report.json")
    
    # Add metadata
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'pipeline_version': '1.0.0',
            'report_type': 'ai_feature_pipeline_summary'
        },
        'pipeline_results': pipeline_results
    }
    
    FileHelper.safe_file_write(report, output_path)
    return output_path


# Utility functions for common operations
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value for division by zero."""
    return numerator / denominator if denominator != 0 else default


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage with safe division."""
    return safe_divide(part * 100, total)


def format_number(num: Union[int, float], precision: int = 2) -> str:
    """Format number with appropriate units."""
    if isinstance(num, int) or num.is_integer():
        return f"{int(num):,}"
    else:
        return f"{num:.{precision}f}"


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates."""
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)


def extract_date_from_universal_key(universal_key: str) -> Optional[datetime]:
    """Extract datetime from universal_key string."""
    try:
        parts = str(universal_key).split('_')
        if len(parts) >= 3:
            timestamp_part = '_'.join(parts[2:])
            if len(timestamp_part) >= 8:
                year = int(timestamp_part[:4])
                month = int(timestamp_part[4:6])
                day = int(timestamp_part[6:8])
                hour = int(timestamp_part[9:11]) if len(timestamp_part) > 9 else 0
                return datetime(year, month, day, hour)
    except:
        pass
    return None


if __name__ == "__main__":
    # Demonstrate utilities when run directly
    logger = PipelineLogger()
    
    # Test timer
    with PipelineTimer("utility_test", logger):
        # Test data profiler
        sample_df = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5],
            'text_col': ['a', 'b', 'c', 'd', 'e'],
            'date_col': pd.date_range('2023-01-01', periods=5)
        })
        
        profile = DataProfiler.profile_dataframe(sample_df)
        logger.logger.info(f"Profiled sample data: {profile['basic_info']}")
        
        # Test memory manager
        memory_info = MemoryManager.monitor_memory_usage()
        logger.logger.info(f"Memory info: {memory_info}")
        
        # Test config validator
        config_validation = ConfigValidator.validate_config(DEFAULT_CONFIG)
        logger.logger.info(f"Config validation: {config_validation['valid']}")
    
    print("Utilities demonstration complete!")