# Fire Climate Enrichment

This pipeline enriches sample fire records with two climate signals:

1. Local weather data from the existing realtime weather pipeline
2. ENSO / ONI climate data from the NOAA CPC ENSO pipeline

## Inputs

- `sample_fires.csv`
- `realtime_weather_validated.csv`
- processed ENSO / ONI CSV (the script currently selects the 20260906 file)

## Enriched fields

### Local weather
- `temperature_c`
- `wind_speed_kmh`
- `relative_humidity`

### ENSO
- `oni_anomaly`
- `enso_phase`
- `oni_lag6m`

The backward join selects the latest season centre at or before the fire month.
The existing `enso_match_date` is the first day of the fire month. Three columns
describe the selected record.

| Column | Meaning |
|---|---|
| `enso_source_month` | Centre month of the selected three-month season, formatted as YYYY-MM. |
| `enso_age_months` | Calendar months from that centre to the fire month. |
| `enso_match_status` | `exact` for the same centre month, `prior` for an earlier one, or `unmatched` when there is no eligible row. |

An unmatched fire stays in the CSV with empty climate values, source month and age.
The join has no maximum age. The status describes the month match. Individual
features such as `oni_lag6m` can be missing even when a season matches.

For example, July's JJA reading includes August observations. A July fire can
match JJA in a historical dataset even though that reading was unavailable
on the fire date. Historical forecast replay requires the publication time and
the version then available. [NOAA CPC ONI](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/)

## Run

From the repository root:

```bash
python data-engineering/pipelines/fire_climate_enrichment/enrich_fire_climate.py
```
