# Victorian Suburbs Latitude and Longitude Dataset

Document contributor: *Thai Ha NGUYEN*

Planner Task: [Link to MS Planner](https://planner.cloud.microsoft/webui/v1/plan/H6UJiW7Qd0-pqy0lPXGgZ8gADBxI/view/board/task/Spgu91DbVkagDM7dkRDKD8gANlhg?tid=d02378ec-1688-46d5-8540-1c28b5f470f6)

## Source Information

- Source: Wildlife Victoria
- Provider: Victorian Government / Wildlife Victoria
- URL: https://www.wildlife.vic.gov.au/injured-native-wildlife/media/files/iwt-suburbs-latlng
- Date collected: 2026-05-03
- Collected by: **Thai Ha NGUYEN**
- Refresh frequency: Static / irregular update
- File format: JSON / API-style structured data
- Number of rows: 3,540
- Number of columns: 6

## Description

This dataset contains suburb-level location information for Victoria, including latitude, longitude, suburb name, postcode, state, and electorate rating classification.

For the FireFusion project, this dataset is useful as a suburb reference dataset. It can support location-based matching, spatial lookup, weather API requests by suburb coordinates, and mapping suburb-level information to the project `location_registry` table.

The dataset can also help the Data Engineering stream connect real-world suburb names and postcodes with latitude and longitude values before aligning them with the project’s 1km x 1km grid system.

## Variables

| Column Name | Description | Type | Unit/Range | Null Allowed | Notes |
|-------------|-------------|------|------------|--------------|-------|
| `latitude` | Latitude coordinate of the suburb or postcode area | Float | Decimal degrees, expected within Victoria latitude range | No | Used for spatial matching with `location_registry` |
| `longitude` | Longitude coordinate of the suburb or postcode area | Float | Decimal degrees, expected within Victoria longitude range | No | Used for spatial matching with `location_registry` |
| `electoraterating` | Electorate or regional classification supplied by the source | String | Example: `Inner Metropolitan` | Yes | Some records contain blank values |
| `suburb` | Name of the suburb or locality | String | Uppercase text | No | Example: `MELBOURNE`, `SOUTHBANK` |
| `postcode` | Australian postcode for the suburb or locality | String | 4-digit postcode | No | Stored as string to preserve leading zeros if needed |
| `state` | Australian state abbreviation | String | Expected value: `VIC` | No | All records are expected to be in Victoria |

## Data Quality Notes

- The dataset contains 3,540 rows and 6 columns.
- Some records have a blank `electoraterating` value.
- Suburb names are stored in uppercase format.
- Some postcodes may appear multiple times because one postcode can contain multiple suburbs or locality names.
- Some suburbs may appear more than once if they are linked to different postcode records or locality variations.
- Latitude and longitude values should be validated to confirm they fall within the expected geographic boundary of Victoria.
- The `postcode` field should be treated as a string, not an integer.
- The `state` column is expected to contain only `VIC`.
- Duplicate coordinate pairs may exist for closely related locality names.

## Transformations Applied

- Column names are already in lowercase and mostly compatible with project naming standards.
- `postcode` should be kept as a string.
- Blank `electoraterating` values should be converted to `NULL` during processing.
- Suburb names may be standardised using title case if required for display purposes, but the original source value should be preserved or documented.
- Latitude and longitude should be converted to numeric float values.
- Records should be checked for missing coordinates before loading.
- Each suburb coordinate should be mapped to the nearest `location_id` in the FireFusion `location_registry` table.

## Target Mapping

- Target table: `suburb_reference` or staging table before mapping to `location_registry`

| Source Column | Target Column | Notes |
|---------------|---------------|-------|
| `latitude` | `suburb_latitude` | Original suburb latitude from source |
| `longitude` | `suburb_longitude` | Original suburb longitude from source |
| `electoraterating` | `electorate_rating` | Rename for readability and snake_case consistency |
| `suburb` | `suburb_name` | Standard suburb/locality name |
| `postcode` | `postcode` | Store as string |
| `state` | `state` | Expected value: `VIC` |
| Derived | `location_id` | Matched from nearest grid point in `location_registry` |

## Suggested Target Schema

```sql
CREATE TABLE suburb_reference (
    suburb_reference_id SERIAL PRIMARY KEY,
    suburb_name VARCHAR(150) NOT NULL,
    postcode VARCHAR(10) NOT NULL,
    state VARCHAR(10) NOT NULL,
    electorate_rating VARCHAR(100),
    suburb_latitude DOUBLE PRECISION NOT NULL,
    suburb_longitude DOUBLE PRECISION NOT NULL,
    location_id INTEGER,
    source_name VARCHAR(150),
    source_url TEXT,
    collected_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_suburb_location
        FOREIGN KEY (location_id)
        REFERENCES location_registry(location_id)
);
````

## Primary Key / Unique Row Logic

Recommended unique logic:

```text
suburb_name + postcode + state + suburb_latitude + suburb_longitude
```

This is recommended because suburb names and postcodes may not be unique by themselves.


## FireFusion Usage

This dataset can be used for:

* suburb-level location lookup
* weather API requests using suburb coordinates
* mapping suburbs to the FireFusion 1km x 1km grid
* joining postcode-based datasets with spatial data
* supporting frontend suburb search or filtering
* preparing location-based inputs for AI modelling and backend services

## Assumptions and Limitations

* Coordinates are assumed to represent suburb or postcode-level approximate locations, not exact boundaries.
* The dataset does not provide polygon boundaries for suburbs.
* The dataset may not include every locality or updated postcode change.
* `electoraterating` is source-defined and may need further explanation from the provider.
* This dataset should not be used as a high-precision geospatial boundary dataset.
* For accurate suburb boundary analysis, an official suburb boundary shapefile or GeoJSON dataset should be used.
