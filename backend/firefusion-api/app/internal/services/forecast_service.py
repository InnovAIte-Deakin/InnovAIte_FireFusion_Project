import json
from datetime import datetime
from .caching_service import cache_client
from .websocket_connection_manager import ws_manager
from ..models.geojson import FeatureCollection

LATEST_KEY = "predictions"
HISTORY_KEY = "predictions_history"


class ForecastService:
    async def on_prediction_message(self, message):
        async with message.process():
            print("Processed message")

            payload = json.loads(message.body)

            # ensure date exists
            if "date" not in payload:
                payload["date"] = datetime.utcnow().date().isoformat()

            geojson = FeatureCollection(**payload)

            # broadcast
            await ws_manager.broadcast(geojson.model_dump())

            # ✅ KEEP existing latest prediction logic
            await cache_client.set(LATEST_KEY, message.body)

            # ✅ ADD history (do NOT replace anything)
            await cache_client.rpush(
                HISTORY_KEY,
                json.dumps(geojson.model_dump())
            )

    # ✅ UNCHANGED: frontend depends on this
    async def fetch_predictions(self):
        data = await cache_client.get(LATEST_KEY)
        if data is None:
            return None
        return json.loads(data)

    # ✅ NEW: fetch all history
    async def fetch_all_history(self):
        data = await cache_client.lrange(HISTORY_KEY, 0, -1)
        if not data:
            return []
        return [json.loads(item) for item in data]

    # ✅ NEW: filter by date
    async def fetch_history_by_date(self, target_date):
        data = await cache_client.lrange(HISTORY_KEY, 0, -1)
        if not data:
            return []

        target = target_date.isoformat()
        return [
            json.loads(item)
            for item in data
            if json.loads(item).get("date") == target
        ]