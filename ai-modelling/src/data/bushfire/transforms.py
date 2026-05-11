from typing import Literal

import pandas as pd


ScaleMethod = Literal["minmax", "standard"]


def interpolate_time_series(
    df: pd.DataFrame,
    time_col: str,
    cols: list[str],
    group_cols: list[str] | None = None,
    method: str = "linear",
    limit_direction: Literal["forward", "backward", "both"] = "forward",
) -> pd.DataFrame:
    if time_col not in df.columns:
        raise KeyError(f"time column '{time_col}' not found")

    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"columns not found: {missing_cols}")

    result = df.copy()
    result[time_col] = pd.to_datetime(result[time_col])
    sort_cols = [*(group_cols or []), time_col]
    result = result.sort_values(sort_cols)

    if group_cols:
        for col in cols:
            result[col] = (
                result.groupby(group_cols, group_keys=False)[col]
                .transform(
                    lambda series: series.interpolate(
                        method=method,
                        limit_direction=limit_direction,
                    )
                )
            )
        return result

    result[cols] = result[cols].apply(
        lambda series: series.interpolate(
            method=method,
            limit_direction=limit_direction,
        )
    )
    return result


def scale_features(
    df: pd.DataFrame,
    cols: list[str],
    method: ScaleMethod = "standard",
    suffix: str | None = None,
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"columns not found: {missing_cols}")

    if method not in {"minmax", "standard"}:
        raise ValueError("method must be 'minmax' or 'standard'")

    result = df.copy()
    params: dict[str, dict[str, float]] = {}
    out_suffix = suffix or f"_{method}"

    for col in cols:
        numeric = pd.to_numeric(result[col], errors="raise").astype(float)

        if method == "minmax":
            col_min = float(numeric.min())
            col_max = float(numeric.max())
            denom = col_max - col_min
            scaled = pd.Series(0.0, index=numeric.index) if denom == 0 else (numeric - col_min) / denom
            params[col] = {"min": col_min, "max": col_max}
        else:
            mean = float(numeric.mean())
            std = float(numeric.std(ddof=0))
            scaled = pd.Series(0.0, index=numeric.index) if std == 0 else (numeric - mean) / std
            params[col] = {"mean": mean, "std": std}

        result[f"{col}{out_suffix}"] = scaled

    return result, params
