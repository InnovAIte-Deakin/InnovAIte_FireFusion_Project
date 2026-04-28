"""
Model loader and FastAPI lifespan dependency injection.

At startup the app tries to load a serialised model file.
If the file doesn't exist yet (model not trained), model stays None
and the predict endpoint falls back to mock/stub responses.

When the LSTM model is ready, just drop the .pkl file at MODEL_PATH
and restart the server — no other code changes needed.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request

logger = logging.getLogger("firefusion.api")

# Configurable via env var; default relative to ai-modelling root
MODEL_PATH = Path(
    os.getenv("MODEL_PATH", str(Path(__file__).resolve().parent.parent / "models" / "lstm_model.pkl"))
)


@asynccontextmanager
async def model_lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Loads the model once at startup, stores it on app.state,
    and cleans up on shutdown.
    """
    model = None

    if MODEL_PATH.exists():
        try:
            import joblib

            model = joblib.load(MODEL_PATH)
            logger.info("Model loaded from %s", MODEL_PATH)
        except Exception as exc:
            logger.error("Failed to load model from %s: %s", MODEL_PATH, exc)
    else:
        logger.warning("Model file not found at %s — running in mock mode", MODEL_PATH)

    app.state.model = model
    yield
    # Cleanup (nothing required for now)
    app.state.model = None


def get_model(request: Request):
    """FastAPI dependency — returns the loaded model (or None)."""
    return request.app.state.model
