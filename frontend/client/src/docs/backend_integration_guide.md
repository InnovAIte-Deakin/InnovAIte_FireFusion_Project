# Backend & AI Integration Guide

This guide details how real API services connect to the Misinformation Review & Analytics frontend components.

## API Service Mapping

1. **Narratives Endpoint**: `GET /api/misinformation/narratives`
   - Maps to `normalizeNarrative` helper in `misinfoData.js`.
   - Requires `confidenceLevel` (0-100), `urgency` ("Immediate" | "High" | "Moderate"), and `reviewStatus`.

2. **Incidents Endpoint**: `GET /api/misinformation/incidents`
   - Maps to `normalizeIncident` helper in `misinfoData.js`.

3. **Bushfire Forecast GeoJSON**: `GET /api/bushfire-forecast`
   - Rendered by `FireRiskMap.tsx` with automatic fallback to sample GeoJSON features if offline.
