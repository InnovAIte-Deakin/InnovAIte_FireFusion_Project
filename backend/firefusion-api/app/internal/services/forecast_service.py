import json
import logging

from .caching_service import cache_client
from .websocket_connection_manager import ws_manager
from ..models.geojson import FeatureCollection

logger = logging.getLogger(__name__)

EMPTY_FEATURE_COLLECTION = {"type": "FeatureCollection", "features": []}


class ForecastService:
    async def on_prediction_message(self, message):
        async with message.process(): # handles deleting from queue but not on exceptions
            print("Processed message")

            payload = json.loads(message.body)
            geojson = FeatureCollection(**payload)
            await ws_manager.broadcast(geojson.model_dump())

            await cache_client.set('predictions', message.body)

    async def fetch_predictions(self):
        """Return cached predictions as a GeoJSON FeatureCollection.

        Never returns None: no cached data or unparseable cached data both
        fall back to an empty FeatureCollection. See
        docs/fire-risk-map-api-contract.md.
        """
        data = await cache_client.get('predictions')
        if data is None:
            return EMPTY_FEATURE_COLLECTION
        try:
            return json.loads(data)
        except (TypeError, ValueError):
            logger.warning("Discarding unparseable cached prediction payload")
            return EMPTY_FEATURE_COLLECTION
