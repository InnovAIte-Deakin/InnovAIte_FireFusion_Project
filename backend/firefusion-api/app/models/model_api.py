from fastapi import FastAPI
from pydantic import BaseModel
import requests
import joblib
import numpy as np

app = FastAPI()

model = joblib.load("risk_model.pkl")


class PredictionRequest(BaseModel):
    lat: float
    lon: float


def get_live_weather(lat, lon):
    """
    Free real-time weather (no API key)
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )

    r = requests.get(url, timeout=5)
    data = r.json()["current_weather"]

    return {
        "temperature": data["temperature"],
        "windspeed": data["windspeed"],
        "rain": 0  # Open-Meteo doesn't always include rain in current_weather
    }


def decode_risk(pred):
    return {0: "LOW", 1: "MEDIUM", 2: "HIGH"}[pred]


@app.post("/predict")
def predict(req: PredictionRequest):

    weather = get_live_weather(req.lat, req.lon)

    features = np.array([[
        weather["temperature"],
        weather["windspeed"],
        weather["rain"]
    ]])

    prediction = model.predict(features)[0]
    probability = model.predict_proba(features).max()

    return {
        "risk_level": decode_risk(prediction),
        "latitude": req.lat,
        "longitude": req.lon,
        "probability": float(round(probability, 3)),
        "weather": weather,
        "source": "live_open_meteo + sklearn_model"
    }