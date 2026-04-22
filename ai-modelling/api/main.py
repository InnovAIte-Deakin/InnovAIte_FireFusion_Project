from fastapi import FastAPI
from schemas import FeatureCollection
from model import predict_fire

app = FastAPI(
    title="FireFusion LSTM API",
    description="Bushfire prediction API",
    version="0.1"
)


@app.post("/predict")
def predict(data: FeatureCollection):

    results = []

    for feature in data.features:

        prediction = predict_fire(feature)

        output_feature = {
            "type": "Feature",
            "geometry": feature.geometry.dict(),
            "properties": {
                "cell_id": feature.properties.cell_id,
                "prediction": prediction
            }
        }

        results.append(output_feature)

    return {
        "type": "FeatureCollection",
        "features": results
    }