# Fire Risk Map API Contract (Backend to Front-end)

**Status:** Draft for review — revision 2
**Author:** Arsh Dang
**Reviewer:** Viet Quang Nguyen
**Streams affected:** Back-end (producer), Front-end (consumer)
**Sprint 1 goal:** Goals 2 and 3 — stable APIs for integration, and one end-to-end integration.

## Scope

This document defines **only the Back-end to Front-end boundary** for the Fire Risk
Map: the single endpoint Front-end calls, and the shape of what it gets back.

It deliberately does **not** define the upstream flow. The Data Engineering to
Back-end to AI Modelling input contract (which Supabase tables feed the model, the
grid and timestamp mapping, and the `POST /predict/bushfire/forecast` request format)
is being worked through separately and tracked in PR #218.

The value of splitting them is that the Front-end boundary can be locked now, while
the upstream pipeline is still being resolved. Front-end builds against this document
and is unaffected by changes behind it.

---

## 1. Endpoint

```
GET /api/bushfire-forecast
```

Served by **firefusion-api** (port 8080). This is the only endpoint Front-end needs
for the Fire Risk Map. Front-end does not call model-api or aggregator-api directly.

No request parameters in Sprint 1. Filtering (by region or time window) is out of
scope and can be added later without breaking this contract.

### Optional live updates

```
WS /api/ws
```

The existing WebSocket pushes the same `FeatureCollection` payload when a new
prediction arrives. Front-end may use it for live refresh, but the Fire Risk Map must
work correctly using the REST endpoint alone.

---

## 2. Response schema

`200 OK`, `Content-Type: application/json`. The body is a GeoJSON
**FeatureCollection**; each feature is a polygon carrying a risk rating.

```jsonc
{
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
          [142.1560, -37.5600]
        ]]
      },
      "properties": {
        "risk_factor": 2,
        "fire_probability": 0.78
      }
    }
  ]
}
```

### Field definitions

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string | yes | Always `"FeatureCollection"` |
| `features` | array | yes | May be empty (`[]`) — see section 4 |
| `features[].type` | string | yes | Always `"Feature"` |
| `features[].geometry.type` | string | yes | `"Polygon"` in Sprint 1 |
| `features[].geometry.coordinates` | array | yes | GeoJSON polygon rings, `[longitude, latitude]` order, first and last position identical |
| `features[].properties.risk_factor` | integer | yes | `1`–`5`. **See the scale below — 1 is the most severe.** |
| `features[].properties.fire_probability` | number | optional | Model confidence/probability, `0.0`–`1.0`. Present when the model supplies it; Front-end must tolerate its absence. |

### `risk_factor` scale

Confirmed with AI Modelling. The Front-end value is the **inverse** of the model's
internal `risk_levels`, so **1 is the most severe**, not the least:

| AI internal `risk_levels` | Front-end `risk_factor` | Meaning |
|---|---|---|
| 4 | **1** | High / extreme |
| 3 | **2** | Medium-high |
| 2 | **3** | Medium |
| 1 | **4** | Medium-low |
| 0 | **5** | Low |

The backend serves the Front-end convention. Front-end does not need to know the
model's internal scale.

### Notes for Front-end

- Coordinate order is **`[longitude, latitude]`**, per the GeoJSON standard. Some map
  libraries (including Leaflet's raw `L.polygon`) expect `[lat, lng]` — check before
  rendering.
- Drive the colour ramp from `risk_factor`, remembering that **low numbers are high
  risk**. The backend does not send colours.
- `fire_probability` is available where the model provides it, for example as an
  opacity or a detail-panel value. Treat it as optional.

---

## 3. Data sources behind the endpoint

The response shape is identical regardless of source, so Front-end never needs to
know which is in use:

1. **Live prediction (target for Sprint 1).** A prediction is produced upstream, the
   backend caches it and serves it here.
2. **Fallback sample data (planned follow-up).** If no live prediction is available,
   the backend serves an agreed sample `FeatureCollection`. **Not implemented yet** —
   the agreed fallback dataset is still to be confirmed with AI Modelling, so today
   the no-data path returns an empty `FeatureCollection` (section 4). Tracked as a
   follow-up task rather than blocking this contract.

---

## 4. Behaviour when data is unavailable

**This is a change from the original behaviour.** The endpoint previously returned
`null` when the prediction cache was empty. A bare `null` is not valid GeoJSON and
would break a map client expecting a `FeatureCollection`.

| Situation | Status | Body |
|---|---|---|
| Live prediction available | `200` | `FeatureCollection` with features |
| No live prediction, fallback available (planned) | `200` | `FeatureCollection` from sample data |
| No data at all | `200` | `{"type": "FeatureCollection", "features": []}` |
| Backend or dependency failure | `503` | `{"detail": "Forecast data temporarily unavailable"}` |

The empty `FeatureCollection` lets the map render cleanly with no polygons instead of
erroring. Front-end should handle three cases: features present, features empty, and
a non-200 response.

---

## 5. Confirmed and open points

Confirmed:

- **`risk_factor` is 1–5 with 1 most severe**, the inverse of the model's internal
  scale (AI Modelling).
- **`risk_factor` alone is sufficient for the Sprint 1 map**, served through
  `GET /api/bushfire-forecast` (Front-end).

Still open:

| # | Question | Who decides |
|---|---|---|
| 1 | Will `fire_probability` be present on every feature, or only some? | AI Modelling |
| 2 | Which sample dataset becomes the agreed fallback | AI Modelling and Back-end |
| 3 | Does Front-end want the WebSocket for live refresh in Sprint 1, or REST only? | Front-end |

---

## 6. Acceptance criteria

- `GET /api/bushfire-forecast` returns a valid `FeatureCollection` matching this
  schema in all situations in section 4.
- `risk_factor` values are integers in `1`–`5` on the Front-end convention.
- The endpoint is documented in the published Swagger/OpenAPI output.
- Automated tests cover a known-good `200` response, the empty-data case, and the
  `503` failure path.
- The Front-end Fire Risk Map renders live data retrieved from this endpoint.

---

## 7. Related work

- **PR #218** (Tim Trevett) — the wider cross-stream integration: Data Engineering
  models and Aggregator routes, the AI Modelling REST client for
  `POST /predict/bushfire/forecast`, and a shared `store_prediction()` path so the
  RabbitMQ and REST flows share validation, caching and WebSocket broadcast. Changes
  to `forecast_service.py` need coordinating across both branches before merge.