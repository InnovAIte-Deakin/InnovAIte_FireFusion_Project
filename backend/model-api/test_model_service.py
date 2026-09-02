import asyncio
import json
from app.internal.services.model_service import ModelService


class FakeMessagingService:
    async def publish_prediction(self, payload):
        print("✅ Mock publish_prediction called")
        if hasattr(payload, "model_dump"):
            print(json.dumps(payload.model_dump(), indent=2))
        else:
            print(json.dumps(payload, indent=2))


class DummyProcess:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummyMessage:
    def __init__(self, body):
        self.body = body

    def process(self):
        return DummyProcess()


async def test():
    messaging = FakeMessagingService()
    service = ModelService(messaging)

    test_data = [
        {
            "day": 1,
            "hour": 12,
            "max_temp_c": 35.8,
            "wind_speed_kmh": 32.0,
            "wind_dir_deg": 292.0,
            "rel_humidity_pct": 22.0,
            "precipitation_mm": 0.0,
            "evapotranspiration": 6.1,
            "soil_moisture": 0.11,
            "soil_temp_c": 29.5,
            "days_since_rain": 10,
            "years_since_last_fire": 21.0
        }
    ]

    message = DummyMessage(json.dumps(test_data).encode("utf-8"))

    await service.consume_data_publish_prediction(message)


asyncio.run(test())