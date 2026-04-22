import redis
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

KEY = "firefusion:predictions"


def save_prediction(geojson: dict):
    """
    Store ONLY GeoJSON prediction in Redis
    """
    r.lpush(KEY, json.dumps(geojson, default=str))


def get_all_history():
    """
    Return all stored GeoJSON predictions
    """
    data = r.lrange(KEY, 0, -1)
    return [json.loads(item) for item in data]


def get_latest():
    """
    Return most recent prediction
    """
    data = r.lindex(KEY, 0)
    return json.loads(data) if data else None