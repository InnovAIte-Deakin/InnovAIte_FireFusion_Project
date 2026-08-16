# Fire Risk Map Backend Integration

**Status:** Sprint 1 integration work in progress - Ready for Review  
**Owner:** Timothy Trevett
**Reviewer:** Whole Backend Team*   
**Streams affected:** Back-end, Front-end, AI Modelling, Data Engineering  
**Purpose:** Connect the existing Fire Risk Map API path to the newer Data Engineering and AI Modelling services without replacing the existing Frontend-facing contract.

---

## 1. Integration goal

The Backend integration is being prepared around the following flow:

```text
Data Engineering
    ↓
Aggregator API
    ↓
FireFusion API
    ↓
AI Modelling
    ↓
FireFusion API
    ↓
GET /api/bushfire-forecast
    ↓
Frontend Fire Risk Map
```

The aim is to keep the existing Frontend boundary stable while allowing Backend to retrieve prepared source data, build the AI request, call the AI forecast API, and return the resulting risk polygons to the map.

This work is intended to complement the separate Fire Risk Map API contract work rather than replace it.

---

## 2. Confirmed cross-stream contract

### Frontend

Frontend has confirmed that, for Sprint 1:

- the Fire Risk Map expects a GeoJSON `FeatureCollection` containing Polygon features;
- `properties.risk_factor` is sufficient for the map;
- the risk convention is `1 = extreme` through to `5 = very low`;
- `GET /api/bushfire-forecast` is the required working path;
- `/api/ws` can remain optional for Sprint 1.

### AI Modelling

AI Modelling has confirmed that:

- Backend calls `POST /predict/bushfire/forecast`;
- the response is a GeoJSON `FeatureCollection` containing prediction polygons;
- `risk_factor` is already converted to the Frontend convention, so Backend must not convert it again;
- forecast timestamps are included in the current response;
- the current request contains 30 historical timesteps per grid cell;
- the request contains `feature_names`, and AI validates the supplied feature names/order during inference;
- the overall request structure is expected to remain stable, although additional input features may be added later, including live fire-event data from Data Engineering.

Current AI input feature names are:

```text
era5land_temperature_2m_c
era5_dewpoint_temperature_2m_c
era5_total_precipitation
era5_u_component_of_wind_10m
era5_v_component_of_wind_10m
era5land_surface_solar_radiation_downwards
era5land_skin_temperature_c
```

---

## 3. Backend files added or changed

### `firefusion-api/app/internal/clients/aggregator_client.py`

Introduces a REST client for communication from `firefusion-api` to `aggregator-api`.

Current responsibilities:

- use the configured Aggregator service URL;
- request recent Data Engineering fire incident records;
- keep inter-service HTTP logic out of ForecastService and API routes;
- raise HTTP errors instead of passing failed responses further into the integration pipeline.

Current internal route:

```text
GET /internal/data/fire-incidents
```

---

### `firefusion-api/app/internal/clients/ai_modelling_client.py`

Introduces the REST boundary between Backend and the AI Modelling FastAPI service.

Current responsibilities:

- call `POST /predict/bushfire/forecast`;
- return the AI GeoJSON response to Backend;
- expose a `/health` check for AI service connectivity;
- keep the AI service URL configurable rather than hard-coded into business logic.

The current AI response includes fields such as `risk_factor`, `fire_probability`, `is_burning_predicted`, `forecast_timestamps`, `grid_row` and `grid_col`.

Backend should preserve AI's `risk_factor` value without applying a second risk conversion.

---

### `firefusion-api/app/internal/models/ai_forecast.py`

Defines the Backend representation of the AI forecast request.

The request is a GeoJSON `FeatureCollection`, where each grid cell contains:

- Polygon geometry;
- ordered historical observations;
- timestamps;
- `grid_row`;
- `grid_col`.

The current AI request uses 30 historical timesteps. The number of feature values should remain tied to the supplied `feature_names` rather than being permanently fixed, because AI Modelling may add additional model inputs later.

---

### `firefusion-api/app/internal/services/ai_request_builder.py`

Provides the transformation boundary between Data Engineering records and the AI Modelling request.

Its intended responsibilities are:

1. group source records by location/grid cell;
2. order records chronologically;
3. select the required 30 historical timesteps;
4. map Data Engineering fields into the exact AI `feature_names` order;
5. build the observation arrays and timestamps;
6. attach the correct geometry and grid identifiers;
7. return the final AI GeoJSON request.

The exact Data Engineering field-to-feature and grid mappings are still the main outstanding dependency before this component can be considered complete.

Missing or unknown values should fail clearly rather than being invented or silently substituted.

---

### `firefusion-api/app/internal/services/forecast_normaliser.py`

Provides the AI response → Frontend contract transformation.

For Sprint 1 the normalisation can remain intentionally small:

- validate that the AI response is a GeoJSON `FeatureCollection`;
- retain the Polygon geometry returned by AI;
- read the current forecast horizon value from `risk_factor`;
- validate that the value is within `1..5`;
- expose that same value to Frontend without converting the scale.

Frontend has confirmed that `risk_factor` alone is sufficient for the current Fire Risk Map integration, even though AI may return additional prediction metadata.

---

### `firefusion-api/app/internal/services/forecast_service.py`

A shared `store_prediction()` path has been introduced so predictions can eventually enter Backend through either:

- the inherited RabbitMQ prediction flow; or
- the newer REST-based AI Modelling integration.

The shared path validates the GeoJSON payload, stores the latest prediction in Redis, and broadcasts it to WebSocket clients.

This avoids duplicating caching and WebSocket behaviour between old and new prediction sources.

`forecast_service.py` also overlaps with separate Fire Risk Map API contract work, so final integration of those changes should be coordinated after the related PR is merged.

---

### `aggregator-api/app/internal/models/fire_incident_v2.py`

Adds a model for the newer Data Engineering fire incident structure while retaining the existing legacy `FireEvent` model.

The new model includes:

- Data Engineering identifiers (`incident_id`, `location_id`, `time_id`);
- original coordinates;
- NASA FIRMS metadata where available;
- raw measurements such as brightness and FRP;
- joined location information;
- joined timestamp/season information.

Keeping this separate allows the newer DE schema to be introduced without immediately removing the inherited `fire_events_full` pathway.

---

### `aggregator-api/app/internal/repositories/aggregator_repository.py`

Adds a second repository query for the newer Data Engineering schema.

The new query joins:

```text
Fire_Incident_Record
    ↓ location_id
Location_Registry

Fire_Incident_Record
    ↓ time_id
Time_Registry
```

The existing `fire_events_full` query is deliberately retained so the current Backend path is not removed while the newer integration is being established.

---

### `aggregator-api/app/routers/fire_data.py`

Adds an internal Backend endpoint:

```text
GET /internal/data/fire-incidents?days=<n>
```

This route is intended for service-to-service use and is not a Frontend endpoint.

It exposes fire incident records from the newer Data Engineering schema through `aggregator-api` so `firefusion-api` does not need to directly own Data Engineering database queries.

---

## 4. Current integration boundary

The following parts are now defined:

```text
Aggregator API
    ↓
AggregatorClient
    ↓
AIRequestBuilder
    ↓
AIModellingClient
    ↓
POST /predict/bushfire/forecast
    ↓
ForecastNormaliser
    ↓
ForecastService / existing Fire Risk Map API path
```

The AI request and response structures are now known. Frontend's minimum output contract is also confirmed.

The remaining live-data dependency is primarily the Data Engineering → AI input mapping.

---

## 5. Remaining Data Engineering information required

Before the live request builder can be finalised, Backend still needs confirmation of:

1. which Supabase tables/columns supply each of the seven current AI input features;
2. whether at least 30 chronological observations per grid cell are available for those features;
3. how Data Engineering location/grid records map to the AI request's `grid_row`, `grid_col` and Polygon geometry;
4. the intended Backend access path to the Sprint 1 source data, including the database/schema that should be treated as the source of truth.

No missing model feature should be approximated from an unrelated field without agreement from Data Engineering and AI Modelling.

---

## 6. Known local limitation

The newer Data Engineering query has been reached successfully through the Aggregator API, but the current local Docker PostgreSQL database does not contain the newer `Fire_Incident_Record`, `Location_Registry` and `Time_Registry` tables.

This means the new internal route cannot yet be fully exercised against the local database. The code is intended to align with the Data Engineering/Supabase schema once the final database access path is confirmed.

---

## 7. Sprint 1 completion path

The intended final validation is:

```text
Data Engineering records
    ↓
Aggregator API
    ↓
AI-compatible 30-step request
    ↓
POST /predict/bushfire/forecast
    ↓
AI GeoJSON prediction
    ↓
Backend normalisation
    ↓
GET /api/bushfire-forecast
    ↓
Frontend renders Fire Risk Map polygons using risk_factor
```

If the live DE → AI mapping cannot be completed within Sprint 1, the same Backend/Frontend contract can still be validated using the confirmed AI request/response fixture while the live Data Engineering mapping remains a documented integration dependency.

---

## 8. Key design decisions

- Keep `GET /api/bushfire-forecast` as the stable Frontend-facing endpoint.
- Keep `/api/ws` available but optional for Sprint 1.
- Keep Frontend isolated from Aggregator API and AI Modelling API details.
- Use REST for direct cross-stream integration.
- Preserve the existing RabbitMQ prediction path while introducing the AI REST path.
- Do not recalculate AI's `risk_factor`; AI already returns the Frontend-compatible `1..5` value.
- Keep AI input feature handling flexible because the feature list may grow later.
- Keep the legacy Backend data path available while the newer Data Engineering schema is introduced.
- Do not fabricate missing DE → AI feature mappings; fail clearly until the correct mapping is available.
