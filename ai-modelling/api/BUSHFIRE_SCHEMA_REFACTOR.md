# [Bushfire] Refactor Input/Output Schemas for the Single-Model ConvLSTM

**Stream:** AI Modelling · **Type:** refactor + docs + test · **Risk:** Low · **Breaking changes:** none

---

## Scope

**Schema and documentation only.** This change touches:

| File | Change |
|---|---|
| `api/schemas/bushfire.py` | Input grid dimensions, output fire-probability contract, dimension constants |
| `api/README.md` | Input/output property tables, 5-D tensor explanation, classifier marked deprecated |
| `tests/test_bushfire_schemas.py` | New — 28 schema tests |

**Deliberately not touched:** `api/inference/bushfire_forecaster.py` and
`api/inference/bushfire_classifier.py`. An earlier revision of this branch modified both; those
changes were removed on review, because a separate task has already refactored the inference
script for the single-ConvLSTM architecture and the classifier is being retired. The useful
inference-side changes are listed under [Deferred to the refactored inference script](#deferred-to-the-refactored-inference-script)
so they are not lost.

No model, training, or checkpoint code is touched. No retraining, no re-serialisation.

---

## Part 1 — Inputs: data variables, dimensions, structure

The ConvLSTM is spatiotemporal and works on 5-D tensors end to end:

```
input   [batch, seq_len, height, width, n_features]
output  [batch, horizon, height, width, n_output_channels]
```

The input schema could not express the `height`/`width` axes at all, so a request had no way to
say where a cell sits in the grid.

| # | Change |
|---|---|
| 1.1 | Added `grid_row` / `grid_col` to `FeatureTimeseriesPropertiesIn` |
| 1.2 | Validation — grid indices come in pairs, are `>= 0`, and no two cells claim the same position |
| 1.3 | Added optional `schema_version` to `ForecastRequest` |
| 1.4 | Dimension constants `N_DEFAULT_FEATURES`, `DEFAULT_INPUT_STEPS = 60`, `DEFAULT_HORIZON = 1`, `DEFAULT_FIRE_THRESHOLD = 0.5` |
| 1.5 | Documented the 7 ERA5-Land data variables (index, name, unit) and both tensor layouts in the module docstring |

**Why 1.1 / 1.2.** The inference adapter already had the code to reassemble the grid, gated on
`properties.grid_row` / `grid_col` — but those fields were never declared on the input schema,
and the schema is `extra="forbid"`. Any request carrying them was rejected with a 422, so
`has_grid_coords` was always `False` and **every** request fell through to the fallback that
reshapes each cell into a 1×1 grid:

```
[n_samples, seq_len, n_features] -> [n_samples, seq_len, 1, 1, n_features]
```

Still 5-D, but a 1×1 grid gives the convolution no spatial neighbourhood — the ConvLSTM was
being used as an expensive per-cell LSTM. Declaring the two fields is the minimum needed to
make the intended path reachable.

The extra validation exists because a half-specified position (`grid_row` with no `grid_col`)
or two cells claiming `(1, 1)` would otherwise be a silent wrong answer: the first is dropped
from the grid, the second overwrites the first.

**Why `DEFAULT_HORIZON = 1`.** The single-model ConvLSTM predicts one timestep ahead. The old
value of 2 came from the two-model pipeline, where the classifier consumed `horizon - 1`
forecast steps. `60` and `2` were also hardcoded as fallbacks in several files; they are
training hyperparameters, so they now live next to the feature list with a comment pointing at
the training script.

---

## Part 2 — Outputs: fire probability, dimensions, structure

The old output schema described a multivariate regression forecast, plus a separate risk
response for the TCN classifier. Neither matches a single ConvLSTM that emits fire probability.

| # | Change |
|---|---|
| 2.1 | `ForecastPropertiesOut` now leads with `fire_probability` — probability in `[0, 1]`, one entry per horizon step |
| 2.2 | Added `is_burning_predicted` (thresholded) and `fire_threshold` (the threshold used) |
| 2.3 | `risk_score` is now defined as the mean `fire_probability` across the horizon |
| 2.4 | Added `risk_levels` / `risk_labels`, from the single threshold table `RISK_LEVEL_THRESHOLDS` + `prob_to_risk_level()` |
| 2.5 | `forecast` kept as `[horizon, n_output_channels]` — one **row** per horizon step — and made optional, so a multi-channel checkpoint can still be served |
| 2.6 | Added `horizon`, `n_output_channels`, and echoed `grid_row` / `grid_col` |
| 2.7 | Validation — every per-horizon-step field must describe the same number of steps |
| 2.8 | Removed `RiskPropertiesOut` / `GeoRiskFeatureOut` / `RiskResponse` — they were the TCN classifier's contract |
| 2.9 | Removed `output_feature_names` — it described the multivariate regression output |

**Why 2.1–2.4.** Fire probability is what the product consumes, and it had no declared home:
`risk_score` was previously smuggled through `extra="allow"`, undocumented, set on one branch
and not the other. `is_burning_predicted` and `fire_threshold` are named to match the
refactored inference script so the two do not drift.

**Why 2.5 — `forecast` stays a list of rows.** Per-cell output sliced out of the 5-D tensor is
`[horizon, n_output_channels]`. For a 1-channel model that is `[[p]]`, not `[p]`. Keeping the
row structure is what makes "5-D in, 5-D out consistently" visible in the payload, and it
means a checkpoint with more than one output channel is not locked out. A flat list of
probabilities belongs in `fire_probability`.

**Why 2.7.** `fire_probability`, `is_burning_predicted`, `risk_levels`, `risk_labels` and
`forecast` all index the same horizon axis. A mismatch means a postprocessing bug, and it is
cheaper to catch it at the boundary than to debug a misaligned map later.

---

## Deferred to the refactored inference script

These were found while working on the schema and belong to whoever lands the grid handling in
the refactored `bushfire_forecaster.py`. Written down so they are not lost:

1. **Read the declared fields directly.** The adapter uses
   `feature.properties.__dict__.get("grid_row")`. Now that `grid_row` / `grid_col` are declared,
   `feature.properties.grid_row` works and is clearer.
2. **Fill unsupplied grid cells after scaling.** `_build_grid_tensor` initialises the grid with
   `NaN` and only fills the cells the request supplied. Training fills the gaps with the feature
   mean *after* scaling (`scale_and_fill`); inference does not. Because a convolution mixes each
   cell with its neighbours, **one** empty cell spreads `NaN` across the whole output. Verified:
   a partial 2×2 grid returns `"forecast": [[NaN]]`. Note this is already handled in the
   refactored script (`x_scaled[np.isnan(x_scaled)] = 0.0` in `_apply_scaler`) — but only when a
   scaler is present, so a checkpoint shipped without one still leaks `NaN`.
3. **Bounds-check grid positions.** `grid_row >= height` raises a bare `IndexError`; a clear
   `ValueError` naming the offending cell and the model `grid_shape` is easier to act on.
4. **Populate the output dimension fields** (`horizon`, `n_output_channels`, `grid_row`,
   `grid_col`). They are declared but nothing sets them yet, so they serialise as `null`.

---

## Merge order — please read

This PR makes the gridded path *reachable*, but the NaN fill lives in the refactored inference
script. If this lands on top of the current `bushfire_forecaster.py`, a gridded request that
does not cover every cell in `grid_shape` returns `NaN` — and `NaN` is not valid JSON.

Verified against the current inference script with a partial 2×2 grid:

```
gridded path reachable : True
forecast returned      : [[nan]]
```

Two things gate the exposure: `grid_shape` must be present in the checkpoint's scaler bundle
(it may not be), and the request must supply only part of the grid. Safest order is **refactored
inference script first, this PR second**. Merging this first is fine too, as long as the
refactored script follows before anyone sends a partial gridded request.

---

## Backward compatibility

- Every previously valid request is still valid — only optional fields were added.
- The current inference script still validates against this schema: it passes
  `forecast=[[...], [...]]` and `risk_score=...`, both of which the schema accepts.
- Removed output schemas (`RiskResponse` and friends) were only ever used by the TCN classifier
  adapter, which builds raw dicts and does not import them.
- Requests that previously got a 422 for carrying `grid_row` / `grid_col` now succeed. That is
  the point of the ticket, but note it for anyone whose tests assert on that rejection.

## Tests

```bash
cd ai-modelling && python -m pytest tests/test_bushfire_schemas.py -q   # 28 passed
```

Covers dimension constants (including `horizon = 1`), probability → risk level thresholds,
backward-compatible payload acceptance, grid-position validation, the fire-probability output,
`forecast` row structure, per-horizon-step alignment, and multi-channel checkpoints. Pure
pydantic, so it runs without torch installed.

The three pre-existing test modules in `ai-modelling/tests/` still fail to collect
(`src.data.preprocessing` missing, torch/transformers not installed). Unrelated — none of them
import the bushfire API.

## Follow-ups

1. `model_loader.py` still defaults `horizon` to `2` and never sets `fire_threshold` or a
   feature-name key the refactored script can read. Belongs with the checkpoint/metadata work.
2. Regenerate the forecaster scaler bundle so `grid_shape` is present — without it, gridded
   requests silently keep using the 1×1 fallback.
3. Retire `POST /predict/bushfire/classify` and `bushfire_classifier.py` once the single-ConvLSTM
   refactor lands. Marked deprecated in the README for now; the route is still registered.
4. Reconcile `DEFAULT_FEATURE_NAMES` (7 ERA5-Land variables, following the trained checkpoint)
   with `notebooks/research/InputDataSchema.md` (8 static + 10 temporal, the target schema).
5. Agree a single risk contract with BE/FE. They currently read `properties.risk_factor` — a
   single int `0..5` where `1` is extreme and `5` is very low
   (`backend/model-api/app/models/geojson_model.py`, `FireRiskMap.tsx`). This schema produces
   `risk_levels` as a list, range `0..4`, with `0 = LOW` — the opposite direction. Piping one
   into the other would invert the map colours.

## Rollback

Revert the PR. One schema file, one README, one new test file and this doc; no checkpoint,
migration, or config change to undo.
