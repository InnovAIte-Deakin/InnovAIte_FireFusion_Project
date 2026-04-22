def to_geojson(prediction):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                prediction["longitude"],
                prediction["latitude"]
            ]
        },
        "properties": {
            "risk_level": prediction["risk_level"],
            "probability": prediction["probability"],
            "timestamp": prediction["timestamp"]
        }
    }