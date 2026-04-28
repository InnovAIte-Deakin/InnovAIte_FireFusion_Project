import numpy as np
import pandas as pd

FEATURE_COLS: list[str] = [
    "temperature_2m",
    "skin_temperature",
    "soil_temperature_l1",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
]

WIND_COLS: list[str] = [
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]


def create_sequences(
    df: pd.DataFrame,
    seq_len: int = 60,
    horizon: int = 2,
    feature_cols: list[str] = FEATURE_COLS,
    cell_col: str = "cell_id",
    time_col: str = "datetime",
) -> tuple[np.ndarray, np.ndarray]:
    X_list: list[np.ndarray] = []
    y_list: list[np.ndarray] = []

    df = df.sort_values([cell_col, time_col])

    for _, cell_df in df.groupby(cell_col, sort=False):
        features = cell_df[feature_cols].to_numpy(dtype=np.float32)
        n = len(features)

        for i in range(n - seq_len - horizon + 1):
            X_list.append(features[i : i + seq_len])
            y_list.append(features[i + seq_len : i + seq_len + horizon])

    if not X_list:
        raise ValueError(f"No sequences created — each cell needs more than {seq_len + horizon} rows.")

    return np.stack(X_list), np.stack(y_list)
