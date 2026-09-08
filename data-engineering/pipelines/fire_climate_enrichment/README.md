# Fire Climate Enrichment

This pipeline enriches sample fire records with two climate signals:

1. Local weather data from the existing realtime weather pipeline
2. ENSO / ONI climate data from the NOAA CPC ENSO pipeline

## Inputs

- `sample_fires.csv`
- `realtime_weather_validated.csv`
- latest processed ENSO / ONI CSV

## Enriched fields

### Local weather
- `temperature_c`
- `wind_speed_kmh`
- `relative_humidity`

### ENSO
- `oni_anomaly`
- `enso_phase`
- `oni_lag6m`

If an exact ENSO month is not available, the script uses the latest available ENSO record before the fire date.

## Run

From the repository root:

```bash
python data-engineering/pipelines/fire_climate_enrichment/enrich_fire_climate.py