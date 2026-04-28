from __future__ import annotations

from typing import Callable

import numpy as np
from tensorflow import keras


def expanding_window_cv(
    X: np.ndarray,
    y: np.ndarray,
    model_fn: Callable[[], keras.Model],
    *,
    initial_train_size: int = 1000,
    val_size: int = 200,
    epochs: int = 50,
    batch_size: int = 64,
    patience: int = 7,
    verbose: int = 0,
) -> list[dict[str, float]]:
    n = len(X)
    results = []
    fold = 1
    train_end = initial_train_size

    while train_end + val_size <= n:
        X_val = X[train_end : train_end + val_size]
        y_val = y[train_end : train_end + val_size]

        model = model_fn()
        model.fit(
            X[:train_end], y[:train_end],
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[keras.callbacks.EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=True)],
            verbose=verbose,
        )

        val_loss, val_mae = model.evaluate(X_val, y_val, verbose=0)
        results.append({"fold": fold, "train_size": train_end, "val_loss": float(val_loss), "val_mae": float(val_mae)})
        print(f"Fold {fold} | train={train_end} | val_loss={val_loss:.4f} | val_mae={val_mae:.4f}")

        train_end += val_size
        fold += 1

    print(f"\nMean val_loss={np.mean([r['val_loss'] for r in results]):.4f} | Mean val_mae={np.mean([r['val_mae'] for r in results]):.4f}")
    return results
