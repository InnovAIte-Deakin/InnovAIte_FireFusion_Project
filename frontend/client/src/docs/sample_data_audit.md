# FireFusion Frontend - Sample Data Audit Report

## Executive Summary

This audit identifies every location in the frontend codebase where hardcoded, fallback, or mock sample data is currently being used instead of real API endpoints. This report unblocks backend and AI integration by mapping each frontend component to its corresponding mock data structures and recommended API endpoints.

---

## 1. Misinformation Review & Landing Pages

### File: `src/components/misinfo/misinfoData.js`

- **`FALLBACK_INCIDENTS`**:
  - Mock array of active incidents (`inc_east_gippsland`, `inc_grampians`, `inc_yarra`).
  - Contains threat counts, top threats, and flag counts.
  - **Target API**: `GET /api/misinformation/incidents`
- **`FALLBACK_NARRATIVES`**:
  - Mock array of misinformation narratives/claims.
  - Contains severity, incident mapping, headline, post count, platforms, shares, spread status, snippets, confidence level, urgency, and review status.
  - **Target API**: `GET /api/misinformation/narratives`, `GET /api/misinformation/narratives/:id`

---

## 2. Analytics Page

### File: `src/pages/Analytics.jsx`

- **`KPISection`**:
  - Hardcoded array `data` for KPIs: Overall Risk, Active Zones, Misinformation Count, Communities, Alerts Issued.
  - **Target API**: `GET /api/analytics/kpis`
- **`WeatherTimeline`**:
  - Fallback mock data array `fallbackWeather` for temperature, humidity, and wind speed.
  - **Target API**: `GET /api/weather/timeline`
- **`ZoneRiskTable`**:
  - Hardcoded array `data` for active zones.
  - **Target API**: `GET /api/analytics/zones`

---

## 3. Dashboard Page

### File: `src/pages/Dashboard.jsx`

- **`officialUpdates`**:
  - Hardcoded CFA / VicEmergency alerts array.
  - **Target API**: `GET /api/alerts/official`
- **`resources`**:
  - Hardcoded resource deployment counts.
  - **Target API**: `GET /api/resources/status`
