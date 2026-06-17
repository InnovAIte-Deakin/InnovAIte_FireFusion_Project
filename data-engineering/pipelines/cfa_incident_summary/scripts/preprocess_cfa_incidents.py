"""
Clean and enrich CFA Incident Summary data for hub-and-spoke loading.

Joins district reference coordinates, snaps to location_registry (at load time),
and outputs processed Parquet plus quarantine files for rejected rows.
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
    DISTRICT_REGISTRY_CSV,
    PROCESSED_DIR,
    PROCESSED_PARQUET,
    QUARANTINE_DIR,
    RAW_COLUMNS,
    SOURCE_SYSTEM,
    TIMEZONE,
    VALID_DISTRICT_NUMBERS,
)
from utils.season import get_australian_meteorological_season  # noqa: E402


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw headers to canonical names."""
    rename_map = {}
    lower_cols = {str(c).strip().lower(): c for c in df.columns}
    for canonical, aliases in RAW_COLUMNS.items():
        for alias in aliases:
            key = alias.strip().lower()
            if key in lower_cols:
                rename_map[lower_cols[key]] = canonical
                break
    return df.rename(columns=rename_map)


def load_raw_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Raw CFA file not found: {path}\n"
            "Place the file under data/raw/ or set CFA_INCIDENT_RAW_PATH. See data/DATA_SOURCE.md."
        )
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def parse_incident_datetime(series: pd.Series) -> pd.Series:
    """Parse '1/07/2020  1:17:10 AM' style strings in Australia/Melbourne."""
    parsed = pd.to_datetime(series, dayfirst=True, errors="coerce")
    if parsed.dt.tz is None:
        parsed = parsed.dt.tz_localize(
            TIMEZONE,
            ambiguous="infer",
            nonexistent="shift_forward",
        )
    else:
        parsed = parsed.dt.tz_convert(TIMEZONE)
    return parsed


def load_district_reference() -> pd.DataFrame:
    districts = pd.read_csv(DISTRICT_REGISTRY_CSV)
    districts["district_no"] = districts["district_no"].astype(int)
    return districts


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = normalize_columns(df.copy())
    stats = {"input_rows": len(df)}

    required = ["incident_datetime", "incident_no", "district_no"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns after normalization: {missing_cols}")

    # Quarantine: unparseable dates
    df["incident_datetime_parsed"] = parse_incident_datetime(df["incident_datetime"])
    bad_dates = df[df["incident_datetime_parsed"].isna()]
    stats["quarantine_bad_datetime"] = len(bad_dates)
    df = df[df["incident_datetime_parsed"].notna()].copy()

    # incident_no / district
    df["incident_no"] = pd.to_numeric(df["incident_no"], errors="coerce")
    df["district_no"] = pd.to_numeric(df["district_no"], errors="coerce")
    bad_ids = df[df["incident_no"].isna()]
    stats["quarantine_bad_incident_no"] = len(bad_ids)
    df = df[df["incident_no"].notna()].copy()
    df["incident_id"] = df["incident_no"].astype(int)

    # Quarantine: unknown districts
    df["district_no"] = df["district_no"].astype("Int64")
    unknown = df[~df["district_no"].isin(list(VALID_DISTRICT_NUMBERS))]
    stats["quarantine_unknown_district"] = len(unknown)
    df = df[df["district_no"].isin(list(VALID_DISTRICT_NUMBERS))].copy()
    df["district_no"] = df["district_no"].astype(int)

    # Duplicates
    dup_mask = df.duplicated(subset=["incident_id"], keep="first")
    dups = df[dup_mask]
    stats["quarantine_duplicate_incident_id"] = len(dups)
    df = df[~dup_mask].copy()

    # Type fields (nullable)
    if "incident_type_code" in df.columns:
        df["incident_type_code"] = pd.to_numeric(df["incident_type_code"], errors="coerce")
    else:
        df["incident_type_code"] = pd.NA
    if "incident_type" not in df.columns:
        df["incident_type"] = pd.NA
    df["incident_type"] = df["incident_type"].astype("string")

    # Join district reference (HQ anchor coordinates)
    districts = load_district_reference()
    df = df.merge(districts, on="district_no", how="left", suffixes=("", "_ref"))
    missing_ref = df[df["reference_latitude"].isna()]
    stats["quarantine_missing_district_ref"] = len(missing_ref)
    df = df[df["reference_latitude"].notna()].copy()

    # Derived time fields for load step
    df["datetime_record_key"] = (
        df["incident_datetime_parsed"]
        .dt.tz_convert(TIMEZONE)
        .dt.floor("min")
        .dt.tz_localize(None)
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    df["season"] = df["incident_datetime_parsed"].dt.month.map(get_australian_meteorological_season)
    df["source_system"] = SOURCE_SYSTEM

    # Final load-ready columns
    out_cols = [
        "incident_id",
        "district_no",
        "incident_type_code",
        "incident_type",
        "reference_latitude",
        "reference_longitude",
        "cfa_region",
        "headquarters_name",
        "region_name",
        "datetime_record_key",
        "season",
        "source_system",
        "incident_datetime_parsed",
    ]
    processed = df[out_cols].copy()
    stats["output_rows"] = len(processed)
    stats["retention_rate_pct"] = round(
        100.0 * len(processed) / max(stats["input_rows"], 1), 2
    )
    return processed, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess CFA Incident Summary")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(os.getenv("CFA_INCIDENT_RAW_PATH", DEFAULT_RAW_FILE)),
    )
    parser.add_argument("--output", type=Path, default=PROCESSED_PARQUET)
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_raw_dataframe(args.input)
    processed, stats = preprocess(raw)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    processed.to_parquet(args.output, index=False)

    stats_path = QUARANTINE_DIR / "preprocess_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))
    print(f"\nProcessed data: {args.output} ({len(processed)} rows)")
    print(f"Stats: {stats_path}")


if __name__ == "__main__":
    main()
