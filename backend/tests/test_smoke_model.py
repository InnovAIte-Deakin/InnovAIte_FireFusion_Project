"""Smoke tests for model-api (ML inference service)."""
import pytest

pytestmark = pytest.mark.integration


def test_health(model, http):
    r = http.get(f"{model}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "service": "model-api"}


def test_model_hello(model, http):
    r = http.get(f"{model}/model/hello")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello from model-api"}


def test_model_geojson_is_feature_collection(model, http):
    r = http.get(f"{model}/model/geojson")
    assert r.status_code == 200
    body = r.json()
    # served risk layer should be GeoJSON (FeatureCollection) or a list of them
    if isinstance(body, dict):
        assert body.get("type") == "FeatureCollection"
    else:
        assert isinstance(body, list)
