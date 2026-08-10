# Victorian Bushfire Data Pipeline — Complete Overview
Integrated satellite, ground-truth, and unified datasets for fire forecasting and risk modeling.

---

## Overview

This pipeline produces three complementary datasets from NASA satellite fire detections and official Australian bushfire records:

1. **Satellite Thermal Fire Detection Data** – Gridded, time-series thermal detections (1 km² cells, multi-hourly timesteps)
     - Located: `satellite_fire_data\`
2. **Victorian Bushfire Events** – Ground-truth fire extents with geometry and metadata (polygon-based, single snapshot per fire)
     - Located: `historic_fire_events_data\`
3. **Unified Historical Bushfire Events** – Matched ground-truth events with satellite-derived severity, extinguish dates, and burn duration (polygon-based, integrated features)
     - Located: `unified_fire_data\`

Each dataset has advantages and disadvantages depending on forecasting goals, modelling approaches, and GEE integrations.
The Satellite Thermal Detection data and the Unified Historical Bushfire Events data are the most feature-complete, with the Historical Bushfire Event data providing a ground-truth used in the Unified dataset.

The research these datasets are built off of can be found in `ai-modelling\notebooks\research\fire_data\`.

---

## Dataset Comparison

### 1. Satellite Thermal Fire Detection Data
**Best for:** Per-cell spatiotemporal models, fire spread prediction, intensity forecasting. Combines thermal imaging data from 4 seperate satellites hosting NASA's VIIRS and MODIS instruments.

| Aspect | Details |
|--------|---------|
| **Spatial Granularity** | 1 km² grid cells; ~1.3M cells across Victoria |
| **Temporal Granularity** | Multi-hourly (6–12 hr between passes per satellite); 4 satellites provide ~4 passes/day coverage |
| **Time Period** | July 2018 – July 2022; can be easily adjusted for a larger dataset |
| **Records** | ~500k–2M detection records (varies by year and fire activity) |
| **Key Features** | `FRP (peak/cumulative)`, `brightness`, `confidence`, `burning neighbour counts (r=1,2)`, `next/previous cell states` |
| **Geometry** | Grid cells (square, axis-aligned in projected space) |
| **Format** | CSV time-series |

**Advantages:**
- Temporal resolution enables time-series modelling\
- Dense time-series suitable for deep learning
- Neighbor features (`burning_neighbors_r1/r2`) capture fire spread mechanisms
- Built-in prediction targets (`is_burning_next`, `frp_next`) for supervised learning
- Multi-satellite redundancy provides robust coverage
- Cell-level FRP tracks intensity changes

**Limitations:**
- Coarse 1 km² resolution may miss sub-grid fire dynamics
- Multi-hour gaps between passes miss short-duration burns
- Aggregation to cell-level loses fine-scale heterogeneity
- Only contains detections, no entries for non-burning cells
- No ground-truth extent or actual burn area

**Use Cases:**
- Per-cell fire modelling (granular)
- Fire spread prediction (will cell burn in next pass?)
- Intensity forecasting (will FRP increase/decrease?)
- Active fire monitoring and alerting
- Spatiotemporal fire behavior analysis

---

### 2. Victorian Bushfire Events
**Best for:** ground-truth validation

| Aspect | Details |
|--------|---------|
| **Spatial Granularity** | Polygon boundaries (1–10,000+ km² per fire) |
| **Temporal Granularity** | Single snapshot per fire (final extent); ignition date only, no extinguish dates |
| **Time Period** | July 2018 – July 2022; can be easily adjusted for a larger dataset |
| **Records** | ~1,310 bushfire events; can be increased by adjusting time period |
| **Key Features** | `Fire ID`, `name`, `ignition date`, `season`, `fire type`, `size class`, `area`, `perimeter`, `compactness`, `log area` |
| **Geometry** | Polygons (final burnt extent) |
| **Format** | CSV/GeoJSON |

**Advantages:**
- Ground-truth fire boundaries for validation
- Official records with fire metadata
- Directly compatible with GEE for terrain/vegetation correlation

**Limitations:**
- No extinguish dates (only ignition) – critical for modeling burn lifecycle
- No severity measures (FRP) – can't quantify fire intensity
- No temporal evolution – only final extent, not spread timeline
- Small fires excluded from official records – sampling bias
- Polygon imprecision – boundaries are estimates, not real-time data
- No fire behavior targets for supervised learning
- Impossible to train models for fire prediction without extinguish dates

**Use Cases:**
- Fire risk mapping (where do fires burn historically?)
- Ground-truth validation (did satellite detections match official fire extents?)
- Seasonal fire pattern analysis
- Spatial joins with GEE datasets (terrain, vegetation, population)

---

### 3. Unified Historical Bushfire Events
**Best for:** Fire severity modeling, burn lifecycle prediction, holistic fire risk assessment

| Aspect | Details |
|--------|---------|
| **Spatial Granularity** | Polygon boundaries (same as bushfire events dataset) |
| **Temporal Granularity** | Ignition + satellite-estimated extinguish (span from a few hours to 120+ days) |
| **Time Period** | July 2018 – July 2022 |
| **Records** | ~1,310 bushfire events |
| **Key Features** | All from #2 + `extinguish_date`, `duration_days`, `peak_frp`, `cumulative_frp`, `detection_status` |
| **Geometry** | Polygons (final burnt extent) |
| **Format** | CSV/GeoJSON; ready for modeling and GEE integration |

**Advantages:**
- Complete burn lifecycle (ignition → extinguish from satellites)
- Severity measures (FRP) derived from satellite data
- Burn duration quantifies fire persistence
- Detection status flags reveals satellite coverage gaps
- Combines official records with satellite observations (best of both worlds)
- Ready for multi-task learning (severity + duration + spread)
- Ready for GEE integration for correlating fire properties with environment

**Limitations:**
- ~20–30% of short-lived fires undetected by satellites (imputed or flagged as coverage gaps)
- No per-cell spread dynamics; only per fire event aggregates
- Makes research-driven assumptions regarding extinguish date classifications

**Use Cases:**
- Fire severity prediction (will this fire be high-intensity?)
- Burn duration forecasting (how long will this fire burn?)
- Fire risk scoring (whats the risk of a fire in this area?)
- Seasonal/climate impact on fire properties
- Multi-task learning (severity + duration + spread)
- Validation of satellite-derived metrics

---

## Recommended Datasets by Model Type

### Granular Per-Cell Fire Spread Prediction
**Dataset:** Satellite Thermal Fire Detection Data  
**Why:** Temporal sequences of cell states with neighbour context and 4 per-day timesteps

---

### Fire-Level Severity & Duration Prediction
**Dataset:** Unified Historical Bushfire Events  
**Why:** Fire-level targets (peak_frp, cumulative_frp, duration_days) with metadata and GEE-ready polygons

---

## Data Limitations

### General Limitations
- **Geographic scope**: Victoria only; not generalizable to other regions
- **Late ignition dates**: Some fires recorded ignition after first detection due to late official recognition of the fire event

### Satellite Limitations
- **Temporal gaps**: Even with 4 satellites, there are sometimes ~6 hours between passes; fast-moving short-lived fires can be missed
- **Aggregation loss**: Max FRP per cell may not reflect fire dynamics within cell
- **Sparse data**: Only records detected fire events. A full training dataset would also need reference of conditions where the cell wasn't burning
- **Confidence degradation**: MODIS confidence (0–100) binned to 3 levels to match VIIRS data; some precision lost

### Bushfire Events Limitations
- **No extinguish dates**: Official records don't include extinguish; must infer from satellite data
- **Boundary imprecision**: Polygons are estimates
- **Late detection**: Some fires recorded days after ignition
- **Prescribed burns excluded**: Focus on uncontrolled bushfires only

### Unified Dataset Limitations
- **Extinguish estimation error**: 4-day gap threshold selected from the literature; actual extinguish may differ
- **FRP underestimation**: ~20–30% of short-lived fires undetected by satellites; severity for these fires are unknown
- **Imputation bias**: Small undetected fires imputed as 6-hour burns; not ground truth
- **Coarse temporal resolution**: Only ignition and extinguish; no intermediate evolution. Can be addressed with addition feature engineering using satellite data

---

## Next Steps

- Choose modeling approach (per-cell vs. event-level vs. both)
- Load appropriate dataset(s) and validate with use case
- Integrate GEE datasets for environmental context
- Train baseline models on each dataset
- Benchmark per-cell vs. event-level approaches

---

**Processing & Code:**
- See individual notebook READMEs in each dataset folder

---
