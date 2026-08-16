import json
import logging
from .caching_service import cache_client
from .websocket_connection_manager import ws_manager
from ..models.geojson import FeatureCollection

logger = logging.getLogger(__name__)

EMPTY_FEATURE_COLLECTION = {"type": "FeatureCollection", "features": []}


def _empty():
    """Return a fresh empty FeatureCollection.

    A new dict each call so callers can never mutate a shared constant.
    """
    return {"type": "FeatureCollection", "features": []}


class ForecastService:
    async def on_prediction_message(self, message):
        async with message.process():  # handles deleting from queue but not on exceptions
            payload = json.loads(message.body)
            geojson = FeatureCollection(**payload)
            await ws_manager.broadcast(geojson.model_dump())

            await cache_client.set('predictions', message.body)

    async def fetch_predictions(self):
        """Return the latest forecast as a GeoJSON FeatureCollection.

        Per the Fire Risk Map API contract, this always returns a valid
        FeatureCollection so map clients never receive a null or malformed body.
        Dependency failures propagate, and the router translates them to a 503.
        """
        data = await cache_client.get('predictions')
        if data is None:
            logger.info("No cached prediction available; returning empty FeatureCollection")
            return _empty()

        try:
            payload = json.loads(data)
        except (TypeError, ValueError):
            logger.warning("Cached prediction was not valid JSON; returning empty FeatureCollection")
            return _empty()

        # json.loads("null") returns None, and other JSON scalars decode to
        # non-dict types. None of these can be a FeatureCollection.
        if not isinstance(payload, dict):
            logger.warning(
                "Cached prediction decoded to %s, not an object; returning empty FeatureCollection",
                type(payload).__name__,
            )
            return _empty()

        try:
            return FeatureCollection(**payload).model_dump()
        except Exception:
            logger.warning("Cached prediction did not match the GeoJSON schema; returning empty FeatureCollection")
            return _empty()