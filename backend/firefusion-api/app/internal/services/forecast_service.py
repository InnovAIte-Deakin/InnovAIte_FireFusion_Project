import json
from datetime import datetime
from .caching_service import cache_client
from .websocket_connection_manager import ws_manager
from ..models.geojson import FeatureCollection

REDIS_KEY = "predictions"


class ForecastService:
    async def on_prediction_message(self, message):
        async with message.process():
            print("Processed message")

            payload = json.loads(message.body)

            # ensure date exists for filtering
            if "date" not in payload:
                payload["date"] = datetime.utcnow().date().isoformat()

            geojson = FeatureCollection(**payload)

            # broadcast to websocket clients
            await ws_manager.broadcast(geojson.model_dump())

            # store in Redis list
            await cache_client.rpush(
                REDIS_KEY,
                json.dumps(geojson.model_dump())
            )

    async def fetch_predictions(self):
        data = await cache_client.lrange(REDIS_KEY, 0, -1)

        if not data:
            return []

        return [json.loads(item) for item in data]

    async def fetch_history_by_date(self, target_date):
        data = await cache_client.lrange(REDIS_KEY, 0, -1)

        if not data:
            return []

        target = target_date.isoformat()

        filtered = []
        for item in data:
            obj = json.loads(item)

            if obj.get("date") == target:
                filtered.append(obj)

        return filtered