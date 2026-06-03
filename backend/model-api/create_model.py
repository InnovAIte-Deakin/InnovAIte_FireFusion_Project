from sklearn.ensemble import RandomForestClassifier
import numpy as np
import joblib
from pathlib import Path

# 10 input features:
# max_temp_c, wind_speed_kmh, wind_dir_deg, rel_humidity_pct,
# precipitation_mm, evapotranspiration, soil_moisture,
# soil_temp_c, days_since_rain, years_since_last_fire

X = np.array([
    [25, 10, 180, 60, 5.0, 3.0, 0.30, 20, 1, 5],
    [30, 25, 220, 35, 1.0, 5.0, 0.20, 25, 5, 10],
    [36, 45, 290, 18, 0.0, 7.0, 0.12, 30, 12, 20],
    [40, 70, 315, 8,  0.0, 9.0, 0.05, 35, 20, 30],
    [28, 15, 120, 50, 3.0, 4.0, 0.25, 22, 2, 8],
    [34, 35, 260, 22, 0.0, 6.0, 0.15, 28, 9, 18],
])

# Severity class: 1 to 5
y = np.array([1, 2, 4, 5, 2, 3])

model = RandomForestClassifier(random_state=42)
model.fit(X, y)

model_path = Path(__file__).resolve().parent / "app" / "models" / "model.pkl"
model_path.parent.mkdir(parents=True, exist_ok=True)

joblib.dump(model, model_path)

print(f"Dummy model saved at: {model_path}")