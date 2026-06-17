"""
Verify Supabase configuration before running load_cfa_to_supabase.py.

Usage (from cfa_incident_summary folder):
    python scripts/verify_supabase_setup.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PIPELINE_ROOT / ".env")

REQUIRED_TABLES = [
    "location_registry",
    "time_registry",
    "cfa_district_registry",
    "fire_incident_record",
]


def main() -> None:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    print("=== Supabase configuration check ===\n")

    if not url or "your-project" in url:
        print("FAIL: SUPABASE_URL is missing or still a placeholder in .env")
        sys.exit(1)
    if not key or key.startswith("your-") or key.startswith("sb_secret_"):
        print("FAIL: SUPABASE_KEY is missing, placeholder, or invalid in .env")
        print("      Use SUPABASE_KEY=... in .env (not in source code).")
        sys.exit(1)
    if url.startswith("postgresql://") or ("@" in url and not url.startswith("https://")):
        print("FAIL: SUPABASE_URL must be the API URL (https://xxx.supabase.co), not DATABASE_URL")
        sys.exit(1)

    print(f"SUPABASE_URL: {url}")
    print(f"SUPABASE_KEY: {'*' * 8}...{key[-4:] if len(key) > 4 else '****'}")

    try:
        from supabase import create_client
    except ImportError:
        print("\nFAIL: Install dependencies: pip install -r requirements.txt")
        sys.exit(1)

    client = create_client(url, key)
    print("\n--- Table checks ---")

    all_ok = True
    for table in REQUIRED_TABLES:
        try:
            response = client.table(table).select("*", count="exact").limit(1).execute()
            count = response.count if response.count is not None else len(response.data or [])
            print(f"  OK  {table} (accessible, sample count hint: {count})")
        except Exception as exc:
            print(f"  FAIL {table}: {exc}")
            all_ok = False

    if all_ok:
        loc = client.table("location_registry").select("*", count="exact").limit(1).execute()
        loc_count = loc.count or 0
        if loc_count == 0:
            print("\nWARN: location_registry is empty. Load the Victoria grid first")
            print("      (see data-engineering/notebooks/grid/push_grid_supabase.ipynb)")
            all_ok = False

        time = client.table("time_registry").select("*", count="exact").limit(1).execute()
        time_count = time.count or 0
        if time_count == 0:
            print("\nWARN: time_registry is empty. Populate time_registry first")
            print("      (see data-engineering/notebooks/time/time_registry.ipynb)")
            all_ok = False
        else:
            print(f"\nOK  time_registry has data (~{time_count} rows reported)")

    print("\n=== Result ===")
    if all_ok:
        print("Ready for: python main.py --load")
        sys.exit(0)

    print("Fix issues above, then run SQL migrations in Supabase if tables are missing.")
    print("See docs/SUPABASE_SETUP.md")
    sys.exit(1)


if __name__ == "__main__":
    main()
