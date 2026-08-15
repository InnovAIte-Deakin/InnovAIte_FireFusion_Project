"""Integration tests for the Fire Risk Map endpoint.

Validates GET /api/bushfire-forecast against the agreed API contract
(see docs/fire-risk-map-api-contract.md). These hit the running stack and
skip cleanly when it is not up.
"""
import pytest

pytestmark = pytest.mark.integration

RISK_MIN, RISK_MAX = 0, 5


def _get_forecast(ff, http):
    r = http.get(f"{ff}/api/bushfire-forecast")
    assert r.status_code in (200, 503), f"unexpected status {r.status_code}"
    if r.status_code == 503:
        pytest.skip("forecast dependency unavailable (503) - contract-compliant, nothing to validate")
    return r.json()


def test_returns_a_feature_collection(ff, http):
    """Contract: the body is always a GeoJSON FeatureCollection, never null."""
    body = _get_forecast(ff, http)
    assert body is not None, "endpoint returned null; map clients cannot render this"
    assert isinstance(body, dict)
    assert body.get("type") == "FeatureCollection"
    assert isinstance(body.get("features"), list)


def test_empty_data_is_still_valid_geojson(ff, http):
    """Contract: with no prediction cached, features is an empty list, not null."""
    body = _get_forecast(ff, http)
    features = body.get("features")
    assert features is not None
    if not features:
        assert features == []


def test_features_match_the_agreed_schema(ff, http):
    """Contract: each feature is a Polygon with an integer risk_factor 0-5."""
    body = _get_forecast(ff, http)
    for i, feature in enumerate(body.get("features", [])):
        assert feature.get("type") == "Feature", f"feature {i} has wrong type"
        geometry = feature.get("geometry", {})
        assert geometry.get("type") == "Polygon", f"feature {i} geometry is not a Polygon"
        coords = geometry.get("coordinates")
        assert isinstance(coords, list) and coords, f"feature {i} has no coordinates"

        risk = feature.get("properties", {}).get("risk_factor")
        assert isinstance(risk, int), f"feature {i} risk_factor is not an integer"
        assert RISK_MIN <= risk <= RISK_MAX, f"feature {i} risk_factor {risk} outside {RISK_MIN}-{RISK_MAX}"


def test_polygon_rings_are_closed(ff, http):
    """GeoJSON requires the first and last position of a ring to match."""
    body = _get_forecast(ff, http)
    for i, feature in enumerate(body.get("features", [])):
        for j, ring in enumerate(feature["geometry"]["coordinates"]):
            assert len(ring) >= 4, f"feature {i} ring {j} needs at least 4 positions"
            assert ring[0] == ring[-1], f"feature {i} ring {j} is not closed"


def test_coordinates_are_lon_lat_within_valid_range(ff, http):
    """Contract: coordinates are [longitude, latitude], so ranges are +/-180 and +/-90."""
    body = _get_forecast(ff, http)
    for i, feature in enumerate(body.get("features", [])):
        for ring in feature["geometry"]["coordinates"]:
            for lon, lat in ring:
                assert -180 <= lon <= 180, f"feature {i} longitude {lon} out of range"
                assert -90 <= lat <= 90, f"feature {i} latitude {lat} out of range"


def test_endpoint_is_documented_in_openapi(ff, http):
    """Contract: the endpoint appears in the published OpenAPI docs for Front-end."""
    spec = http.get(f"{ff}/openapi.json").json()
    assert "/api/bushfire-forecast" in spec.get("paths", {})
    assert "get" in spec["paths"]["/api/bushfire-forecast"]
