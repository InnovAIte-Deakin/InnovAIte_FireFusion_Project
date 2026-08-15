# Fire Risk Map API Contract

**Status:** Draft for review
**Owners:** Arsh Dang, Justice Tran, Zehong Li
**Reviewer:** Viet Quang Nguyen
**Streams affected:** Back-end, Front-end, AI Modelling
**Sprint 1 goal:** Goals 2 and 3 — stable APIs for integration, and one end-to-end integration.

The purpose of this document is to fix one interface so Front-end, Back-end and AI
Modelling all build against the same data format, whether the response comes from a
live model prediction or from fallback sample data.

---

## 1. Endpoint

```
GET /api/bushfire-forecast
```

Served by **firefusion-api** (port 8080). This is the only endpoint Front-end needs
for the Fire Risk Map. Front-end does not call model-api or aggregator-api directly.

No request parameters in Sprint 1. Filtering (by region, time window) is out of scope
and can be added later without breaking this contract.

### Optional live updates

```
WS /api/ws
```

The existing WebSocket pushes the same `FeatureCollection` payload when a new
prediction arrives. Front-end may connect to it for live refresh, but the Fire Risk
Map must work correctly using the REST endpoint alone.

---

## 2. Response schema

`200 OK`, `Content-Type: application/json`.

The body is a GeoJSON **FeatureCollection**. Each feature is a polygon with a risk
rating.

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
        "risk_factor": 3
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
| `features[].properties.risk_factor` | integer | yes | `0`–`5`, where 0 is lowest risk and 5 is highest |

### Notes for Front-end

- Coordinate order is **`[longitude, latitude]`**, per the GeoJSON standard. Most map
  libraries expect this, but some (including Leaflet's raw `L.polygon`) expect
  `[lat, lng]` — check before rendering.
- `risk_factor` is the value to drive the colour scale. Agree the colour ramp for
  0–5 on the Front-end side; the backend does not send colours.
- This matches the existing Pydantic model in `model-api/app/models/geojson_model.py`,
  so it is already what the model side produces.

---

## 3. Data sources behind the endpoint

The response is identical in shape regardless of source, so Front-end never needs to
know which is in use:

1. **Live prediction (preferred).** AI Modelling publishes a prediction; the backend
   caches it and serves it.
2. **Fallback sample data.** If no live prediction is available, the backend serves
   an agreed sample `FeatureCollection` (the existing files in
   `model-api/app/data/geojson_data-*.json` are the reference format).

Swapping from fallback to live must not change the contract.

---

## 4. Behaviour when data is unavailable

**This is a change from current behaviour and needs agreement.**

Today `/api/bushfire-forecast` returns `null` when the prediction cache is empty
(see `ForecastService.fetch_predictions`). A bare `null` is not valid GeoJSON and will
break a map client that expects a `FeatureCollection`.

Proposed behaviour for Sprint 1:

| Situation | Status | Body |
|---|---|---|
| Live prediction available | `200` | `FeatureCollection` with features |
| No live prediction, fallback enabled | `200` | `FeatureCollection` from sample data |
| No data at all | `200` | `{"type": "FeatureCollection", "features": []}` |
| Backend or dependency failure | `503` | `{"detail": "Forecast data temporarily unavailable"}` |

The empty `FeatureCollection` lets the map render cleanly with no polygons instead of
erroring. Front-end should handle: features present, features empty, and a non-200
response.

---

## 5. Open points to confirm

| # | Question | Who decides |
|---|---|---|
| 1 | Is the `risk_factor` 0–5 integer scale correct, or does AI Modelling intend a continuous score? | AI Modelling |
| 2 | Does the Fire Risk Map need any field beyond `risk_factor` (for example a timestamp, region name, or confidence)? | Front-end |
| 3 | Agreement on the empty-`FeatureCollection` and `503` behaviour in section 4 | All three streams |
| 4 | Will Front-end use the WebSocket for live refresh in Sprint 1, or REST only? | Front-end |
| 5 | Which sample dataset is the agreed fallback | Back-end and AI Modelling |

---

## 6. Acceptance criteria

The contract is satisfied when:

- `GET /api/bushfire-forecast` returns a valid `FeatureCollection` matching the schema
  above, in all three data situations from section 4.
- The endpoint is documented in the published Swagger/OpenAPI output.
- Automated tests cover success, empty-data and unavailable-dependency cases.
- The Front-end Fire Risk Map renders live data retrieved from this endpoint.
