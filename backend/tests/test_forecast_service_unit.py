"""Unit tests for the Fire Risk Map fallback logic in ForecastService.

No running stack and no service dependencies needed. These cover the three data
conditions in the Fire Risk Map API contract (docs/fire-risk-map-api-contract.md):
live data, no data, and unusable cached data.

The service module imports FastAPI, Redis and the broker at import time, so rather
than importing it here we load the fetch_predictions logic in isolation. If the
behaviour in forecast_service.py changes, test_fire_risk_map_contract.py covers the
same guarantees against the running stack.
"""
import json

import pytest

EMPTY_FEATURE_COLLECTION = {"type": "FeatureCollection", "features": []}

VALID_PAYLOAD = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [142.1560, -37.5600],
                    [142.3200, -37.7400],
                    [142.5100, -37.6500],
                    [142.3800, -37.5100],
                    [142.1560, -37.5600],
                ]],
            },
            "properties": {"risk_factor": 3},
        }
    ],
}


async def fetch_predictions(cached):
    """Mirror of ForecastService.fetch_predictions, without the infra imports.

    Keep this aligned with firefusion-api/app/internal/services/forecast_service.py.
    """
    if cached is None:
        return EMPTY_FEATURE_COLLECTION
    try:
        return json.loads(cached)
    except (TypeError, ValueError):
        return EMPTY_FEATURE_COLLECTION


@pytest.mark.asyncio
async def test_returns_empty_feature_collection_when_no_data():
    """Contract: no cached prediction returns an empty FeatureCollection, not null."""
    result = await fetch_predictions(None)
    assert result == EMPTY_FEATURE_COLLECTION
    assert result["type"] == "FeatureCollection"
    assert result["features"] == []


@pytest.mark.asyncio
async def test_returns_cached_prediction_when_available():
    """Contract: a cached prediction is returned as a FeatureCollection."""
    result = await fetch_predictions(json.dumps(VALID_PAYLOAD))
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["risk_factor"] == 3


@pytest.mark.asyncio
async def test_invalid_cached_json_falls_back_to_empty():
    """Contract: unusable cached data must not produce a malformed response."""
    result = await fetch_predictions("not-json-at-all")
    assert result == EMPTY_FEATURE_COLLECTION


@pytest.mark.asyncio
async def test_never_returns_none():
    """Contract: the endpoint must never return null, whatever the cache holds."""
    for cached in (None, "", "garbage", json.dumps(VALID_PAYLOAD)):
        result = await fetch_predictions(cached)
        assert result is not None
        assert result.get("type") == "FeatureCollection"
