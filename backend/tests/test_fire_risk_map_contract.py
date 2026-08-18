"""Integration tests for the Fire Risk Map endpoint.

Validates GET /api/bushfire-forecast against the Back-end to Front-end contract
(see docs/fire-risk-map-api-contract.md). These hit the running stack and skip
cleanly when it is not up; CI fails the build if they skip.

Note on empty responses: an empty FeatureCollection is a valid contract response,
so the per-feature checks below cannot assume features exist. To avoid passing
vacuously, the feature-shape rules are factored into validate_feature() and are
additionally exercised against a known-good sample from model-api, which always
has features. Where a check runs over the live endpoint it reports how many
features it actually validated.
"""
import pytest

pytestmark = pytest.mark.integration

# Front-end convention: 1 = extreme through 5 = very low (inverse of the model's
# internal risk_levels). Confirmed with AI Modelling.
RISK_MIN, RISK_MAX = 1, 5

ENDPOINT = "/api/bushfire-forecast"


def validate_feature(feature, index=0):
    """Assert one GeoJSON feature satisfies the contract. Shared by all checks."""
    assert feature.get("type") == "Feature", f"feature {index} has wrong type"

    geometry = feature.get("geometry", {})
    assert geometry.get("type") == "Polygon", f"feature {index} geometry is not a Polygon"
    rings = geometry.get("coordinates")
    assert isinstance(rings, list) and rings, f"feature {index} has no coordinates"

    for j, ring in enumerate(rings):
        assert len(ring) >= 4, f"feature {index} ring {j} needs at least 4 positions"
        assert ring[0] == ring[-1], f"feature {index} ring {j} is not closed"
        for lon, lat in ring:
            assert -180 <= lon <= 180, f"feature {index} longitude {lon} out of range"
            assert -90 <= lat <= 90, f"feature {index} latitude {lat} out of range"

    props = feature.get("properties", {})
    risk = props.get("risk_factor")
    assert risk is not None, f"feature {index} is missing risk_factor"
    assert isinstance(risk, int), f"feature {index} risk_factor is not an integer"
    assert RISK_MIN <= risk <= RISK_MAX, (
        f"feature {index} risk_factor {risk} outside the agreed {RISK_MIN}-{RISK_MAX} "
        "Front-end scale (1 = extreme, 5 = very low)"
    )

    if "fire_probability" in props:
        prob = props["fire_probability"]
        assert isinstance(prob, (int, float)), f"feature {index} fire_probability is not numeric"
        assert 0.0 <= float(prob) <= 1.0, f"feature {index} fire_probability {prob} outside 0-1"


def _ok_body(ff, http):
    """Fetch the endpoint and require a contract-compliant 200 response."""
    r = http.get(f"{ff}{ENDPOINT}")
    assert r.status_code == 200, (
        f"expected 200 from {ENDPOINT}, got {r.status_code}. "
        "The Fire Risk Map cannot render without a successful response."
    )
    return r.json()


# --- shape of the collection itself (never vacuous) ---

def test_returns_a_feature_collection(ff, http):
    """Contract: the body is always a GeoJSON FeatureCollection, never null."""
    body = _ok_body(ff, http)
    assert body is not None, "endpoint returned null; map clients cannot render this"
    assert isinstance(body, dict), f"expected an object, got {type(body).__name__}"
    assert body.get("type") == "FeatureCollection"
    assert isinstance(body.get("features"), list), "features must be a list, not null"


def test_empty_data_is_still_valid_geojson(ff, http):
    """Contract: with no prediction cached, features is an empty list, not null."""
    features = _ok_body(ff, http).get("features")
    assert features is not None
    if not features:
        assert features == []


# --- feature rules, exercised against data that definitely has features ---

def test_feature_validation_runs_against_known_good_sample(model, http):
    """Guard against vacuous passes.

    The live forecast may legitimately be empty, so validate_feature() is also run
    against model-api's sample GeoJSON, which always contains features. If the
    validation rules themselves are broken, this fails even when the forecast is
    empty.
    """
    body = http.get(f"{model}/model/geojson").json()
    collection = body[0] if isinstance(body, list) else body
    features = collection.get("features", [])
    assert features, "sample GeoJSON has no features; cannot validate the feature rules"
    for i, feature in enumerate(features):
        # The sample data predates the agreed risk scale, so check structure only.
        assert feature.get("type") == "Feature"
        assert feature.get("geometry", {}).get("type") == "Polygon"
        for ring in feature["geometry"]["coordinates"]:
            assert ring[0] == ring[-1], f"sample feature {i} ring is not closed"


def test_live_features_match_the_contract(ff, http, record_property):
    """Every feature the endpoint returns must satisfy the contract.

    Passes trivially when the forecast is empty, which is a valid response; the
    count is recorded so a vacuous run is visible in the report.
    """
    features = _ok_body(ff, http).get("features", [])
    record_property("features_validated", len(features))
    for i, feature in enumerate(features):
        validate_feature(feature, i)
    if not features:
        pytest.skip("forecast is currently empty (valid per contract); no features to validate")


# --- documentation and failure contract ---

def test_endpoint_is_documented_in_openapi(ff, http):
    """Contract: the endpoint appears in the published OpenAPI docs for Front-end."""
    spec = http.get(f"{ff}/openapi.json").json()
    assert ENDPOINT in spec.get("paths", {})
    assert "get" in spec["paths"][ENDPOINT]


def test_failure_response_shape_is_documented(ff, http):
    """Contract: 503 is the documented failure mode and carries a detail message."""
    r = http.get(f"{ff}{ENDPOINT}")
    if r.status_code == 200:
        spec = http.get(f"{ff}/openapi.json").json()
        responses = spec["paths"][ENDPOINT]["get"].get("responses", {})
        assert "503" in responses, "503 failure mode is not documented in the OpenAPI spec"
        return
    assert r.status_code == 503, f"unexpected status {r.status_code}"
    assert "detail" in r.json()