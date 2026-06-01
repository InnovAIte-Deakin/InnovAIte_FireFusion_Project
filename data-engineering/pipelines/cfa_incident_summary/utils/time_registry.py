"""
Resolve incident datetimes to time_registry.time_id via Supabase.

Expects time_registry rows keyed by datetime_record (minute resolution),
as populated by data-engineering/notebooks/time/time_registry.ipynb.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class TimeRegistryResolver:
    def __init__(self, supabase_client=None, timezone: str = "Australia/Melbourne"):
        if supabase_client is not None:
            self._client = supabase_client
        else:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise EnvironmentError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in .env for time lookup."
                )
            self._client = create_client(url, key)
        self._tz = timezone
        self._cache: Dict[str, int] = {}

    @staticmethod
    def to_registry_key(ts: pd.Timestamp) -> str:
        """Format timestamp for time_registry.datetime_record lookup."""
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC").tz_localize(None)
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    def resolve_series(self, datetimes: pd.Series) -> pd.Series:
        """Map timezone-aware datetimes to time_id (with caching)."""
        if datetimes.dt.tz is None:
            localized = datetimes.dt.tz_localize(self._tz)
        else:
            localized = datetimes.dt.tz_convert(self._tz)

        floored = localized.dt.floor("min").dt.tz_localize(None)
        keys = floored.map(self.to_registry_key)

        unique_keys = [k for k in keys.unique().tolist() if k not in self._cache]
        if unique_keys:
            self._fetch_batch(unique_keys)

        return keys.map(self._cache)

    def _fetch_batch(self, keys: List[str], batch_size: int = 200) -> None:
        for i in range(0, len(keys), batch_size):
            batch = keys[i : i + batch_size]
            response = (
                self._client.table("time_registry")
                .select("time_id,datetime_record")
                .in_("datetime_record", batch)
                .execute()
            )
            for row in response.data or []:
                self._cache[row["datetime_record"]] = int(row["time_id"])

        missing = [k for k in keys if k not in self._cache]
        if missing:
            raise ValueError(
                f"{len(missing)} datetime(s) not found in time_registry. "
                f"Example missing key: {missing[0]}. "
                "Ensure time_registry is populated for your incident date range."
            )
