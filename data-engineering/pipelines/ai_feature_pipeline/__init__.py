"""
AI Feature Pipeline for FireFusion

Data engineering pipeline that prepares and feeds environmental data 
into the AI modelling workflow for the FireFusion project.

This package provides:
- Chunked ingestion of large datasets
- Comprehensive data validation
- AI-ready preprocessing
- Export functionality
- Utility functions and configuration management

Usage:
    from data_engineering.pipelines.ai_feature_pipeline import AIFeaturePipeline
    
    pipeline = AIFeaturePipeline()
    results = pipeline.run_full_pipeline()
"""

__version__ = "1.0.0"
__author__ = "FireFusion Data Engineering Team"

from .main import AIFeaturePipeline
from .config.processing_config import DEFAULT_CONFIG, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG

__all__ = [
    "AIFeaturePipeline",
    "DEFAULT_CONFIG", 
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG"
]