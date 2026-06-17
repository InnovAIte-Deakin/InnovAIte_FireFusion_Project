"""
Profile raw CFA Incident Summary data — outputs quantifiable QA metrics (JSON).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from config.pipeline_config import (  # noqa: E402
    DEFAULT_RAW_FILE,
    LOGS_DIR,
    PROFILE_JSON,
    RAW_COLUMNS,
    VALID_DISTRICT_NUMBERS,
)
from scripts.preprocess_cfa_incidents import (  # noqa: E402
    load_raw_dataframe,
    normalize_columns,
)


def build_profile(df: pd.DataFrame) -> dict:
    df = normalize_columns(df)
    total = len(df)

    district_col = df["district_no"] if "district_no" in df.columns else pd.Series(dtype=float)
    district_numeric = pd.to_numeric(district_col, errors="coerce")
    unknown_districts = sorted(
        set(district_numeric.dropna().astype(int).unique())
        - VALID_DISTRICT_NUMBERS
    )

    parsed_dates, parse_failures = _try_parse_dates(df.get("incident_datetime"))

    profile = {
        "total_rows": total,
        "distinct_incident_no": int(df["incident_no"].nunique()) if "incident_no" in df.columns else None,
        "duplicate_incident_no_count": int(df["incident_no"].duplicated().sum())
        if "incident_no" in df.columns
        else None,
        "null_incident_type_code_pct": _null_pct(df, "incident_type_code"),
        "null_incident_type_pct": _null_pct(df, "incident_type"),
        "null_district_no_pct": _null_pct(df, "district_no"),
        "unknown_district_numbers": unknown_districts,
        "unknown_district_row_count": int(
            district_numeric.dropna().astype(int).isin(unknown_districts).sum()
        )
        if unknown_districts
        else 0,
        "valid_district_row_count": int(
            district_numeric.dropna().astype(int).isin(VALID_DISTRICT_NUMBERS).sum()
        ),
        "datetime_parse_failure_count": parse_failures,
        "datetime_parse_success_count": int(parsed_dates.notna().sum())
        if parsed_dates is not None
        else None,
        "datetime_min": str(parsed_dates.min()) if parsed_dates is not None and parsed_dates.notna().any() else None,
        "datetime_max": str(parsed_dates.max()) if parsed_dates is not None and parsed_dates.notna().any() else None,
        "top_incident_types": (
            df["incident_type"].value_counts().head(10).astype(str).to_dict()
            if "incident_type" in df.columns
            else {}
        ),
        "district_distribution": (
            district_numeric.dropna().astype(int).value_counts().sort_index().astype(int).to_dict()
        ),
    }
    return profile


def _null_pct(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or len(df) == 0:
        return 0.0
    return round(100.0 * df[col].isna().sum() / len(df), 2)


def _try_parse_dates(series: pd.Series | None):
    if series is None:
        return None, 0
    parsed = pd.to_datetime(series, dayfirst=True, errors="coerce")
    return parsed, int(parsed.isna().sum())


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile CFA Incident Summary raw file")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(os.getenv("CFA_INCIDENT_RAW_PATH", DEFAULT_RAW_FILE)),
    )
    parser.add_argument("--output", type=Path, default=PROFILE_JSON)
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_raw_dataframe(args.input)
    profile = build_profile(df)
    profile["input_file"] = str(args.input)

    args.output.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(json.dumps(profile, indent=2))
    print(f"\nProfile written to {args.output}")


if __name__ == "__main__":
    main()
