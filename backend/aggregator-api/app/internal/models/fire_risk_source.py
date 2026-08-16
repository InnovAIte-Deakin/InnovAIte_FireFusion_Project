from datetime import datetime

from pydantic import BaseModel


class FireRiskSourceRecord(BaseModel):
    """
    Prepared Data Engineering information that may contribute to
    an AI Modelling bushfire forecast request.

    These fields reflect the currently visible Supabase schema.

    This is intentionally NOT the AI request model. Backend will map
    the final agreed DE fields into the AI model contract separately.
    """

    location_id: int
    time_id: int
    datetime_record: datetime

    grid_latitude: float
    grid_longitude: float
    region_name: str | None = None

    # weather_observation
    temperature_c: float | None = None
    wind_speed_kmh: float | None = None
    relative_humidity: float | None = None

    # vegetation_condition
    vegetation_class: str | None = None
    dryness_index: float | None = None
    soil_moisture: float | None = None

    # topography_profile
    elevation_meters: float | None = None
    slope_angle: float | None = None

    # ENSO / el_nino
    oni_anomaly: float | None = None
    enso_phase: str | None = None
    oni_lag6m: float | None = None