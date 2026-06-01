"""
CFA Incident Summary — historical pipeline entry point.

Workflow A (one-time bulk load) aligned with database_architecture.md.

Usage:
    python main.py --profile
    python main.py --preprocess
    python main.py --validate
    python main.py --load
    python main.py --all
    python main.py --all --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent
SCRIPTS = PIPELINE_ROOT / "scripts"


def run_script(name: str, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, str(SCRIPTS / name)] + (extra_args or [])
    print(f"\n>>> {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="CFA Incident Summary pipeline")
    parser.add_argument("--profile", action="store_true", help="Profile raw dataset")
    parser.add_argument("--preprocess", action="store_true", help="Preprocess raw to Parquet")
    parser.add_argument("--validate", action="store_true", help="Validate processed output")
    parser.add_argument("--load", action="store_true", help="Load districts + incidents to Supabase")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Load step: prepare only, no upload")
    args = parser.parse_args()

    if not any([args.profile, args.preprocess, args.validate, args.load, args.all]):
        parser.print_help()
        sys.exit(0)

    load_extra = ["--dry-run"] if args.dry_run else []

    if args.all or args.profile:
        run_script("profile_cfa_incidents.py")
    if args.all or args.preprocess:
        run_script("preprocess_cfa_incidents.py")
    if args.all or args.validate:
        run_script("validate_cfa_incidents.py")
    if args.all or args.load:
        run_script("load_cfa_to_supabase.py", load_extra)

    print("\nPipeline step(s) complete.")


if __name__ == "__main__":
    main()
