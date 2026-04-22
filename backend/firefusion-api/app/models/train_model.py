import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib

# Fake training dataset (replace later with real historical data)
# Features: [temperature, wind_speed, rainfall]
X = np.array([
    [10, 5, 0],
    [15, 10, 0],
    [25, 20, 0],
    [35, 30, 0],
    [40, 40, 0],
    [20, 5, 10],
    [15, 15, 20],
    [10, 20, 30],
])

# Labels: 0 = LOW, 1 = MEDIUM, 2 = HIGH
y = np.array([0, 0, 1, 2, 2, 1, 2, 2])

model = LogisticRegression()
model.fit(X, y)

joblib.dump(model, "risk_model.pkl")

print("Model trained and saved!")