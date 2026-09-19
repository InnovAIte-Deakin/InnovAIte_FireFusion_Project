# Risk Escalation Alerts

**Status:** Phase 1 (decision logic) and phase 2 (subscriptions API) implemented. Wiring to live forecasts and delivery are not built yet.
**Stream:** Back-end only.

## The gap

FireFusion shows the current risk picture, and (with forecast history) can
replay past ones. What it cannot do is *tell* anyone. A responder has to be
looking at the map at the moment risk rises in the area they care about.

This feature lets a subscriber define a region and a severity threshold, and
be notified when a new forecast makes that region worse.

## Boundaries: what this does not touch

This is built to add to the backend without changing anything other streams own.

- **Data Engineering.** No DE table is read, altered or referenced. A region is
  supplied by the subscriber, not derived from `Location_Registry` or any other
  DE data. Alerting never goes through the aggregator or its read-only DE role.
- **AI Modelling.** No change to the forecast contract. Alerting consumes the
  same `FeatureCollection` the API already serves.
- **Front-end.** No existing endpoint or response shape changes. Alerts are
  delivered out of band (webhook, email); the map is unaffected.
- **Existing back-end code.** Phase 1 adds a new package,
  `app/internal/alerting/`, and edits no existing file. It adds no dependency:
  polygon intersection is implemented in pure Python rather than adding a
  geometry library to `requirements.txt`.
- **Database.** None. Subscriptions are stored in Redis under their own
  `alerting:` key prefix, so there is no schema, no migration and no table of
  any stream is involved. The prefix keeps them apart from the forecast cache
  keys (`predictions`, `predictions:generated_at`), and a test asserts every key
  alerting writes is under it.
- **Shared files.** Phase 2 makes small additive edits to three shared files:
  three settings in `config.py`, one router registration in `main.py`, and in
  `docker-compose.yaml` an `ALERTS_API_KEY` variable and append-only persistence
  for the Redis container (see [Persistence](#persistence)).

## How a decision is made

For each rule (a region plus a threshold) and each new forecast:

1. **Assess the region.** Find the forecast polygons that touch the region. The
   region's risk is the *most severe* (lowest `risk_factor`) among them. The
   worst is used rather than an average on purpose: one extreme polygon inside
   the region is what a responder needs to hear about, however mild the rest is.
   `risk_factor` follows the Fire Risk Map convention: 1 is most severe, 5 least.
2. **Compare with the previous assessment** for the same region.
3. **Decide:**

| Previous | Now | Threshold met? | Result |
|---|---|---|---|
| below threshold, or no risk | at or beyond threshold | yes | `threshold_crossed` |
| at or beyond threshold | more severe | yes | `escalated` |
| at or beyond threshold | same | yes | nothing (already told) |
| any | less severe | - | nothing (easing is not alerted) |
| any | below threshold | no | nothing |

The threshold is inclusive: `threshold_risk_factor = 2` means "tell me at 2
(high) or 1 (extreme)".

**Design choices that lean toward alerting**, because a missed alert is worse
than an extra one for an emergency tool:

- A polygon that only touches the region's boundary counts as affecting it.
- With no previous assessment, a forecast already at or beyond the threshold
  alerts.

**Callers must pass only fresh forecasts.** Alerting on a stale forecast would
present old information as news. Freshness is already classified by
`meta.status` (see `fire-risk-map-graceful-degradation.md`).

## Known limitation: flapping

The detector is stateless, so risk oscillating around the threshold
(`4, 2, 4, 2`) alerts each time it crosses. Suppressing that needs stored state
(a cooldown per subscription), so it belongs to the delivery layer, not the
decision. A test documents the current behaviour so the gap is explicit.

## Subscriptions API (phase 2)

All routes need the header `X-API-Key`. The API **fails closed**: with
`ALERTS_API_KEY` unset it returns `503 Alerting is not configured` rather than
being open, because it decides who is told about a fire. It is for agency
systems, not browsers; the service's CORS policy already allows only `GET`, so a
browser on another origin cannot call it.

| Route | Purpose |
|---|---|
| `POST /api/alerts/subscriptions` | Create. `201` with the stored subscription |
| `GET /api/alerts/subscriptions` | List, oldest first |
| `GET /api/alerts/subscriptions/{id}` | Read one. `404` if unknown |
| `DELETE /api/alerts/subscriptions/{id}` | Remove. `204`, or `404` if unknown |

Errors: `401` bad or missing key, `409` subscription limit reached, `422` an
invalid or unacceptable request, `503` Redis unavailable or alerting not
configured.

```json
POST /api/alerts/subscriptions
{
  "label": "Gippsland duty officer",
  "bbox": [142.0, -38.0, 143.0, -37.0],
  "threshold_risk_factor": 2,
  "webhook_url": "https://ops.example.com/hook",
  "email": "duty@agency.gov.au"
}
```

- **Region:** a `bbox` (`[min_lon, min_lat, max_lon, max_lat]`) or a GeoJSON
  `geometry` polygon, exactly one. Polygons are limited to 500 vertices.
- **`threshold_risk_factor`:** alert at this risk or worse; `risk_factor` 1 is
  most severe, 5 least.
- **Channels:** at least one of `webhook_url` and `email`. Delivery is a later
  phase; they are validated and stored now.
- **Baseline:** on creation the subscription records what the current forecast
  shows over its region, so the first evaluation only alerts on change from
  there, not on risk that already existed. If the forecast cannot be read the
  baseline is empty and the first evaluation may alert, which errs toward
  telling someone.

### Webhook safety

A subscriber supplies a URL the backend will later call, which is a server-side
request forgery risk: a caller could aim the backend at cloud metadata endpoints
or internal services. Creation rejects anything other than `https`, embedded
credentials, `localhost` and internal-looking names (`.local`, `.internal`, ...),
private, loopback, link-local, multicast, reserved and unspecified addresses
(including IPv6 and IPv4-mapped forms), and encoded IPs such as
`https://2130706433/` or `https://0x7f000001/`.

This cannot catch a public hostname that *resolves* to a private address. **The
delivery phase must re-check the resolved address at send time**, and must not
follow redirects to a different host.
`ALERTS_ALLOW_INSECURE_WEBHOOKS=true` relaxes the scheme and address rules for
local development only.

### Configuration

| Variable | Default | Notes |
|---|---|---|
| `ALERTS_API_KEY` | unset (API disabled) | `docker-compose.yaml` defaults it to `local-development-key` for local use only; set a real secret when deployed |
| `ALERTS_MAX_SUBSCRIPTIONS` | `500` | Enforced atomically, so concurrent creates cannot exceed it |
| `ALERTS_ALLOW_INSECURE_WEBHOOKS` | `false` | Development only |

### Persistence

Subscriptions cannot be regenerated if lost, unlike the forecast cache, and Redis
by default snapshots on a schedule that can lose up to an hour of writes on a
crash. The compose Redis container therefore runs with `--appendonly yes`.
**Any deployed Redis must have append-only persistence enabled too**, or
subscriptions can be lost. Verified: a subscription survives a restart of the
Redis container. Note the first request after a Redis restart returns `503`
before the connection recovers; the existing forecast endpoint behaves
identically, because they share the same Redis client.

## Phases

1. **Decision logic (done).** Region model, polygon intersection, region
   assessment, escalation decision. Pure, no I/O, fully unit-tested.
2. **Subscriptions (done).** A keyed API to create, list, read and delete
   subscriptions, stored in Redis; validation including webhook safety; baselining
   a new subscription so it is not alerted about a risk that already existed.
3. **Wiring and delivery.** Evaluate subscriptions when a prediction is stored,
   best-effort so a failure here can never affect live forecast delivery (the
   same rule as the history write). Deliver through RabbitMQ workers with
   webhook and email channels, retries with backoff, a dead-letter queue,
   idempotency and a per-subscription cooldown.
4. **Audit.** Record each alert and its delivery outcome.

## Tests

`tests/test_alert_subscriptions.py` covers webhook validation (including 25
rejected forms), request validation, the Redis store (round trip, ordering,
cap enforcement and rollback, dangling and corrupt entries, key prefix), baselining,
and the API (auth, fail-closed, CRUD, 422/409/503 mapping), using an in-memory
stand-in for Redis, plus one integration test against the real stack. It was
checked by deliberately breaking eleven behaviours (each SSRF rule, the auth
check, failing open, the cap, region and channel rules, the key prefix) to
confirm each is caught.

`tests/test_risk_escalation.py` needs no database, broker or running stack. It
covers segment and polygon intersection (including concave shapes, holes,
touching edges and corners, and nesting), a randomized check of the geometry
against the analytic answer for rectangles, region and rule validation, region
assessment, and the full decision table. The tests were also checked by
deliberately breaking the code in six places (the nesting check, endpoint
touching, holes, the alert-on-unchanged rule, the threshold boundary, and
worst-versus-least-severe) to confirm each is caught.
