"""Unit test: no running stack needed.

Validates a bundled risk-layer sample is well-formed GeoJSON. Runs in CI
even without Docker, so it catches broken data files fast.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "model-api" / "app" / "data"


def test_sample_geojson_is_valid_feature_collection():
    sample = DATA_DIR / "geojson_data-0.json"
    assert sample.exists(), f"missing sample data at {sample}"
    data = json.loads(sample.read_text())
    assert data.get("type") == "FeatureCollection"
    assert isinstance(data.get("features"), list) and data["features"]
    first = data["features"][0]
    assert first.get("type") == "Feature"
    assert "geometry" in first and "properties" in first
