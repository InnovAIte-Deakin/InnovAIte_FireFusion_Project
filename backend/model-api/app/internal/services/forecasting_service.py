from pathlib import Path
import numpy as np

from src.models.bushfire.ts_forecaster_inference import ForecastingPredictor


class ForecastingService:

    def __init__(self):

        checkpoint_dir = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "models"
            / "bushfire"
            / "checkpoints"
        )

        self.predictor = ForecastingPredictor(
            model_path=checkpoint_dir / "lstm_forecaster.pth",
            scaler_path=checkpoint_dir / "firefusion_scaler.pkl",
        )

    def predict(self, input_sequence: np.ndarray):

        if input_sequence.shape != (1, 60, 7):
            raise ValueError(
                f"Expected shape (1, 60, 7), got {input_sequence.shape}"
            )

        return self.predictor.predict(
            input_sequence,
            return_original_scale=True
        )