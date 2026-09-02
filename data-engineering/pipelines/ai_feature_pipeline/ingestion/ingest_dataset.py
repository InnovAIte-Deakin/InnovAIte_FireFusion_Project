"""
Dataset Ingestion Module for AI Feature Pipeline

Handles safe chunked reading of the 2.2GB FireFusion_Master_Dataset.csv
with memory-efficient processing and progress tracking.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
from contextlib import contextmanager

from config.processing_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(
    level=DEFAULT_CONFIG.log_level,
    format=DEFAULT_CONFIG.log_format
)
logger = logging.getLogger(__name__)


class DatasetIngester:
    """Handles chunked ingestion of large datasets with memory safety."""
    
    def __init__(self, config: Optional[Any] = None):
        """Initialize ingester with configuration."""
        self.config = config or DEFAULT_CONFIG
        self.total_rows = None
        self.processed_rows = 0
        self.current_chunk = 0
        
    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Get basic dataset information without loading full dataset.
        
        Returns:
            Dictionary with file size, row count, and column info.
        """
        dataset_path = self.config.input_dataset
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        # Get file size
        file_size_mb = dataset_path.stat().st_size / (1024 * 1024)
        
        # Quick row count using pandas (memory efficient)
        logger.info(f"Counting rows in {dataset_path.name}...")
        try:
            # Use pandas to count rows efficiently
            row_count = sum(1 for _ in pd.read_csv(dataset_path, chunksize=self.config.chunksize))
        except Exception as e:
            logger.error(f"Error counting rows: {e}")
            # Fallback: read first chunk to estimate
            sample_df = pd.read_csv(dataset_path, nrows=1000)
            estimated_rows = "Unknown (estimated from sample)"
            logger.warning("Using estimated row count")
            row_count = estimated_rows
        
        # Get column information from first chunk
        sample_df = pd.read_csv(dataset_path, nrows=1)
        columns = list(sample_df.columns)
        dtypes = sample_df.dtypes.to_dict()
        
        info = {
            'file_path': str(dataset_path),
            'file_size_mb': round(file_size_mb, 2),
            'row_count': row_count,
            'column_count': len(columns),
            'columns': columns,
            'data_types': {col: str(dtype) for col, dtype in dtypes.items()},
            'chunk_size': self.config.chunksize,
        }
        
        self.total_rows = row_count
        return info
    
    def chunked_reader(self):
        """
        Iterator for safe chunked dataset reading.
        
        Yields:
            DataFrame chunks for processing.
        """
        dataset_path = self.config.input_dataset
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        logger.info(f"Starting chunked reading of {dataset_path.name}")
        logger.info(f"Chunk size: {self.config.chunksize:,} rows")
        
        try:
            chunk_reader = pd.read_csv(
                dataset_path,
                chunksize=self.config.chunksize,
                low_memory=False
            )
            
            for chunk in chunk_reader:
                self.current_chunk += 1
                chunk_size = len(chunk)
                self.processed_rows += chunk_size
                
                # Log progress
                if self.current_chunk % 10 == 0 or self.current_chunk == 1:
                    if self.total_rows:
                        progress_pct = (self.processed_rows / self.total_rows * 100)
                        progress_str = f"{progress_pct:.1f}%"
                    else:
                        progress_str = "Unknown"
                    logger.info(f"Processed chunk {self.current_chunk}: {chunk_size:,} rows "
                              f"(total: {self.processed_rows:,}, {progress_str})")
                
                yield chunk
                
        except Exception as e:
            logger.error(f"Error reading chunk {self.current_chunk}: {e}")
            raise
        finally:
            logger.info(f"Completed reading {self.processed_rows:,} rows in {self.current_chunk} chunks")
    
    def read_sample(self, n_rows: int = 10) -> pd.DataFrame:
        """
        Read a small sample of the dataset for inspection.
        
        Args:
            n_rows: Number of rows to sample
            
        Returns:
            DataFrame with sample data.
        """
        dataset_path = self.config.input_dataset
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        
        logger.info(f"Reading sample of {n_rows} rows from {dataset_path.name}")
        
        try:
            sample_df = pd.read_csv(
                dataset_path,
                nrows=n_rows
            )
            logger.info(f"Successfully read sample: {sample_df.shape}")
            return sample_df
        except Exception as e:
            logger.error(f"Error reading sample: {e}")
            raise
    
    def validate_schema(self, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate dataset schema against expected configuration.
        
        Args:
            sample_df: Sample DataFrame for schema validation
            
        Returns:
            Validation results dictionary.
        """
        logger.info("Validating dataset schema...")
        
        results = {
            'expected_columns': self.config.required_columns,
            'actual_columns': list(sample_df.columns),
            'missing_columns': [],
            'extra_columns': [],
            'dtype_mismatches': [],
            'validation_passed': True
        }
        
        # Check for missing columns
        expected_set = set(self.config.required_columns)
        actual_set = set(sample_df.columns)
        
        results['missing_columns'] = list(expected_set - actual_set)
        results['extra_columns'] = list(actual_set - expected_set)
        
        # Check data types
        if hasattr(self.config, 'expected_dtypes') and self.config.expected_dtypes is not None:
            for col in self.config.required_columns:
                if col in sample_df.columns:
                    expected_dtype = self.config.expected_dtypes.get(col)
                    actual_dtype = str(sample_df[col].dtype)
                    
                    if expected_dtype and actual_dtype != expected_dtype:
                        results['dtype_mismatches'].append({
                            'column': col,
                            'expected': expected_dtype,
                            'actual': actual_dtype
                        })
        
        # Determine validation status
        if (results['missing_columns'] or 
            results['dtype_mismatches'] and self.config.validation_strict):
            results['validation_passed'] = False
            logger.warning("Schema validation failed")
        else:
            logger.info("Schema validation passed")
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics.
        
        Returns:
            Dictionary with processing progress information.
        """
        stats = {
            'total_rows': self.total_rows,
            'processed_rows': self.processed_rows,
            'current_chunk': self.current_chunk,
            'progress_percentage': (self.processed_rows / self.total_rows * 100) if self.total_rows else None,
            'chunk_size': self.config.chunksize,
            'estimated_chunks_remaining': ((self.total_rows - self.processed_rows) / self.config.chunksize) if self.total_rows else None
        }
        
        return stats


def ingest_dataset(config: Optional[Any] = None) -> DatasetIngester:
    """
    Factory function to create a dataset ingester.
    
    Args:
        config: Processing configuration (uses default if None)
        
    Returns:
        Configured DatasetIngester instance.
    """
    return DatasetIngester(config)


def quick_dataset_inspection(config: Optional[Any] = None) -> Dict[str, Any]:
    """
    Perform quick inspection of dataset without full processing.
    
    Args:
        config: Processing configuration
        
    Returns:
        Dictionary with dataset information and validation results.
    """
    ingester = ingest_dataset(config)
    
    # Get basic info
    info = ingester.get_dataset_info()
    
    # Read sample for validation
    sample_df = ingester.read_sample(n_rows=10)
    
    # Validate schema
    validation_results = ingester.validate_schema(sample_df)
    
    # Combine results
    inspection_results = {
        'dataset_info': info,
        'schema_validation': validation_results,
        'sample_data': {
            'shape': sample_df.shape,
            'columns': list(sample_df.columns),
            'first_rows': sample_df.head(3).to_dict('records') if len(sample_df) > 0 else []
        }
    }
    
    return inspection_results


if __name__ == "__main__":
    # Quick inspection when run directly
    logger.info("Running quick dataset inspection...")
    
    try:
        results = quick_dataset_inspection()
        
        print("\n=== DATASET INSPECTION RESULTS ===")
        print(f"File: {results['dataset_info']['file_path']}")
        print(f"Size: {results['dataset_info']['file_size_mb']} MB")
        print(f"Rows: {results['dataset_info']['row_count']}")
        print(f"Columns: {results['dataset_info']['column_count']}")
        
        print(f"\nSchema Validation: {'PASSED' if results['schema_validation']['validation_passed'] else 'FAILED'}")
        
        if results['schema_validation']['missing_columns']:
            print(f"Missing columns: {results['schema_validation']['missing_columns']}")
        
        if results['schema_validation']['extra_columns']:
            print(f"Extra columns: {results['schema_validation']['extra_columns']}")
        
        print("\nSample data preview:")
        for i, row in enumerate(results['sample_data']['first_rows'][:3]):
            print(f"Row {i+1}: {dict(list(row.items())[:5])}...")
            
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise
    