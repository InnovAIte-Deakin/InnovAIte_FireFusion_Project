"""Smoke tests for firefusion-api (the main entry point)."""
import pytest

pytestmark = pytest.mark.integration


def test_service_is_up(ff, http):
    assert http.get(f"{ff}/openapi.json").status_code == 200


def test_health(ff, http):
    r = http.get(f"{ff}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "service": "firefusion-api"}


def test_hello(ff, http):
    assert http.get(f"{ff}/hello/").status_code == 200


def test_bushfire_forecast_returns_json(ff, http):
    r = http.get(f"{ff}/api/bushfire-forecast")
    assert r.status_code == 200
    r.json()  # must be valid JSON


@pytest.mark.parametrize("path", [
    "/api/misinformation/narratives",
    "/api/misinformation/posts",
    "/api/misinformation/incidents",
])
def test_misinformation_list_endpoints(ff, http, path):
    r = http.get(f"{ff}{path}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_unknown_post_returns_404(ff, http):
    r = http.get(f"{ff}/api/misinformation/posts/does-not-exist-xyz")
    assert r.status_code == 404
