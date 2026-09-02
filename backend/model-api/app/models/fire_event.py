from pydantic import BaseModel
from datetime import date

class FireEvent(BaseModel):
    max_temp_c: float
    wind_speed_kmh: float
    wind_dir_deg: float
    rel_humidity_pct: float
    precipitation_mm: float
    evapotranspiration: float
    soil_moisture: float
    soil_temp_c: float
    days_since_rain: int
    years_since_last_fire: float
    