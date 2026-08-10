import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data-engineering/pipelines/realtime_weather/output/realtime_weather_raw.csv")
OUTPUT_FILE = Path("data-engineering/pipelines/realtime_weather/output/realtime_weather_validated.csv")

def validate_weather_data(df):
    required_columns = [
        "location_id",
        "time_id",
        "original_latitude",
        "original_longitude",
        "temperature_c",
        "wind_speed_kmh",
        "relative_humidity",
        "source_system"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = df.dropna(subset=[
        "original_latitude",
        "original_longitude",
        "temperature_c",
        "wind_speed_kmh",
        "relative_humidity"
    ])

    df = df[
        (df["relative_humidity"] >= 0) &
        (df["relative_humidity"] <= 100) &
        (df["wind_speed_kmh"] >= 0) &
        (df["temperature_c"] >= -20) &
        (df["temperature_c"] <= 60)
    ]

    return df

def main():
    df = pd.read_csv(INPUT_FILE)

    validated_df = validate_weather_data(df)

    validated_df.to_csv(OUTPUT_FILE, index=False)

    print("Validation completed successfully.")
    print(f"Validated file saved to: {OUTPUT_FILE}")
    print(validated_df)

if __name__ == "__main__":
    main()
