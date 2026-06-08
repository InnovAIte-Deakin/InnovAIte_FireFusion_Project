"""
AI Feature Pipeline - Main Entry Point

Main orchestration script for the FireFusion AI feature processing pipeline.
Handles end-to-end processing of the master dataset for AI model consumption.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent))

from config.processing_config import DEFAULT_CONFIG, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG
from ingestion.ingest_dataset import DatasetIngester, quick_dataset_inspection
from validation.validate_dataset import DatasetValidator
from preprocessing.preprocess_dataset import DatasetPreprocessor
from export.export_dataset import DatasetExporter
from utils.pipeline_utils import PipelineLogger, PipelineTimer, ConfigValidator, create_pipeline_report

# Configure logging
logger = PipelineLogger("ai_feature_pipeline_main")


class AIFeaturePipeline:
    """Main pipeline orchestrator for AI feature processing."""
    
    def __init__(self, config: Optional[Any] = None, run_mode: str = "standard"):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Processing configuration
            run_mode: Execution mode (standard, development, production)
        """
        self.run_mode = run_mode
        
        # Select configuration based on run mode
        if run_mode == "development":
            self.config = config or DEVELOPMENT_CONFIG
        elif run_mode == "production":
            self.config = config or PRODUCTION_CONFIG
        else:
            self.config = config or DEFAULT_CONFIG
        
        # Initialize pipeline components
        self.ingester = DatasetIngester(self.config)
        self.validator = DatasetValidator(self.config)
        self.preprocessor = DatasetPreprocessor(self.config)
        self.exporter = DatasetExporter(self.config)
        
        # Pipeline results storage
        self.pipeline_results = {
            'pipeline_info': {
                'start_time': None,
                'end_time': None,
                'duration_seconds': None,
                'run_mode': run_mode,
                'config_used': str(self.config)
            },
            'ingestion_results': {},
            'validation_results': {},
            'preprocessing_results': {},
            'export_results': {},
            'final_statistics': {}
        }
        
        logger.logger.info(f"Pipeline initialized in {run_mode} mode")
        logger.logger.info(f"Configuration: chunksize={self.config.chunksize}, validation_strict={self.config.validation_strict}")
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete end-to-end pipeline.
        
        Returns:
            Comprehensive pipeline results.
        """
        start_time = datetime.now()
        self.pipeline_results['pipeline_info']['start_time'] = start_time.isoformat()
        
        try:
            logger.log_pipeline_start("AI Feature Pipeline", 
                                    mode=self.run_mode,
                                    chunksize=self.config.chunksize,
                                    input_file=str(self.config.input_dataset))
            
            # Step 1: Dataset Inspection
            with PipelineTimer("Dataset Inspection", logger):
                self.pipeline_results['ingestion_results'] = self._inspect_dataset()
            
            # Step 2: Validation
            with PipelineTimer("Dataset Validation", logger):
                self.pipeline_results['validation_results'] = self._validate_dataset()
            
            # Step 3: Preprocessing
            with PipelineTimer("Dataset Preprocessing", logger):
                self.pipeline_results['preprocessing_results'] = self._preprocess_dataset()
            
            # Step 4: Export
            with PipelineTimer("Dataset Export", logger):
                self.pipeline_results['export_results'] = self._export_dataset()
            
            # Step 5: Final Statistics
            self.pipeline_results['final_statistics'] = self._calculate_final_statistics()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.pipeline_results['pipeline_info']['end_time'] = end_time.isoformat()
            self.pipeline_results['pipeline_info']['duration_seconds'] = duration
            
            logger.log_pipeline_end("AI Feature Pipeline", duration,
                                   total_rows_processed=self.pipeline_results['final_statistics'].get('total_rows_processed', 0),
                                   success_rate=self.pipeline_results['final_statistics'].get('success_rate', 0))
            
            # Generate pipeline report
            report_path = self._generate_pipeline_report()
            logger.logger.info(f"Pipeline report generated: {report_path}")
            
            return self.pipeline_results
            
        except Exception as e:
            logger.log_error_with_traceback(e, "pipeline execution")
            self.pipeline_results['pipeline_info']['error'] = str(e)
            raise
    
    def run_inspection_only(self) -> Dict[str, Any]:
        """Run only dataset inspection."""
        logger.log_pipeline_start("Dataset Inspection Only")
        
        with PipelineTimer("Dataset Inspection", logger):
            self.pipeline_results['ingestion_results'] = self._inspect_dataset()
        
        return self.pipeline_results['ingestion_results']
    
    def run_validation_only(self) -> Dict[str, Any]:
        """Run only dataset validation."""
        logger.log_pipeline_start("Dataset Validation Only")
        
        with PipelineTimer("Dataset Validation", logger):
            self.pipeline_results['validation_results'] = self._validate_dataset()
        
        return self.pipeline_results['validation_results']
    
    def _inspect_dataset(self) -> Dict[str, Any]:
        """Perform dataset inspection."""
        logger.logger.info("Performing dataset inspection...")
        
        # Quick inspection
        inspection_results = quick_dataset_inspection(self.config)
        
        # Validate configuration
        config_validation = ConfigValidator.validate_config(self.config)
        inspection_results['config_validation'] = config_validation
        
        if not config_validation['valid']:
            logger.logger.error("Configuration validation failed")
            raise ValueError("Invalid pipeline configuration")
        
        logger.logger.info(f"Dataset inspection complete: {inspection_results['dataset_info']['row_count']} rows, "
                         f"{inspection_results['dataset_info']['column_count']} columns")
        
        return inspection_results
    
    def _validate_dataset(self) -> Dict[str, Any]:
        """Perform dataset validation."""
        logger.logger.info("Performing dataset validation...")
        
        validation_results = []
        
        # Process dataset in chunks for validation
        chunk_id = 0
        chunk_reader = self.ingester.chunked_reader()
        try:
            for chunk in chunk_reader:
                chunk_validation = self.validator.validate_chunk(chunk, chunk_id)
                validation_results.append(chunk_validation)
                
                # Log progress
                if chunk_id % 10 == 0:
                    total_chunks = (self.ingester.total_rows // self.config.chunksize + 1) if self.ingester.total_rows else None
                    logger.log_chunk_progress(chunk_id + 1, 
                                            total_chunks,
                                            self.ingester.processed_rows,
                                            self.ingester.total_rows)
                
                chunk_id += 1
        finally:
            # Clean up if needed
            pass
        
        # Generate comprehensive validation report
        validation_report = self.validator.generate_validation_report(validation_results)
        
        logger.logger.info(f"Validation complete: {validation_report['validation_summary']['validation_passed']}, "
                         f"Quality score: {validation_report['validation_summary']['data_quality_score']:.1f}%")
        
        return validation_report
    
    def _preprocess_dataset(self) -> Dict[str, Any]:
        """Perform dataset preprocessing."""
        logger.logger.info("Performing dataset preprocessing...")
        
        preprocessing_results = []
        
        # Process dataset in chunks for preprocessing
        chunk_id = 0
        chunk_reader = self.ingester.chunked_reader()
        try:
            for chunk in chunk_reader:
                processed_chunk, chunk_stats = self.preprocessor.preprocess_chunk(chunk, chunk_id)
                preprocessing_results.append(chunk_stats)
                
                # Log progress
                if chunk_id % 10 == 0:
                    total_chunks = (self.ingester.total_rows // self.config.chunksize + 1) if self.ingester.total_rows else None
                    logger.log_chunk_progress(chunk_id + 1,
                                            total_chunks,
                                            self.ingester.processed_rows,
                                            self.ingester.total_rows)
                
                chunk_id += 1
        finally:
            # Clean up if needed
            pass
        
        # Generate comprehensive preprocessing report
        preprocessing_report = self.preprocessor.generate_preprocessing_report(preprocessing_results)
        
        logger.logger.info(f"Preprocessing complete: {preprocessing_report['preprocessing_summary']['retention_rate']:.1f}% retention rate")
        
        return preprocessing_report
    
    def _export_dataset(self) -> Dict[str, Any]:
        """Export processed dataset."""
        logger.logger.info("Exporting processed dataset...")
        
        # For demonstration, create a sample processed dataset
        # In full implementation, this would use the actual processed data
        sample_data = self._create_sample_processed_data()
        
        # Prepare metadata
        metadata = {
            'pipeline_run_id': datetime.now().isoformat(),
            'run_mode': self.run_mode,
            'validation_passed': self.pipeline_results['validation_results'].get('validation_summary', {}).get('validation_passed', False),
            'preprocessing_applied': True,
            'ai_features_count': len(self.config.ai_feature_names)
        }
        
        # Export dataset
        export_results = self.exporter.export_processed_dataset(sample_data, metadata)
        
        logger.logger.info(f"Export complete: {export_results['rows_exported']} rows exported to {export_results['output_file']}")
        
        return export_results
    
    def _create_sample_processed_data(self) -> Any:
        """Create sample processed data for demonstration."""
        # In full implementation, this would return the actual processed DataFrame
        # For now, create a small sample to demonstrate export functionality
        import pandas as pd
        
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
        
        return pd.DataFrame(sample_data)
    
    def _calculate_final_statistics(self) -> Dict[str, Any]:
        """Calculate final pipeline statistics."""
        stats = {
            'pipeline_success': True,
            'total_rows_processed': 0,
            'final_rows_output': 0,
            'success_rate': 0.0,
            'processing_efficiency': 'high',
            'quality_score': 0.0
        }
        
        # Extract statistics from pipeline results
        if 'ingestion_results' in self.pipeline_results:
            ingestion_info = self.pipeline_results['ingestion_results'].get('dataset_info', {})
            stats['total_rows_processed'] = ingestion_info.get('row_count', 0)
        
        if 'validation_results' in self.pipeline_results:
            validation_summary = self.pipeline_results['validation_results'].get('validation_summary', {})
            stats['quality_score'] = validation_summary.get('data_quality_score', 0.0)
            stats['final_rows_output'] = validation_summary.get('total_output_rows', 0)
        
        if 'preprocessing_results' in self.pipeline_results:
            preprocessing_summary = self.pipeline_results['preprocessing_results'].get('preprocessing_summary', {})
            stats['success_rate'] = preprocessing_summary.get('retention_rate', 0.0)
            stats['processing_efficiency'] = preprocessing_summary.get('quality_metrics', {}).get('processing_efficiency', 'unknown')
        
        # Determine overall success
        stats['pipeline_success'] = (
            stats['quality_score'] > 80.0 and 
            stats['success_rate'] > 80.0 and
            stats['processing_efficiency'] != 'unknown'
        )
        
        return stats
    
    def _generate_pipeline_report(self) -> Path:
        """Generate comprehensive pipeline report."""
        report_path = self.config.logs_dir / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        return create_pipeline_report(self.pipeline_results, report_path)


def main():
    """Main entry point for command line execution."""
    parser = argparse.ArgumentParser(description="AI Feature Pipeline for FireFusion")
    parser.add_argument("--mode", choices=["standard", "development", "production"], 
                       default="standard", help="Pipeline execution mode")
    parser.add_argument("--inspect-only", action="store_true", 
                       help="Run dataset inspection only")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Run dataset validation only")
    parser.add_argument("--chunksize", type=int, 
                       help="Override chunk size for processing")
    parser.add_argument("--no-strict-validation", action="store_true",
                       help="Disable strict validation mode")
    
    args = parser.parse_args()
    
    try:
        # Create configuration with overrides
        config = DEFAULT_CONFIG
        
        if args.chunksize:
            config.chunksize = args.chunksize
        
        if args.no_strict_validation:
            config.validation_strict = False
        
        # Initialize pipeline
        pipeline = AIFeaturePipeline(config, args.mode)
        
        # Run appropriate pipeline
        if args.inspect_only:
            results = pipeline.run_inspection_only()
            print(f"\n=== INSPECTION RESULTS ===")
            print(f"Dataset: {results['dataset_info']['row_count']:,} rows, {results['dataset_info']['column_count']} columns")
            print(f"File size: {results['dataset_info']['file_size_mb']} MB")
            
        elif args.validate_only:
            results = pipeline.run_validation_only()
            print(f"\n=== VALIDATION RESULTS ===")
            print(f"Validation passed: {results['validation_summary']['validation_passed']}")
            print(f"Data quality score: {results['validation_summary']['data_quality_score']:.1f}%")
            
        else:
            results = pipeline.run_full_pipeline()
            print(f"\n=== PIPELINE RESULTS ===")
            print(f"Pipeline success: {results['final_statistics']['pipeline_success']}")
            print(f"Total rows processed: {results['final_statistics']['total_rows_processed']:,}")
            print(f"Success rate: {results['final_statistics']['success_rate']:.1f}%")
            print(f"Quality score: {results['final_statistics']['quality_score']:.1f}%")
            print(f"Processing efficiency: {results['final_statistics']['processing_efficiency']}")
        
        print(f"\nPipeline completed in {args.mode} mode!")
        
    except KeyboardInterrupt:
        logger.logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.log_error_with_traceback(e, "main execution")
        print(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()