from pydantic import BaseModel
from datetime import datetime

class WeatherData(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    timestamp: datetime

class Prediction(BaseModel):
    risk_level: str
    latitude: float
    longitude: float
    probability: float
    timestamp: datetime