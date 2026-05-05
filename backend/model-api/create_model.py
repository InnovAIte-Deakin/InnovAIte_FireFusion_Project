from sklearn.linear_model import LinearRegression
import numpy as np
import joblib
from pathlib import Path

X = np.array([
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5],
    [4, 5, 6]
])

y = np.array([10, 20, 30, 40])

model = LinearRegression()
model.fit(X, y)

model_path = Path(__file__).resolve().parent / "models" / "model.pkl"
model_path.parent.mkdir(parents=True, exist_ok=True)

joblib.dump(model, model_path)

print(f"Model saved at: {model_path}")