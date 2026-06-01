"""
Validate processed CFA incidents before Supabase load.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from config.pipeline_config import (  # noqa: E402
    LOGS_DIR,
    PROCESSED_PARQUET,
    VALIDATION_JSON,
    VALID_DISTRICT_NUMBERS,
)


REQUIRED_COLUMNS = [
    "incident_id",
    "district_no",
    "reference_latitude",
    "reference_longitude",
    "datetime_record_key",
    "season",
    "source_system",
]


def validate(df: pd.DataFrame) -> dict:
    report = {
        "row_count": len(df),
        "validation_passed": True,
        "errors": [],
        "warnings": [],
    }

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        report["validation_passed"] = False
        report["errors"].append(f"Missing columns: {missing}")
        return report

    if df["incident_id"].duplicated().any():
        report["validation_passed"] = False
        report["errors"].append("Duplicate incident_id values in processed file.")

    invalid_districts = set(df["district_no"].unique()) - VALID_DISTRICT_NUMBERS
    if invalid_districts:
        report["validation_passed"] = False
        report["errors"].append(f"Invalid district_no values: {sorted(invalid_districts)}")

    if df["reference_latitude"].isna().any() or df["reference_longitude"].isna().any():
        report["validation_passed"] = False
        report["errors"].append("Null reference coordinates found.")

    if df["datetime_record_key"].isna().any():
        report["validation_passed"] = False
        report["errors"].append("Null datetime_record_key values found.")

    null_type_pct = round(100.0 * df["incident_type"].isna().sum() / max(len(df), 1), 2)
    if null_type_pct > 0:
        report["warnings"].append(f"{null_type_pct}% rows have null incident_type (allowed).")

    report["distinct_incident_id"] = int(df["incident_id"].nunique())
    report["distinct_districts"] = int(df["district_no"].nunique())
    report["distinct_timestamps"] = int(df["datetime_record_key"].nunique())
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate processed CFA incidents")
    parser.add_argument("--input", type=Path, default=PROCESSED_PARQUET)
    parser.add_argument("--output", type=Path, default=VALIDATION_JSON)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Processed file not found: {args.input}. Run preprocess first.")

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(args.input)
    report = validate(df)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not report["validation_passed"]:
        sys.exit(1)
    print(f"\nValidation passed. Report: {args.output}")


if __name__ == "__main__":
    main()
