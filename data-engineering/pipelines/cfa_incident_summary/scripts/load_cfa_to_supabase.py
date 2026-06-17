"""
Load CFA district registry and fire incidents into Supabase (hub-and-spoke).

Order:
  1. CFA_District_Registry (+ snap districts to location_registry)
  2. Fire_Incident_Record (resolve time_id + location_id per row)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_ROOT))

from config.pipeline_config import (  # noqa: E402
    DISTRICT_REGISTRY_CSV,
    LOAD_REPORT_JSON,
    LOGS_DIR,
    PROCESSED_PARQUET,
    SOURCE_SYSTEM,
    SUPABASE_BATCH_SIZE,
)
from utils.grid_snapper import GridSnapper  # noqa: E402
from utils.time_registry import TimeRegistryResolver  # noqa: E402

load_dotenv()


def get_supabase():
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY required in .env")
    return create_client(url, key)


def load_districts(client, snapper: GridSnapper, dry_run: bool = False) -> dict:
    districts = pd.read_csv(DISTRICT_REGISTRY_CSV)
    districts = snapper.snap_dataframe(
        districts,
        lat_col="reference_latitude",
        lon_col="reference_longitude",
    )

    records = []
    for _, row in districts.iterrows():
        records.append(
            {
                "district_no": int(row["district_no"]),
                "cfa_region": str(row["cfa_region"]),
                "headquarters_name": str(row["headquarters_name"]),
                "location_id": int(row["location_id"]),
                "reference_latitude": float(row["reference_latitude"]),
                "reference_longitude": float(row["reference_longitude"]),
                "source": str(row.get("source", "CFA Victoria district map")),
            }
        )

    if dry_run:
        return {"districts_prepared": len(records), "dry_run": True}

    client.table("cfa_district_registry").upsert(
        records, on_conflict="district_no"
    ).execute()
    return {"districts_upserted": len(records)}


def load_incidents(
    client,
    df: pd.DataFrame,
    snapper: GridSnapper,
    time_resolver: TimeRegistryResolver,
    dry_run: bool = False,
    batch_size: int = SUPABASE_BATCH_SIZE,
) -> dict:
  # District-level location: use district registry location_id via merge
    districts = pd.read_csv(DISTRICT_REGISTRY_CSV)
    districts = snapper.snap_dataframe(
        districts, lat_col="reference_latitude", lon_col="reference_longitude"
    )
    district_loc = districts.set_index("district_no")["location_id"].to_dict()

    df = df.reset_index(drop=True)
    time_ids = time_resolver.resolve_series(
        pd.to_datetime(df["incident_datetime_parsed"], utc=True)
    )

    payload = []
    for i, row in df.iterrows():
        dno = int(row["district_no"])
        payload.append(
            {
                "incident_id": int(row["incident_id"]),
                "location_id": int(district_loc[dno]),
                "time_id": int(time_ids.iloc[i]),
                "original_latitude": float(row["reference_latitude"]),
                "original_longitude": float(row["reference_longitude"]),
                "district_no": dno,
                "incident_type_code": None
                if pd.isna(row.get("incident_type_code"))
                else float(row["incident_type_code"]),
                "incident_type": None
                if pd.isna(row.get("incident_type"))
                else str(row["incident_type"]),
                "confidence_score": None,
                "source_system": SOURCE_SYSTEM,
            }
        )

    if dry_run:
        return {"incidents_prepared": len(payload), "dry_run": True}

    uploaded = 0
    for i in range(0, len(payload), batch_size):
        batch = payload[i : i + batch_size]
        client.table("fire_incident_record").upsert(
            batch, on_conflict="incident_id"
        ).execute()
        uploaded += len(batch)
        time.sleep(0.15)

    return {"incidents_upserted": uploaded}


def main() -> None:
    parser = argparse.ArgumentParser(description="Load CFA data to Supabase")
    parser.add_argument("--input", type=Path, default=PROCESSED_PARQUET)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--districts-only", action="store_true")
    parser.add_argument("--incidents-only", action="store_true")
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    client = get_supabase()
    snapper = GridSnapper(client)
    time_resolver = TimeRegistryResolver(client)

    report = {"dry_run": args.dry_run}

    if not args.incidents_only:
        report["districts"] = load_districts(client, snapper, dry_run=args.dry_run)

    if not args.districts_only:
        if not args.input.exists():
            raise FileNotFoundError(f"Processed file missing: {args.input}")
        df = pd.read_parquet(args.input)
        report["incidents"] = load_incidents(
            client, df, snapper, time_resolver, dry_run=args.dry_run
        )

    LOAD_REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nLoad report: {LOAD_REPORT_JSON}")


if __name__ == "__main__":
    main()
