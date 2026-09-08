# IOD Processor Test Plan

## Purpose
The IOD (Indian Ocean Dipole) processor mirrors the ENSO processor pattern
(`data-engineering/pipelines/enso/fetch_enso.py`), but with one key
structural difference: ENSO's raw NOAA data arrives already averaged into
3-month seasonal blocks (`SEAS` column, e.g. "DJF"), while IOD's raw NOAA
DMI (Dipole Mode Index) data does not. Per the Sprint 2 plan, the IOD
processor must compute its own 3-month running mean before classifying
phases. This is the main area where the two processors diverge, and where
extra test coverage is needed.

This document covers what the test suite validates once the IOD processor
exists. Test names below match the pytest skeleton (`test_fetch_iod.py`).

## Assumed module structure (mirrors fetch_enso.py)
- `fetch_raw_data()` — downloads raw NOAA DMI data
- `compute_running_mean(df)` — computes the 3-month rolling mean (new step,
  not present in ENSO)
- `assign_phase(value)` — classifies Positive / Negative / Neutral
- `transform_and_standardise(raw_filepath)` — orchestrates cleaning,
  running mean, phase assignment, and schema alignment
- `main()` — end-to-end orchestration

These names are assumptions based on the ENSO pattern. Once Ann's actual
IOD code lands, function names in the pytest skeleton will need updating
to match.

## 1. Phase boundary tests
IOD phase is assumed Positive / Negative / Neutral (confirm exact threshold
with Ann — standard convention is ±0.4, differing from ENSO's ±0.5).

| Test case | Input value | Expected phase |
|---|---|---|
| Exactly at positive threshold | 0.4 | Positive |
| Just above positive threshold | 0.41 | Positive |
| Just below positive threshold | 0.39 | Neutral |
| Exactly at negative threshold | -0.4 | Negative |
| Just below negative threshold | -0.41 | Negative |
| Just above negative threshold | -0.39 | Neutral |
| Zero | 0.0 | Neutral |
| Missing/NaN value | NaN | Should not crash; document expected behaviour (e.g. propagate NaN phase, not silently default to Neutral) |

## 2. Missing months tests
- Input data with a gap in the middle of the date sequence (e.g. missing
  March 1995) — processor should not crash, and the gap should be
  detectable in the output (either as a missing row or a flagged/null
  value, not silently interpolated without documentation).
- Input data missing months at the very start or end of the range.
- Running mean calculation across a gap — confirm it does not silently
  average across the gap as if data were continuous.

## 3. Output format tests
- Output back to 1990 (per Sprint 2 spec) — earliest `datetime_record`
  should be no later than Jan 1990.
- Required columns present or expected schema alignment (mirroring the ENSO
  final columns: id, time_id, datetime_record, record_year_month, the
  index value itself, phase, lag feature, source tag).
- `time_id` is unique and correctly formatted (YYYYMMDDHH, matching the
  team's Time_Registry standard used in ENSO).
- Rows are sorted chronologically with no duplicate `datetime_record`
  values.
- Output is written to both `data/processed/` and the equivalent dataset
  folder for IOD, matching the ENSO save pattern.

## 4. Running mean correctness (IOD-specific, not needed for ENSO)
- Feed a known short sequence of raw monthly values and confirm the
  3-month running mean output matches a manually calculated expected
  value.
- Confirm the running mean window aligns correctly at the start of the
  series (first two months have insufficient data for a full 3-month
  window — confirm expected handling, e.g. NaN vs. partial window).

## 5. Edge cases
- Empty raw file — should raise a clear error rather than fail silently
  or produce an empty but "successful" output.
- Malformed/non-numeric values in the raw file — should raise or clearly
  flag rather than silently coercing to unexpected values.
- Raw file fails to download (network error) — should raise a clear
  error, matching ENSO's `urllib.request.urlretrieve` failure behaviour.

## Status
Test plan drafted and pytest skeleton written ahead of the IOD processor
itself being built, so tests are ready to run against the real
implementation as soon as it lands. Function names and exact thresholds
are assumptions to be confirmed with Ann once her processor is pushed.