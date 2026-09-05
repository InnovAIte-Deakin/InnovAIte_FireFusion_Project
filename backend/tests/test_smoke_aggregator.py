"""Smoke tests for aggregator-api (DB-facing, API-key protected)."""
import pytest

pytestmark = pytest.mark.integration


def test_service_is_up(agg, http):
    assert http.get(f"{agg}/openapi.json").status_code == 200


def test_health(agg, http):
    r = http.get(f"{agg}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy", "service": "aggregator-api"}


def test_hello_is_protected_without_api_key(agg, http):
    # verify_api_key guards this route; without a valid key it must be rejected
    r = http.get(f"{agg}/hello/")
    assert r.status_code in (401, 422)
