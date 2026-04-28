from __future__ import annotations

import numpy as np
from tensorflow import keras

from src.utils.dataset import FEATURE_COLS


def predict(model: keras.Model, X: np.ndarray) -> np.ndarray:
    return model.predict(X, verbose=0)


def evaluate(
    model: keras.Model,
    X: np.ndarray,
    y_true: np.ndarray,
    feature_cols: list[str] = FEATURE_COLS,
) -> dict:
    y_pred = predict(model, X)
    errors = y_true - y_pred

    per_feature = {
        col: {
            "mae": float(np.abs(errors[:, :, i]).mean()),
            "rmse": float(np.sqrt((errors[:, :, i] ** 2).mean())),
        }
        for i, col in enumerate(feature_cols)
    }

    per_horizon = [
        {
            "step": h + 1,
            "mae": float(np.abs(errors[:, h, :]).mean()),
            "rmse": float(np.sqrt((errors[:, h, :] ** 2).mean())),
        }
        for h in range(y_true.shape[1])
    ]

    return {
        "mae": float(np.abs(errors).mean()),
        "rmse": float(np.sqrt((errors ** 2).mean())),
        "per_feature": per_feature,
        "per_horizon": per_horizon,
    }


def print_evaluation(metrics: dict, feature_cols: list[str] = FEATURE_COLS) -> None:
    print(f"MAE:  {metrics['mae']:.4f}")
    print(f"RMSE: {metrics['rmse']:.4f}")

    print("\nBy forecast step:")
    for h in metrics["per_horizon"]:
        print(f"  +{h['step']}d  MAE={h['mae']:.4f}  RMSE={h['rmse']:.4f}")

    col_w = max(len(c) for c in feature_cols) + 2
    print("\nBy feature:")
    for col, m in metrics["per_feature"].items():
        print(f"  {col:<{col_w}}  MAE={m['mae']:.4f}  RMSE={m['rmse']:.4f}")
