import time

cache = {}

def get_cached_prediction():
    cached = cache.get("prediction")
    if not cached:
        return None

    # expire after 5 minutes
    if time.time() - cached["time"] > 300:
        return None

    return cached["data"]

def set_cached_prediction(data):
    cache["prediction"] = {
        "data": data,
        "time": time.time()
    }