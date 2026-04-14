import requests
from datetime import datetime
from app.services.cache import get_cached_prediction, set_cached_prediction

MODEL_API_URL = "http://localhost:8001/predict"  


def get_prediction(lat: float = -37.81, lon: float = 144.96):
    """
    Fetch prediction from AI Model API with caching
    """

    cached = get_cached_prediction()
    if cached:
        return cached

    try:
        response = requests.post(
            MODEL_API_URL,
            json={"lat": lat, "lon": lon},
            timeout=5
        )

        response.raise_for_status()
        data = response.json()

        
        data["timestamp"] = datetime.utcnow().isoformat()

        set_cached_prediction(data)

        return data

    except requests.exceptions.RequestException:
        return {
            "risk_level": "UNKNOWN",
            "latitude": lat,
            "longitude": lon,
            "probability": 0.0,
            "timestamp": datetime.utcnow().isoformat(),  # ✅ REQUIRED
            "message": "Model API unavailable"
        }