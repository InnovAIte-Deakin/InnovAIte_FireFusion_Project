import json
import random
from pathlib import Path


class GeoJsonService:
    def __init__(self):
        self.data_file = Path(__file__).resolve().parents[2] / "data" / "geojson_data.json"

    def get_geojson(self):
        with open(self.data_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        all_features = data["features"]

        selected_features = random.sample(all_features, k=3)

        return {
            "type": "FeatureCollection",
            "features": selected_features
        }