# [Bushfire] Refactor Input/Output Schemas to Support the Refined ConvLSTM Model

**Stream:** AI Modelling · **Type:** refactor · **Risk:** Low · **Breaking changes:** none

---

## Summary

The bushfire API schemas described *what the endpoint happened to return*, not *what the
ConvLSTM actually consumes and produces*. Two consequences:

1. The spatial input the ConvLSTM is built for could not be expressed in a request at all.
2. Bushfire risk probability — the output the product actually cares about — had no schema;
   it was assembled as untyped dictionaries.

This change makes both explicit, **additively**. Every payload that worked before still works
and returns the same values under the same keys.

---

## Part 1 — Inputs: data variables, dimensions, structure

### What changed

| # | Change | File |
|---|---|---|
| 1.1 | Added `grid_row` / `grid_col` to `FeatureTimeseriesPropertiesIn` | `api/schemas/bushfire.py` |
| 1.2 | Added validation: grid indices come in pairs, are `>= 0`, and no two cells claim the same position | `api/schemas/bushfire.py` |
| 1.3 | Added `schema_version` to `ForecastRequest` (optional) | `api/schemas/bushfire.py` |
| 1.4 | Added dimension constants `N_DEFAULT_FEATURES`, `DEFAULT_INPUT_STEPS = 60`, `DEFAULT_HORIZON = 2` and replaced the magic numbers in both adapters | `api/schemas/bushfire.py`, both adapters |
| 1.5 | Documented the 7 data variables (name, index, unit) and both tensor layouts in the module docstring | `api/schemas/bushfire.py` |
| 1.6 | Unfilled grid cells are now filled after scaling, mirroring training | `api/inference/bushfire_forecaster.py` |
| 1.7 | Out-of-range grid positions raise a clear `ValueError` instead of an `IndexError` | `api/inference/bushfire_forecaster.py` |

### Why

**1.1 / 1.2 — the gridded path was unreachable.** `MultivariateTSForecaster` is a *2D*
ConvLSTM: it expects `[batch, seq_len, height, width, n_features]` and learns from
neighbouring cells. The adapter already had the code to reassemble that grid, gated on
`properties.grid_row` / `grid_col` — but those fields were never declared on the input schema,
and the schema is `extra="forbid"`. Any request carrying them was rejected with a 422, so
`has_grid_coords` was always `False` and **every** request silently fell through to the
fallback branch, which reshapes each cell to a 1×1 grid:

```
[n_samples, seq_len, n_features] -> [n_samples, seq_len, 1, 1, n_features]
```

That runs, but a 1×1 grid means the convolution has no spatial neighbourhood — the model was
being used as an expensive per-cell LSTM, not the spatiotemporal model it was trained as.
Declaring the two fields is the minimum needed to make the intended path reachable.

The extra validation exists because a half-specified position (`grid_row` with no `grid_col`)
or two cells claiming `(1, 1)` would previously have been a silent wrong answer: the first
would be dropped from the grid, the second would overwrite the first.

**1.3 — `schema_version`.** `extra="forbid"` means clients cannot send anything undeclared,
so there was no way to version a payload. `InputDataSchema.md` already specifies
`schema_version` for the inference contract; this closes that gap without forcing it.

**1.4 — dimensions in one place.** `60` and `2` were hardcoded as fallbacks in three
different files. They are training hyperparameters (`INPUT_STEPS`, `HORIZON`), so they now
live next to the feature list with a comment pointing at the training script.

**1.6 — NaN would have poisoned the whole grid.** `_build_grid_tensor` initialises the grid
with `NaN` and only fills the cells the request supplied. Training fills the gaps with `0`
*after* scaling (`scale_and_fill`), i.e. with the feature mean. Inference did not. Because a
convolution mixes each cell with its neighbours, **one** empty cell would have spread `NaN`
across the entire output. This never fired before only because the gridded path was
unreachable and JSON cannot carry `NaN` — so enabling 1.1 without this would have shipped a
bug. The fill happens after scaling, exactly as in training. It is a no-op for the
non-gridded path.

---

## Part 2 — Outputs: bushfire risk probability, dimensions, structure

### What changed

| # | Change | File |
|---|---|---|
| 2.1 | New `RiskPropertiesOut` / `GeoRiskFeatureOut` / `RiskResponse` schemas — the risk endpoint's contract is now typed | `api/schemas/bushfire.py` |
| 2.2 | Both classifier functions build their response through those schemas via one shared `_build_risk_response()` helper | `api/inference/bushfire_classifier.py` |
| 2.3 | Threshold table centralised as `RISK_LEVEL_THRESHOLDS` + `prob_to_risk_level()`; the two duplicated copies deleted | `api/schemas/bushfire.py`, `api/inference/bushfire_classifier.py` |
| 2.4 | Added `risk_labels` (`LOW` … `HIGH`) and `horizon` to the risk response | both |
| 2.5 | `ForecastPropertiesOut` now declares `horizon`, `n_output_channels`, `output_feature_names`, `grid_row`, `grid_col`, `risk_score` | `api/schemas/bushfire.py`, forecaster adapter |
| 2.6 | `ForecastPropertiesOut` gained optional `risk_probabilities` / `risk_levels` | `api/schemas/bushfire.py` |
| 2.7 | Validation: `risk_probabilities`, `risk_levels` and `risk_labels` must be the same length | `api/schemas/bushfire.py` |
| 2.8 | Removed a dead `risk_score` computation in the non-gridded forecast branch | `api/inference/bushfire_forecaster.py` |

### Why

**2.1 / 2.2 — the risk output had no schema.** `/predict/bushfire/classify` is the endpoint the
rest of the product consumes, and it was the only one returning hand-built `dict`s
(`response_model=dict`). Nothing validated it and it did not appear in the OpenAPI docs, so a
frontend or backend integrating against it had to read the adapter source. It is now a
declared model, which also means `/docs` describes it.

**2.3 — the thresholds were duplicated.** `_prob_to_label_index` and a nested `prob_to_level`
were byte-for-byte identical implementations of the same 0.2/0.4/0.6/0.8 cut points in one
file. Two copies of a business rule drift. The behaviour is unchanged — verified exhaustively
against the old implementation over `[-0.5, 1.5]`.

**2.4 — `horizon` and `risk_labels`.** A consumer previously had to know that
`risk_probabilities` has one entry per forecast step, and had to re-implement the level →
label mapping (which existed only in the README) to display anything. Both are now in the
payload.

**2.5 — output dimensions were implicit.** A client had to infer horizon and channel count
from array lengths, and had no way to know the channel order of `forecast`. `risk_score` was
also being smuggled through `extra="allow"` — present on the gridded branch, absent
otherwise, and undocumented. It is now declared, so it shows up in the schema and its
gridded-only behaviour is written down.

**2.6 — forward compatibility for a risk-probability ConvLSTM.** If the refined model is
retrained to emit risk probability directly (`output_channels=1` with a sigmoid) instead of
environmental variables, its output already has a home: set `risk_probabilities` /
`risk_levels` on the forecast response using the same shared threshold helper, no schema
change needed. These fields are intentionally unused today and serialise as `null`.

---

## Explicitly *not* changed

Kept as-is so this stays a schema refactor and nothing else:

- **No model, training, or checkpoint changes.** `ts_convlstm_forecaster.py`,
  `tcn_classifier.py` and `src/training/` are untouched. No retraining, no re-serialisation.
- **No numerical logic changed.** Same padding/truncation policy, same scaler application,
  same forward passes, same thresholds, same `risk_score` formula.
- **The `risk_score` asymmetry is preserved, not fixed.** The gridded branch sets
  `risk_score = mean(forecast)`; the non-gridded branch does not. That mean is taken over
  scaled environmental variables, so it is not a meaningful risk figure — but changing it
  would change output values. It is documented as a known wart in the API README; deciding
  whether to drop it or replace it belongs to a separate ticket.
- **The 1×1 fallback path is kept.** Callers that cannot supply grid positions keep working.
  If `grid_shape` is missing from a checkpoint's scaler bundle, gridded requests still fall
  back to it — worth flagging to whoever regenerates checkpoints, since `grid_shape` is what
  activates the real grid.
- **No tightening of existing validation.** `feature_names` is still only length-checked, not
  matched against known variable names — tightening it could reject payloads that work today.

## Backward compatibility

- Every previously valid request is still valid (only optional fields were added).
- Every previously returned key is still returned, with the same value.
- New optional response fields serialise as `null` when unset — additive for consumers that
  read keys by name.
- Requests that previously got a 422 (`grid_row`/`grid_col` present) now succeed. That is the
  point of the ticket, but note it for anyone whose tests assert on that rejection.

## Tests

- `tests/test_bushfire_schemas.py` — 26 new tests: dimension constants, threshold parity,
  legacy payload acceptance, grid-position validation, output dimension fields, risk response
  shape, vector alignment. Pure pydantic, so they run without torch:
  ```bash
  cd ai-modelling && python -m pytest tests/test_bushfire_schemas.py -q   # 26 passed
  ```
- Adapters exercised end-to-end (both branches) with stub models: legacy output byte-compatible,
  gridded path produces `[horizon, n_features]` per cell with no `NaN` leakage, out-of-bounds
  positions raise `ValueError`, classifier response keys are a superset of the old ones.
- The three pre-existing test modules in `ai-modelling/tests/` still fail to collect
  (`src.data.preprocessing` missing, torch/transformers not installed). Unrelated to this
  change — none of them import the bushfire API.

## Follow-ups (not in this change)

1. Regenerate the forecaster scaler bundle so `grid_shape` is present — otherwise gridded
   requests silently keep using the 1×1 fallback.
2. Decide the fate of `risk_score` on the forecast response.
3. Reconcile `DEFAULT_FEATURE_NAMES` (7 ERA5-Land variables) with
   `notebooks/research/InputDataSchema.md` (8 static + 10 temporal). The API follows the
   trained checkpoint; the research doc describes the target schema. They need to converge.

## Rollback

Revert the commit. Three files touched plus one new test file and docs; no checkpoint,
migration, or config change to undo.

## Files touched

| File | Change |
|---|---|
| `api/schemas/bushfire.py` | Input grid fields + validation, dimension constants, shared risk mapping, risk output schemas, documented output dimensions |
| `api/inference/bushfire_forecaster.py` | Reads declared grid fields, NaN fill after scaling, bounds check, populates output dimension fields |
| `api/inference/bushfire_classifier.py` | Builds typed risk response via one shared helper, duplicated thresholds removed |
| `api/README.md` | Input/output property tables, gridded-vs-batched explanation, risk level table |
| `tests/test_bushfire_schemas.py` | New — 26 schema tests |
