"""Tests for alert subscriptions: validation, storage, baselining and the API.

The unit tests use an in-memory stand-in for Redis and need no running stack.
The integration test at the bottom exercises the API against the real stack
and Redis. See docs/risk-escalation-alerts.md.
"""

import os
from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError


APP_DIR = Path(__file__).resolve().parents[1] / "firefusion-api"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("CACHE_URL", "redis://localhost:6379/0")

from app.config.config import environment
from app.internal.alerting import store as store_module
from app.internal.alerting.models import Region, RegionAssessment
from app.internal.alerting.service import SubscriptionLimitReached, SubscriptionService
from app.internal.alerting.store import SubscriptionStore
from app.internal.alerting.subscriptions import (
    MAX_REGION_VERTICES,
    Subscription,
    SubscriptionCreate,
    validate_webhook_url,
)
from app.routers import alerts


KEY = "test-alerts-key"


# --- an in-memory stand-in for the parts of Redis the store uses ---

class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.queued = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def set(self, key, value):
        self.queued.append(("set", key, value))
        return self

    def sadd(self, key, *members):
        self.queued.append(("sadd", key, *members))
        return self

    def scard(self, key):
        self.queued.append(("scard", key))
        return self

    def delete(self, key):
        self.queued.append(("delete", key))
        return self

    def srem(self, key, *members):
        self.queued.append(("srem", key, *members))
        return self

    async def execute(self):
        results = []
        for op, *args in self.queued:
            results.append(await getattr(self.redis, op)(*args))
        self.queued = []
        return results


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.fail = False

    def _check(self):
        if self.fail:
            raise RedisConnectionError("redis unavailable")

    def pipeline(self, transaction=True):
        self._check()
        return FakePipeline(self)

    async def set(self, key, value):
        self._check()
        self.values[key] = value.encode() if isinstance(value, str) else value
        return True

    async def get(self, key):
        self._check()
        return self.values.get(key)

    async def mget(self, keys):
        self._check()
        return [self.values.get(k) for k in keys]

    async def delete(self, key):
        self._check()
        return 1 if self.values.pop(key, None) is not None else 0

    async def sadd(self, key, *members):
        self._check()
        before = len(self.sets.setdefault(key, set()))
        self.sets[key].update(m.encode() if isinstance(m, str) else m for m in members)
        return len(self.sets[key]) - before

    async def srem(self, key, *members):
        self._check()
        removed = 0
        for m in members:
            m = m.encode() if isinstance(m, str) else m
            if m in self.sets.get(key, set()):
                self.sets[key].discard(m)
                removed += 1
        return removed

    async def scard(self, key):
        self._check()
        return len(self.sets.get(key, set()))

    async def smembers(self, key):
        self._check()
        return set(self.sets.get(key, set()))


class FakeForecast:
    """Stands in for ForecastService: serves a fixed forecast, or fails."""

    def __init__(self, features=None, fail=False):
        self.features = features or []
        self.fail = fail

    async def fetch_predictions(self):
        if self.fail:
            raise RuntimeError("forecast unavailable")
        return {"type": "FeatureCollection", "features": self.features}


def rect(x1, y1, x2, y2):
    return [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]]


def forecast_feature(x1, y1, x2, y2, risk):
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": rect(x1, y1, x2, y2)},
        "properties": {"risk_factor": risk},
    }


def make_service(redis=None, forecast=None, max_subscriptions=500, allow_insecure=False):
    redis = redis or FakeRedis()
    service = SubscriptionService(
        SubscriptionStore(redis),
        forecast or FakeForecast(),
        max_subscriptions=max_subscriptions,
        allow_insecure_webhooks=allow_insecure,
    )
    return service, redis


VALID = {
    "label": "Bairnsdale ops",
    "bbox": [142.0, -38.0, 143.0, -37.0],
    "threshold_risk_factor": 2,
    "webhook_url": "https://ops.example.com/hook",
}


def create(payload=None, **overrides):
    return SubscriptionCreate(**{**(payload or VALID), **overrides})


# --- webhook URL validation (the backend will call these URLs) ---

@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://ops.example.com/hook", id="plain-https"),
        pytest.param("https://ops.example.com:8443/a/b?token=x", id="port-and-query"),
        pytest.param("https://8.8.8.8/hook", id="public-ip-literal"),
    ],
)
def test_acceptable_webhook_urls(url):
    assert validate_webhook_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("http://ops.example.com/hook", id="plain-http"),
        pytest.param("ftp://ops.example.com/hook", id="wrong-scheme"),
        pytest.param("file:///etc/passwd", id="file-scheme"),
        pytest.param("javascript:alert(1)", id="script-scheme"),
        pytest.param("https:///nohost", id="no-host"),
        pytest.param("https://user:pass@ops.example.com/hook", id="credentials"),
        pytest.param("https://localhost/hook", id="localhost"),
        pytest.param("https://app.localhost/hook", id="localhost-subdomain"),
        pytest.param("https://printer.local/hook", id="mdns-name"),
        pytest.param("https://db.internal/hook", id="internal-suffix"),
        pytest.param("https://127.0.0.1/hook", id="loopback"),
        pytest.param("https://10.0.0.5/hook", id="private-10"),
        pytest.param("https://172.16.4.1/hook", id="private-172"),
        pytest.param("https://192.168.1.1/hook", id="private-192"),
        pytest.param("https://169.254.169.254/latest/meta-data", id="cloud-metadata"),
        pytest.param("https://0.0.0.0/hook", id="unspecified"),
        pytest.param("https://[::1]/hook", id="ipv6-loopback"),
        pytest.param("https://[fe80::1]/hook", id="ipv6-link-local"),
        pytest.param("https://[fd00::1]/hook", id="ipv6-unique-local"),
        pytest.param("https://[::ffff:127.0.0.1]/hook", id="ipv4-mapped-loopback"),
        pytest.param("https://2130706433/hook", id="decimal-encoded-127.0.0.1"),
        pytest.param("https://0x7f000001/hook", id="hex-encoded-127.0.0.1"),
        pytest.param("https://127.1/hook", id="short-form-loopback"),
        pytest.param("https://LOCALHOST./hook", id="trailing-dot-and-case"),
        pytest.param("https://" + "a" * 2050 + ".com/hook", id="oversized"),
    ],
)
def test_unsafe_webhook_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_webhook_url(url)


def test_insecure_mode_permits_local_targets_for_development():
    assert validate_webhook_url("http://localhost:9000/hook", allow_insecure=True)
    assert validate_webhook_url("http://10.0.0.5/hook", allow_insecure=True)


def test_insecure_mode_still_rejects_bad_schemes_and_credentials():
    with pytest.raises(ValueError):
        validate_webhook_url("file:///etc/passwd", allow_insecure=True)
    with pytest.raises(ValueError):
        validate_webhook_url("http://user:pw@localhost/hook", allow_insecure=True)


# --- request validation ---

def test_a_bbox_or_a_polygon_is_accepted():
    assert create().to_region().geometry.coordinates[0][0] == [142.0, -38.0]

    polygon = create(
        bbox=None, geometry={"type": "Polygon", "coordinates": rect(1, 1, 2, 2)}
    )
    assert polygon.to_region().geometry.coordinates == rect(1, 1, 2, 2)


def test_exactly_one_region_is_required():
    with pytest.raises(ValidationError):
        create(bbox=None)
    with pytest.raises(ValidationError):
        create(geometry={"type": "Polygon", "coordinates": rect(1, 1, 2, 2)})


def test_at_least_one_channel_is_required():
    with pytest.raises(ValidationError):
        create(webhook_url=None)


def test_email_alone_is_a_valid_channel():
    assert create(webhook_url=None, email="duty.officer@agency.gov.au").email


@pytest.mark.parametrize("email", ["nope", "a@b", "a b@c.com", "@x.com", "a@@b.com"])
def test_malformed_emails_are_rejected(email):
    with pytest.raises(ValidationError):
        create(webhook_url=None, email=email)


@pytest.mark.parametrize("label", ["", "   ", "x" * 101])
def test_bad_labels_are_rejected(label):
    with pytest.raises(ValidationError):
        create(label=label)


@pytest.mark.parametrize("threshold", [0, 6, -1])
def test_threshold_must_be_on_the_risk_scale(threshold):
    with pytest.raises(ValidationError):
        create(threshold_risk_factor=threshold)


def test_an_inverted_bbox_is_rejected():
    with pytest.raises(ValueError):
        create(bbox=[143.0, -38.0, 142.0, -37.0]).to_region()


def test_an_over_detailed_region_is_rejected():
    ring = [[i / 1000, (i % 7) / 1000] for i in range(MAX_REGION_VERTICES + 5)]
    ring.append(ring[0])
    request = create(
        bbox=None, geometry={"type": "Polygon", "coordinates": [ring]}
    )

    with pytest.raises(ValueError, match="vertices"):
        request.to_region()


# --- storage ---

def stored(subscription_id="a", created="2026-01-01T00:00:00+00:00", **kw):
    return Subscription(
        id=subscription_id,
        label=kw.get("label", "x"),
        region=Region.from_bbox(0, 0, 1, 1),
        threshold_risk_factor=2,
        webhook_url="https://ops.example.com/hook",
        created_at=created,
    )


@pytest.mark.asyncio
async def test_a_subscription_round_trips_through_the_store():
    store = SubscriptionStore(FakeRedis())
    original = stored("abc")
    original.baseline = RegionAssessment(risk_factor=3, feature_count=2)

    assert await store.add(original, max_subscriptions=10)

    assert await store.get("abc") == original


@pytest.mark.asyncio
async def test_a_missing_subscription_is_none_and_deleting_it_reports_false():
    store = SubscriptionStore(FakeRedis())

    assert await store.get("nope") is None
    assert await store.delete("nope") is False


@pytest.mark.asyncio
async def test_delete_removes_the_subscription_and_its_index_entry():
    redis = FakeRedis()
    store = SubscriptionStore(redis)
    await store.add(stored("abc"), 10)

    assert await store.delete("abc") is True

    assert await store.get("abc") is None
    assert await store.list() == []
    assert redis.sets[store_module.INDEX_KEY] == set()


@pytest.mark.asyncio
async def test_list_is_oldest_first():
    store = SubscriptionStore(FakeRedis())
    await store.add(stored("b", created="2026-03-01T00:00:00+00:00"), 10)
    await store.add(stored("a", created="2026-05-01T00:00:00+00:00"), 10)
    await store.add(stored("c", created="2026-01-01T00:00:00+00:00"), 10)

    assert [s.id for s in await store.list()] == ["c", "b", "a"]


@pytest.mark.asyncio
async def test_the_cap_is_enforced_and_the_rejected_subscription_leaves_nothing():
    redis = FakeRedis()
    store = SubscriptionStore(redis)
    assert await store.add(stored("a"), max_subscriptions=2)
    assert await store.add(stored("b"), max_subscriptions=2)

    assert await store.add(stored("c"), max_subscriptions=2) is False

    assert sorted(s.id for s in await store.list()) == ["a", "b"]
    assert store_module.subscription_key("c") not in redis.values
    assert await redis.scard(store_module.INDEX_KEY) == 2


@pytest.mark.asyncio
async def test_a_dangling_index_entry_is_dropped_when_listing():
    redis = FakeRedis()
    store = SubscriptionStore(redis)
    await store.add(stored("a"), 10)
    await redis.sadd(store_module.INDEX_KEY, "ghost")  # index says it exists, value gone

    assert [s.id for s in await store.list()] == ["a"]
    assert b"ghost" not in redis.sets[store_module.INDEX_KEY]


@pytest.mark.asyncio
async def test_a_corrupt_stored_value_is_skipped_not_fatal(caplog):
    redis = FakeRedis()
    store = SubscriptionStore(redis)
    await store.add(stored("good"), 10)
    await redis.sadd(store_module.INDEX_KEY, "bad")
    await redis.set(store_module.subscription_key("bad"), "{not json")

    with caplog.at_level("WARNING"):
        result = await store.list()

    assert [s.id for s in result] == ["good"]
    assert any("could not be parsed" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_everything_alerting_writes_is_under_its_own_prefix():
    """Alerting must never touch the forecast cache's keys."""
    redis = FakeRedis()
    await SubscriptionStore(redis).add(stored("a"), 10)

    keys = set(redis.values) | set(redis.sets)

    assert keys and all(k.startswith("alerting:") for k in keys)
    assert "predictions" not in keys and "predictions:generated_at" not in keys


@pytest.mark.asyncio
async def test_redis_failures_propagate_so_the_router_can_report_them():
    redis = FakeRedis()
    redis.fail = True

    with pytest.raises(RedisConnectionError):
        await SubscriptionStore(redis).list()


# --- creating: baselining and safety ---

@pytest.mark.asyncio
async def test_a_new_subscription_is_baselined_against_the_current_forecast():
    forecast = FakeForecast([
        forecast_feature(142.4, -37.6, 142.6, -37.4, risk=2),
        forecast_feature(10, 10, 11, 11, risk=1),  # nowhere near the region
    ])
    service, _ = make_service(forecast=forecast)

    subscription = await service.create(create())

    assert subscription.baseline.risk_factor == 2
    assert subscription.baseline.feature_count == 1


@pytest.mark.asyncio
async def test_no_forecast_means_a_baseline_of_no_known_risk():
    service, _ = make_service(forecast=FakeForecast([]))

    subscription = await service.create(create())

    assert subscription.baseline == RegionAssessment(risk_factor=None, feature_count=0)


@pytest.mark.asyncio
async def test_an_unreadable_forecast_does_not_stop_someone_subscribing(caplog):
    service, _ = make_service(forecast=FakeForecast(fail=True))

    with caplog.at_level("WARNING"):
        subscription = await service.create(create())

    assert subscription.baseline is None
    assert any("no baseline" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_an_unsafe_webhook_is_rejected_before_anything_is_stored():
    service, redis = make_service()

    with pytest.raises(ValueError):
        await service.create(create(webhook_url="https://169.254.169.254/x"))

    assert not redis.values and not redis.sets


@pytest.mark.asyncio
async def test_insecure_webhooks_are_allowed_only_when_configured():
    local = create(webhook_url="http://localhost:9000/hook")

    with pytest.raises(ValueError):
        await make_service()[0].create(local)

    assert (await make_service(allow_insecure=True)[0].create(local)).id


@pytest.mark.asyncio
async def test_the_limit_is_reported():
    service, _ = make_service(max_subscriptions=1)
    await service.create(create())

    with pytest.raises(SubscriptionLimitReached):
        await service.create(create(label="second"))


@pytest.mark.asyncio
async def test_each_subscription_gets_a_distinct_id():
    service, _ = make_service()

    ids = {(await service.create(create(label=f"s{i}"))).id for i in range(5)}

    assert len(ids) == 5


# --- the HTTP API ---

@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(environment, "alerts_api_key", KEY)
    service, redis = make_service()

    app = FastAPI()
    app.include_router(alerts.router)
    app.dependency_overrides[alerts.get_subscription_service] = lambda: service
    return TestClient(app), redis


def auth(key=KEY):
    return {"X-API-Key": key}


def test_the_api_is_disabled_when_no_key_is_configured(monkeypatch):
    monkeypatch.setattr(environment, "alerts_api_key", None)
    app = FastAPI()
    app.include_router(alerts.router)

    for response in (
        TestClient(app).get("/api/alerts/subscriptions", headers=auth()),
        TestClient(app).post("/api/alerts/subscriptions", json=VALID, headers=auth()),
    ):
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-API-Key": "wrong"}, {"X-API-Key": ""}],
    ids=["missing", "wrong", "empty"],
)
def test_every_route_rejects_a_missing_or_wrong_key(api, headers):
    client, _ = api

    responses = [
        client.post("/api/alerts/subscriptions", json=VALID, headers=headers),
        client.get("/api/alerts/subscriptions", headers=headers),
        client.get("/api/alerts/subscriptions/x", headers=headers),
        client.delete("/api/alerts/subscriptions/x", headers=headers),
    ]

    assert [r.status_code for r in responses] == [401, 401, 401, 401]


def test_create_get_list_and_delete(api):
    client, _ = api

    created = client.post("/api/alerts/subscriptions", json=VALID, headers=auth())
    assert created.status_code == 201
    body = created.json()
    assert body["label"] == "Bairnsdale ops"
    assert body["threshold_risk_factor"] == 2
    assert body["baseline"] == {
        "risk_factor": None, "feature_count": 0, "max_fire_probability": None,
    }
    sub_id = body["id"]

    assert client.get(f"/api/alerts/subscriptions/{sub_id}", headers=auth()).json() == body
    assert [s["id"] for s in client.get("/api/alerts/subscriptions", headers=auth()).json()] == [sub_id]

    assert client.delete(f"/api/alerts/subscriptions/{sub_id}", headers=auth()).status_code == 204
    assert client.get(f"/api/alerts/subscriptions/{sub_id}", headers=auth()).status_code == 404
    assert client.get("/api/alerts/subscriptions", headers=auth()).json() == []


def test_unknown_ids_are_404(api):
    client, _ = api

    assert client.get("/api/alerts/subscriptions/nope", headers=auth()).status_code == 404
    assert client.delete("/api/alerts/subscriptions/nope", headers=auth()).status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"webhook_url": "https://169.254.169.254/x"}, id="ssrf-target"),
        pytest.param({"webhook_url": "http://ops.example.com/x"}, id="plain-http"),
        pytest.param({"bbox": None}, id="no-region"),
        pytest.param({"threshold_risk_factor": 9}, id="bad-threshold"),
        pytest.param({"bbox": [143.0, -38.0, 142.0, -37.0]}, id="inverted-bbox"),
        pytest.param({"webhook_url": None}, id="no-channel"),
    ],
)
def test_unacceptable_requests_are_422_and_store_nothing(api, overrides):
    client, redis = api

    response = client.post(
        "/api/alerts/subscriptions", json={**VALID, **overrides}, headers=auth()
    )

    assert response.status_code == 422
    assert not redis.values and not redis.sets


def test_the_subscription_limit_is_409(monkeypatch):
    monkeypatch.setattr(environment, "alerts_api_key", KEY)
    service, _ = make_service(max_subscriptions=1)
    app = FastAPI()
    app.include_router(alerts.router)
    app.dependency_overrides[alerts.get_subscription_service] = lambda: service
    client = TestClient(app)

    assert client.post("/api/alerts/subscriptions", json=VALID, headers=auth()).status_code == 201
    second = client.post("/api/alerts/subscriptions", json=VALID, headers=auth())

    assert second.status_code == 409


def test_a_redis_outage_is_503_not_a_crash(api):
    client, redis = api
    redis.fail = True

    responses = [
        client.post("/api/alerts/subscriptions", json=VALID, headers=auth()),
        client.get("/api/alerts/subscriptions", headers=auth()),
        client.get("/api/alerts/subscriptions/x", headers=auth()),
        client.delete("/api/alerts/subscriptions/x", headers=auth()),
    ]

    assert [r.status_code for r in responses] == [503, 503, 503, 503]


def test_the_alerts_routes_are_registered_on_the_real_app(monkeypatch):
    monkeypatch.setenv("BROKER_URL", "amqp://localhost/unused")
    monkeypatch.setenv("DB_URL", "postgresql://localhost/unused")
    from app import main

    paths = {route.path for route in main.app.routes}

    assert "/api/alerts/subscriptions" in paths
    assert "/api/alerts/subscriptions/{subscription_id}" in paths
    # and the existing routes are still there
    assert "/api/bushfire-forecast" in paths


# --- integration: the real stack and real Redis ---

@pytest.mark.integration
def test_subscriptions_work_end_to_end_against_the_running_stack(ff, http, prediction_cache):
    key = os.getenv("ALERTS_API_KEY", "local-development-key")
    headers = {"X-API-Key": key}
    base = f"{ff}/api/alerts/subscriptions"

    assert http.post(base, json=VALID).status_code == 401
    assert http.get(base, headers={"X-API-Key": "wrong"}).status_code == 401

    # A polygon-shaped forecast written straight to the forecast cache, so the
    # subscription has something real to baseline against.
    import json as _json
    prediction_cache.set("predictions", _json.dumps({
        "type": "FeatureCollection",
        "features": [forecast_feature(142.4, -37.6, 142.6, -37.4, risk=2)],
    }))

    created = http.post(base, json=VALID, headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    sub_id = body["id"]
    try:
        assert body["baseline"]["risk_factor"] == 2

        assert http.get(f"{base}/{sub_id}", headers=headers).json()["id"] == sub_id
        assert sub_id in [s["id"] for s in http.get(base, headers=headers).json()]

        rejected = http.post(
            base, json={**VALID, "webhook_url": "https://169.254.169.254/x"}, headers=headers
        )
        assert rejected.status_code == 422

        # It persisted in Redis under its own prefix and left the forecast alone.
        assert prediction_cache.exists(f"alerting:subscription:{sub_id}") == 1
        assert prediction_cache.get("predictions") is not None
    finally:
        http.delete(f"{base}/{sub_id}", headers=headers)

    assert http.get(f"{base}/{sub_id}", headers=headers).status_code == 404
    assert prediction_cache.exists(f"alerting:subscription:{sub_id}") == 0
