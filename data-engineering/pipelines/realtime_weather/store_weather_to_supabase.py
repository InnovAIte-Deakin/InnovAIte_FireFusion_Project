import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data-engineering/pipelines/realtime_weather/output/realtime_weather_validated.csv")
OUTPUT_FILE = Path("data-engineering/pipelines/realtime_weather/output/weather_observation_supabase_ready.csv")

def main():
    df = pd.read_csv(INPUT_FILE)

    supabase_df = df[
        [
            "location_id",
            "time_id",
            "original_latitude",
            "original_longitude",
            "temperature_c",
            "wind_speed_kmh",
            "relative_humidity",
        ]
    ]

    supabase_df.to_csv(OUTPUT_FILE, index=False)

    print("Supabase-ready weather CSV created.")
    print(f"Output file: {OUTPUT_FILE}")
    print(supabase_df)

if __name__ == "__main__":
    main()
