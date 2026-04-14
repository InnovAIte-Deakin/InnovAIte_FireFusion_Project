import joblib
import numpy as np
from pathlib import Path


class ModelService:
    def __init__(self):
        # Get absolute path to model.pkl
        model_path = Path(__file__).resolve().parents[2] / "models" / "model.pkl"
        
        print("Loading model from:", model_path)  # optional debug
        
        self.model = joblib.load(model_path)

    async def predict(self, features: list[float]) -> float:
        data = np.array(features).reshape(1, -1)
        prediction = self.model.predict(data)
        return float(prediction[0])