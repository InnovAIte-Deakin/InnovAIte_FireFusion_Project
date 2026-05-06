# FireFusion API

Bushfire risk forecast API serving GeoJSON predictions over REST and WebSocket.

## Endpoints

`GET /api/bushfire-forecast`

Returns the current forecast as a GeoJSON `FeatureCollection`.

`WebSocket /api/ws`

Persistent connection for real-time forecast pushes. API is push only and no client messages expected. Broadcasts the same `FeatureCollection` payload as the REST endpoint when new predictions are broadcasted.

## Response Schema

Both endpoints use the same GeoJSON payload:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lng, lat], ...]]
      },
      "properties": {
        "risk_factor": 3
      }
    }
  ]
}
```

## WebSocket Lifecycle

| Event | Behaviour |
|---|---|
| Connect | Client registered with connection manager |
| Disconnect | Client removed; no further messages sent |
