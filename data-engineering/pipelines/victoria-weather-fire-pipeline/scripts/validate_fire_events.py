import pandas as pd
from pathlib import Path

input_file = Path("data/cleaned/firms_victoria_fire_events_cleaned.csv")
output_dir = Path("data/validated")
output_dir.mkdir(parents=True, exist_ok=True)
report_file = output_dir / "fire_events_validation_report.txt"

df = pd.read_csv(input_file)

lines = []
lines.append("=== FIRE EVENTS VALIDATION REPORT ===\n\n")

lines.append("Missing values:\n")
lines.append(str(df.isnull().sum()) + "\n\n")

lines.append(f"Duplicate rows: {df.duplicated().sum()}\n\n")

lines.append("Data types:\n")
lines.append(str(df.dtypes) + "\n\n")

# Simple coordinate validation
invalid_lat = df[(df["latitude"] < -90) | (df["latitude"] > 90)]
invalid_lon = df[(df["longitude"] < -180) | (df["longitude"] > 180)]

lines.append(f"Invalid latitude rows: {len(invalid_lat)}\n")
lines.append(f"Invalid longitude rows: {len(invalid_lon)}\n")

with open(report_file, "w") as f:
    f.writelines(lines)

print("Validation complete")
print("Report saved to:", report_file)