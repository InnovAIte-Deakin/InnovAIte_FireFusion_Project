from fastapi import FastAPI
from schemas import FeatureCollection
from model import predict_fire

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

app = FastAPI(
    title="FireFusion APIs",
    description="Bushfire prediction and BERT misinformation API",
    version="0.1"
)


@app.post("/predict_bf")
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

MODEL_NAME = "bert-base-uncased"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2
)

model.eval()

# Request schema
class TextRequest(BaseModel):
    text: str

# Health check endpoint

@app.get("/")
def root():
    return {"message": "BERT FastAPI server is running"}

# Prediction endpoint
@app.post("/predict_misinfo")
def predict(request: TextRequest):
    try:
        # Tokenize input
        inputs = tokenizer(
            request.text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )

        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)

        # Get logits
        logits = outputs.logits

        # Convert to probabilities
        probs = F.softmax(logits, dim=1)

        # Predicted class
        predicted_class = torch.argmax(probs, dim=1).item()

        return {
            "input_text": request.text,
            "predicted_class": predicted_class,
            "probabilities": probs.tolist()[0]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
