# FireFusion Master Dataset Schema Notes

## Dataset Overview
- **File**: `FireFusion_Master_Dataset.csv`
- **Size**: 2.2GB
- **Records**: Large-scale environmental and fire data
- **Purpose**: AI model training input data

## Schema Documentation

### Column Analysis (18 total columns)

#### 1. **system:index** (object)
- **Purpose**: Internal indexing system
- **Format**: String-based identifier
- **Example**: "0_0", "0_1", etc.

#### 2. **fire_label** (int64)
- **Purpose**: Binary fire presence indicator
- **Values**: 0 (no fire), 1 (fire present)
- **Critical**: Target variable for AI models

#### 3. **fire_temp_raw** (int64)
- **Purpose**: Raw fire temperature readings
- **Units**: Raw satellite values
- **Processing**: May require conversion to Celsius

#### 4. **latitude** (float64)
- **Purpose**: Spatial coordinate (Y-axis)
- **Range**: Should be [-90, 90] (Victoria region: ~ -37 to -39)
- **Validation**: Critical for spatial integrity

#### 5. **longitude** (float64)
- **Purpose**: Spatial coordinate (X-axis)
- **Range**: Should be [-180, 180] (Victoria region: ~ 141 to 150)
- **Validation**: Critical for spatial integrity

#### 6. **skin_temp_c** (float64)
- **Purpose**: Surface skin temperature
- **Units**: Celsius (already converted)
- **AI Feature**: Used in TCN model

#### 7. **soil_moist_root** (float64)
- **Purpose**: Root zone soil moisture
- **Units**: Volumetric water content
- **AI Feature**: Environmental moisture indicator

#### 8. **soil_moist_surf** (float64)
- **Purpose**: Surface soil moisture
- **Units**: Volumetric water content
- **AI Feature**: Surface fuel dryness indicator

#### 9. **soil_temp_c** (float64)
- **Purpose**: Soil temperature
- **Units**: Celsius
- **AI Feature**: Ground thermal conditions

#### 10. **stable_grid_id** (object)
- **Purpose**: Stable grid cell identifier
- **Format**: String-based grid reference
- **AI Feature**: Spatial grouping and indexing

#### 11. **surface_solar_radiation_downwards** (float64)
- **Purpose**: Incoming solar radiation
- **Units**: W/m²
- **AI Feature**: Used in TCN model

#### 12. **surface_thermal_radiation_downwards** (float64)
- **Purpose**: Incoming thermal radiation
- **Units**: W/m²
- **AI Feature**: Used in TCN model

#### 13. **temp_2m_c** (float64)
- **Purpose**: Air temperature at 2 meters
- **Units**: Celsius
- **AI Feature**: Used in TCN model

#### 14. **total_precip_mm** (float64)
- **Purpose**: Total precipitation
- **Units**: Millimeters
- **AI Feature**: Moisture availability

#### 15. **u_component_of_wind_10m** (float64)
- **Purpose**: East-west wind component
- **Units**: m/s
- **AI Feature**: Used in TCN model

#### 16. **universal_key** (object)
- **Purpose**: Composite spatiotemporal identifier
- **Format**: "{lon}_{lat}_{timestamp}"
- **AI Feature**: Primary record identifier

#### 17. **v_component_of_wind_10m** (float64)
- **Purpose**: North-south wind component
- **Units**: m/s
- **AI Feature**: Used in TCN model

#### 18. **.geo** (object)
- **Purpose**: GeoJSON geometry data
- **Format**: JSON string
- **Processing**: May be excluded from AI features

## AI Model Feature Mapping

### Features Used by TCN Model
From `ai-modelling/src/training/tcn_train_classifier.py`:
```python
FEATURES = [
    'temperature_2m_c',           # temp_2m_c
    'skin_temperature_c',         # skin_temp_c
    'soil_temperature_level_1_c', # soil_temp_c
    'surface_solar_radiation_downwards', # surface_solar_radiation_downwards
    'surface_thermal_radiation_downwards', # surface_thermal_radiation_downwards
    'u_component_of_wind_10m',   # u_component_of_wind_10m
    'v_component_of_wind_10m',   # v_component_of_wind_10m
]
```

### Feature Name Mappings
| AI Model Name | Master Dataset Name | Status |
|---------------|-------------------|---------|
| temperature_2m_c | temp_2m_c | Direct match |
| skin_temperature_c | skin_temp_c | Direct match |
| soil_temperature_level_1_c | soil_temp_c | Direct match |
| surface_solar_radiation_downwards | surface_solar_radiation_downwards | Direct match |
| surface_thermal_radiation_downwards | surface_thermal_radiation_downwards | Direct match |
| u_component_of_wind_10m | u_component_of_wind_10m | Direct match |
| v_component_of_wind_10m | v_component_of_wind_10m | Direct match |

## Data Quality Considerations

### Critical Validation Points
1. **Coordinate Validation**: Latitude/longitude ranges
2. **Missing Values**: Environmental features should not be null
3. **Duplicate Detection**: Based on universal_key or spatial-temporal combos
4. **Temporal Consistency**: Proper timestamp extraction from universal_key
5. **Feature Ranges**: Realistic values for all environmental variables

### Null-Sensitive Fields
- All environmental features (critical for AI model)
- Spatial coordinates (latitude, longitude)
- Fire labels (target variable)

### Processing Requirements
1. **Chunked Reading**: Essential for 2.2GB file
2. **Column Standardization**: Map to AI model expected names
3. **Type Validation**: Ensure proper data types
4. **Spatial Validation**: Victoria region bounds checking
5. **Export Optimization**: AI-ready CSV output

## Temporal Information
- **Timestamp Source**: Embedded in universal_key
- **Format**: "{lon}_{lat}_{timestamp}"
- **Extraction**: Parse timestamp component for sequence generation
- **Resolution**: Appears to be consistent (likely 12-hourly based on AI model)

## Spatial Information
- **Region**: Victoria, Australia
- **Grid System**: Stable 5km grid cells
- **Coordinates**: Decimal degrees
- **Coverage**: Complete Victorian region