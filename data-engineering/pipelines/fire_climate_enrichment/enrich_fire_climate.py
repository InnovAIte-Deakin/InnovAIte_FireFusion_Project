import pandas as pd
from pathlib import Path

BASE_DIR = Path("data-engineering/pipelines/fire_climate_enrichment")

FIRE_FILE = BASE_DIR / "sample_fires.csv"

WEATHER_FILE = Path(
    "data-engineering/pipelines/realtime_weather/output/realtime_weather_validated.csv"
)

ENSO_FILE = Path(
    "data-engineering/data/processed/noaa_cpc_enso_oni_processed_20260906.csv"
)

OUTPUT_FILE = BASE_DIR / "sample_fires_dual_climate_enriched.csv"


def load_sample_fires():
    df = pd.read_csv(FIRE_FILE)
    df["fire_datetime"] = pd.to_datetime(df["fire_datetime"])
    df["record_year_month"] = df["fire_datetime"].dt.strftime("%Y-%m")
    return df


def load_weather():
    return pd.read_csv(WEATHER_FILE)


def load_enso():
    return pd.read_csv(ENSO_FILE)


def enrich_with_weather(fires, weather):
    weather_fields = weather[
        [
            "location_id",
            "temperature_c",
            "wind_speed_kmh",
            "relative_humidity",
            "source_system",
        ]
    ]

    return fires.merge(
        weather_fields,
        on="location_id",
        how="left"
    )


def enrich_with_enso(fires, enso):
    fires = fires.copy()
    enso = enso.copy()

    fires["enso_match_date"] = pd.to_datetime(
        fires["record_year_month"] + "-01"
    )

    enso["enso_match_date"] = pd.to_datetime(
        enso["record_year_month"] + "-01"
    )

    enso_fields = enso[
        [
            "enso_match_date",
            "oni_anomaly",
            "enso_phase",
            "oni_lag6m",
        ]
    ].sort_values("enso_match_date")

    fires = fires.sort_values("enso_match_date")

    enriched = pd.merge_asof(
        fires,
        enso_fields,
        on="enso_match_date",
        direction="backward"
    )

    return enriched


def main():
    fires = load_sample_fires()
    weather = load_weather()
    enso = load_enso()

    enriched = enrich_with_weather(fires, weather)
    enriched = enrich_with_enso(enriched, enso)

    enriched.to_csv(OUTPUT_FILE, index=False)

    print("Dual climate enrichment completed.")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(enriched)


if __name__ == "__main__":
    main()