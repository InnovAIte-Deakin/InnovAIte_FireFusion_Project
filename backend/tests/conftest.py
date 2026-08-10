"""Shared fixtures for the backend test suite.

Integration tests hit the running stack over HTTP. If a service is not
reachable they skip with a clear message instead of failing, so you can run
`pytest` without the stack up and still get the unit tests.
"""
import os
import httpx
import pytest

FF_URL = os.getenv("FF_URL", "http://localhost:8080")
MODEL_URL = os.getenv("MODEL_URL", "http://localhost:8081")
AGG_URL = os.getenv("AGG_URL", "http://localhost:8082")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: hits the running backend stack over HTTP"
    )


def _reachable(url):
    try:
        httpx.get(url, timeout=2.0)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def http():
    with httpx.Client(timeout=10.0) as client:
        yield client


@pytest.fixture
def ff():
    if not _reachable(f"{FF_URL}/openapi.json"):
        pytest.skip(
            f"firefusion-api not reachable at {FF_URL}. "
            "Start the stack: docker compose --profile default up -d"
        )
    return FF_URL


@pytest.fixture
def model():
    if not _reachable(f"{MODEL_URL}/model/hello"):
        pytest.skip(f"model-api not reachable at {MODEL_URL}.")
    return MODEL_URL


@pytest.fixture
def agg():
    if not _reachable(f"{AGG_URL}/openapi.json"):
        pytest.skip(f"aggregator-api not reachable at {AGG_URL}.")
    return AGG_URL
