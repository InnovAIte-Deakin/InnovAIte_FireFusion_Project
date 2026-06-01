"""
Nearest-neighbour grid snapping against location_registry (Supabase).

Uses method='nearest' per data-engineering/utils/interpolate.md for discrete
events (fire incidents).
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy.spatial import cKDTree

load_dotenv()


class GridSnapper:
    """Maps reference lat/lon to the nearest location_registry grid cell."""

    def __init__(self, supabase_client=None):
        if supabase_client is not None:
            self._client = supabase_client
        else:
            from supabase import create_client

            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise EnvironmentError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in .env for grid snapping."
                )
            self._client = create_client(url, key)
        self._grid: Optional[pd.DataFrame] = None
        self._tree: Optional[cKDTree] = None

    def fetch_grid(self) -> pd.DataFrame:
        if self._grid is not None:
            return self._grid

        all_rows = []
        offset = 0
        chunk = 1000
        while True:
            response = (
                self._client.table("location_registry")
                .select("location_id,grid_latitude,grid_longitude,region_name")
                .range(offset, offset + chunk - 1)
                .execute()
            )
            rows = response.data or []
            all_rows.extend(rows)
            if len(rows) < chunk:
                break
            offset += chunk

        if not all_rows:
            raise RuntimeError("location_registry is empty — load the Victoria grid first.")

        self._grid = pd.DataFrame(all_rows)
        coords = self._grid[["grid_longitude", "grid_latitude"]].values
        self._tree = cKDTree(coords)
        return self._grid

    def snap_point(
        self, latitude: float, longitude: float
    ) -> dict:
        """Return location_id and snapped grid coordinates for one point."""
        grid = self.fetch_grid()
        _, idx = self._tree.query([longitude, latitude])
        row = grid.iloc[int(idx)]
        return {
            "location_id": int(row["location_id"]),
            "grid_latitude": float(row["grid_latitude"]),
            "grid_longitude": float(row["grid_longitude"]),
            "region_name": row.get("region_name"),
        }

    def snap_dataframe(
        self,
        df: pd.DataFrame,
        lat_col: str = "reference_latitude",
        lon_col: str = "reference_longitude",
    ) -> pd.DataFrame:
        """Add location_id, grid_latitude, grid_longitude to each row."""
        self.fetch_grid()
        coords = df[[lon_col, lat_col]].values
        _, indices = self._tree.query(coords)
        snapped = self._grid.iloc[indices].reset_index(drop=True)
        out = df.copy()
        out["location_id"] = snapped["location_id"].astype(int).values
        out["grid_latitude"] = snapped["grid_latitude"].astype(float).values
        out["grid_longitude"] = snapped["grid_longitude"].astype(float).values
        return out
