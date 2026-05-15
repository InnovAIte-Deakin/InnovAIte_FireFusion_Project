# AI Feature Pipeline

## Overview
Data engineering pipeline that prepares and feeds environmental data into the AI modelling workflow for the FireFusion project.

## Purpose
- Process the 2.2GB FireFusion_Master_Dataset.csv
- Validate environmental features for AI model consumption
- Ensure consistent preprocessing and data quality
- Generate AI-ready outputs for training/inference workflows

## Input Dataset
- **Source**: `FireFusion_Master_Dataset.csv` (2.2GB)
- **Location**: Parent directory `firefusion/`
- **Schema**: 18 columns with environmental features and fire labels
- **Spatial Coverage**: Victoria, Australia (5km grid)
- **Temporal Coverage**: Multi-year environmental time series

## Pipeline Structure
```
ai_feature_pipeline/
├── ingestion/          # Chunked dataset loading
├── validation/         # Data quality checks
├── preprocessing/     # Cleaning and standardization
├── export/           # AI-ready outputs
├── utils/            # Shared helper functions
├── config/           # Processing configurations
├── logs/             # Processing logs and metadata
└── README.md         # This file
```

## Processing Workflow

### 1. Ingestion
- Safe chunked reading of 2.2GB dataset
- Memory-efficient processing (100,000 rows per chunk)
- Progress tracking and error handling

### 2. Validation
- **Schema Validation**: Required columns and data types
- **Spatial Validation**: Latitude/longitude range checks
- **Temporal Validation**: Timestamp consistency
- **Quality Validation**: Missing values, duplicates, outliers

### 3. Preprocessing
- Column name standardization for AI model compatibility
- Temperature unit conversions (if needed)
- Missing value handling strategies
- Duplicate removal and record consistency

### 4. Export
- **Primary Output**: `processed_master_dataset.csv`
- **Schema Alignment**: Matches AI model expected feature names
- **Metadata**: Processing logs, row counts, quality metrics
- **Future**: Database export options (PostgreSQL, Supabase)

## AI Model Integration

### Target Features
The pipeline outputs data ready for the TCN classifier model:
```python
FEATURES = [
    'temperature_2m_c',
    'skin_temperature_c', 
    'soil_temperature_level_1_c',
    'surface_solar_radiation_downwards',
    'surface_thermal_radiation_downwards',
    'u_component_of_wind_10m',
    'v_component_of_wind_10m',
]
```

### Schema Mapping
| Master Dataset | AI Model Expected | Status |
|---------------|------------------|---------|
| temp_2m_c | temperature_2m_c | Mapped |
| skin_temp_c | skin_temperature_c | Mapped |
| soil_temp_c | soil_temperature_level_1_c | Mapped |
| surface_solar_radiation_downwards | surface_solar_radiation_downwards | Direct |
| surface_thermal_radiation_downwards | surface_thermal_radiation_downwards | Direct |
| u_component_of_wind_10m | u_component_of_wind_10m | Direct |
| v_component_of_wind_10m | v_component_of_wind_10m | Direct |

## Validation Rules

### Spatial Validation
- Latitude: [-90, 90] (Victoria: -37 to -39)
- Longitude: [-180, 180] (Victoria: 141 to 150)

### Data Quality
- Environmental features: No null values allowed
- Fire labels: Binary values (0, 1) only
- Coordinates: Valid decimal degrees
- Timestamps: Consistent temporal resolution

### Consistency Checks
- Duplicate detection based on universal_key
- Range validation for all environmental variables
- Temporal sequence integrity

## Configuration

### Processing Parameters
```python
CHUNKSIZE = 100000          # Rows per processing chunk
MAX_WORKERS = 4             # Parallel processing workers
VALIDATION_STRICT = True    # Strict validation mode
EXPORT_FORMAT = 'csv'       # Output format
```

### Paths
```python
INPUT_PATH = '../../../FireFusion_Master_Dataset.csv'
OUTPUT_PATH = 'processed_master_dataset.csv'
LOG_PATH = 'logs/'
CONFIG_PATH = 'config/'
```

## Usage

### Basic Processing
```bash
cd data-engineering/pipelines/ai_feature_pipeline
python main.py
```

### Custom Configuration
```python
from config.processing_config import ProcessingConfig
config = ProcessingConfig(chunksize=50000, validation_strict=False)
```

### Validation Only
```python
from validation.validate_dataset import validate_master_dataset
validation_report = validate_master_dataset('FireFusion_Master_Dataset.csv')
```

## Outputs

### Primary Dataset
- **File**: `processed_master_dataset.csv`
- **Schema**: AI-ready feature columns
- **Quality**: Validated and cleaned records
- **Metadata**: Processing statistics attached

### Validation Reports
- **File**: `logs/validation_report.json`
- **Content**: Row counts, error statistics, quality metrics
- **Format**: Structured JSON for downstream processing

### Processing Logs
- **File**: `logs/processing.log`
- **Content**: Detailed execution logs
- **Level**: INFO, WARNING, ERROR categorization

## Integration Points

### AI Modelling Team
- Direct consumption of processed dataset
- Consistent schema with training pipelines
- Validated feature quality for model performance

### Data Engineering Team
- Reusable validation utilities
- Established DE architecture patterns
- Integration with existing pipeline infrastructure

### Future Extensions
- Incremental processing for new data
- Database integration (Supabase)
- Automated scheduling (12-hour cycles)
- Partitioned export by time periods

## Dependencies
- pandas >= 1.3.0
- numpy >= 1.21.0
- pathlib (built-in)
- logging (built-in)
- json (built-in)

## Performance Considerations
- **Memory**: Chunked processing prevents OOM errors
- **Speed**: Parallel validation where possible
- **Storage**: Efficient CSV export with compression options
- **Monitoring**: Progress tracking for large datasets