from sklearn.linear_model import LinearRegression
import numpy as np
import joblib

# dummy training data
X = np.array([
    [1, 2, 3],
    [2, 3, 4],
    [3, 4, 5],
    [4, 5, 6]
])

y = np.array([10, 20, 30, 40])

# train model
model = LinearRegression()
model.fit(X, y)

# save model
joblib.dump(model, "./app/internal/model/model.pkl")

print("Model saved as model.pkl")