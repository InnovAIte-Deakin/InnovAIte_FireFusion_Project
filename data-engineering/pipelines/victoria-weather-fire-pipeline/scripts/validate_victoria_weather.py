import pandas as pd
from pathlib import Path

input_file = Path("data/cleaned/victoria_black_summer_weather_cleaned.csv")
output_dir = Path("data/validated")
output_dir.mkdir(parents=True, exist_ok=True)

report_file = output_dir / "weather_validation_report.txt"

df = pd.read_csv(input_file)

lines = []
lines.append("=== WEATHER VALIDATION REPORT ===\n\n")

lines.append("Missing values:\n")
lines.append(str(df.isnull().sum()) + "\n\n")

lines.append(f"Duplicate rows: {df.duplicated().sum()}\n\n")

lines.append("Data types:\n")
lines.append(str(df.dtypes) + "\n\n")

invalid_humidity = df[(df["relative_humidity"] < 0) | (df["relative_humidity"] > 100)]
invalid_wind = df[df["wind_speed_kmh"] < 0]
invalid_temp = df[(df["temperature_c"] < -50) | (df["temperature_c"] > 60)]

lines.append(f"Invalid humidity rows: {len(invalid_humidity)}\n")
lines.append(f"Invalid wind rows: {len(invalid_wind)}\n")
lines.append(f"Unrealistic temperature rows: {len(invalid_temp)}\n")

with open(report_file, "w") as f:
    f.writelines(lines)

print("Validation complete")
print("Report saved to:", report_file)