# FireFusion: Hosting Bushfire Prediction Models as an API Service

## Overview

This guide outlines how to expose FireFusion's deep learning models (LSTM, Transformer, CNN-LSTM, TCN) as REST API endpoints for real-time bushfire behavior predictions (severity, area burned, rate of spread).

---

## Why Host Models as a Service?

- **Separation of Concerns:** Data scientists maintain model code independently from frontend/backend developers
- **Multi-Platform Access:** Web, mobile, and third-party applications can consume predictions via a unified API
- **Scalability:** Deploy multiple model instances behind load balancers
- **Version Control:** Easy model versioning and A/B testing
- **Real-time Inference:** Serve predictions without batch processing delays

---

## Framework Choice: Flask vs FastAPI

### Flask
- **Pros:** Lightweight, minimal boilerplate, quick prototyping, extensive documentation
- **Cons:** Slower for high-throughput scenarios, requires manual async handling
- **Best for:** Small to medium deployments

### FastAPI
- **Pros:** High performance (async-native), automatic API documentation (Swagger), built-in validation (Pydantic)
- **Cons:** Steeper learning curve
- **Best for:** Production-grade, high-traffic APIs

**Recommendation:** Use **FastAPI** for FireFusion to handle burst traffic during fire season.

---

## 1. Prepare Your Model

### Model Loading & Preprocessing

```python
import numpy as np
from tensorflow import keras
import json

# Load trained Keras model
model = keras.models.load_model('models/lstm_best.keras')

# Load scaler for feature normalization
with open('data/scaler_info.json', 'r') as f:
    scaler_info = json.load(f)
```

### Input Schema

FireFusion predictions require:
- **Static Features (8):** elevation, slope, aspect, distance to water, vegetation type, NDVI, NDWI, NBR
- **Temporal Features (10 × 8 timesteps):** temperature, wind speed, humidity, precipitation, soil moisture, etc.

---

## 2. Define API Endpoints

### FastAPI Application

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
from tensorflow import keras
import json

app = FastAPI(title="FireFusion Model API", version="1.0.0")

# Load model and scaler
model = keras.models.load_model('models/lstm_best.keras')
with open('data/scaler_info.json') as f:
    scaler_info = json.load(f)

class PredictionRequest(BaseModel):
    X_static: list  # 8 static features
    X_temporal: list  # 8 timesteps × 10 features (shape: 8, 10)

class PredictionResponse(BaseModel):
    severity_class: int
    area_ha_burned: float
    rate_of_spread: float
    model_version: str

@app.get("/healthcheck")
def healthcheck():
    """API liveness probe"""
    return {"status": "healthy", "model": "lstm_best"}

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """Make bushfire prediction given static and temporal features"""
    try:
        # Reshape input
        X_static = np.array(request.X_static).reshape(1, -1)
        X_temporal = np.array(request.X_temporal).reshape(1, 8, 10)
        
        # Normalize features (if required)
        # X_static = (X_static - scaler_info['static_mean']) / scaler_info['static_std']
        
        # Make prediction
        predictions = model.predict([X_static, X_temporal])
        
        return PredictionResponse(
            severity_class=int(predictions[0][0]),
            area_ha_burned=float(predictions[0][1]),
            rate_of_spread=float(predictions[0][2]),
            model_version="lstm_best"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. Testing the API

### Using Python Requests

```python
import requests
import json

url = 'http://127.0.0.1:8000/predict'

# Example input: 8 static features + 8 timesteps of 10 features
payload = {
    "X_static": [800.5, 15.2, 120.3, 5000, 2, 0.65, 0.45, 0.55],
    "X_temporal": [
        [25.3, 15.2, 180, 65, 2.1, 5.2, 0.45, 18.2, 3.5, 2],
        [26.1, 16.5, 190, 60, 1.8, 5.5, 0.42, 19.1, 2.1, 2],
        [27.5, 18.2, 200, 55, 1.5, 5.8, 0.38, 20.5, 0.5, 2],
        [28.9, 20.1, 210, 48, 0.9, 6.2, 0.32, 22.1, 0.0, 2],
        [30.2, 22.5, 215, 42, 0.6, 6.8, 0.25, 24.5, 0.0, 2],
        [31.5, 25.3, 220, 35, 0.3, 7.5, 0.18, 26.8, 0.0, 2],
        [32.8, 28.1, 225, 28, 0.1, 8.2, 0.10, 28.9, 0.0, 2],
        [33.5, 30.2, 230, 20, 0.0, 8.9, 0.05, 30.5, 0.0, 2]
    ]
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    print("Prediction:", response.json())
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Using Postman

1. **Create New Request:** POST to `http://localhost:8000/predict`
2. **Body (JSON):**
   ```json
   {
       "X_static": [800.5, 15.2, 120.3, 5000, 2, 0.65, 0.45, 0.55],
       "X_temporal": [...]
   }
   ```
3. **Send:** Observe severity, area, and rate of spread predictions

### Interactive API Documentation

FastAPI auto-generates Swagger docs at `http://localhost:8000/docs`

---

## 4. Deployment

### Docker Containerization

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models/ ./models/
COPY data/scaler_info.json ./data/
COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (with aggregator)

Update `docker-compose.yaml` to include model-api service:

```yaml
model-api:
  build: ./model-api
  ports:
    - "8000:8000"
  environment:
    - MODEL_PATH=/app/models/lstm_best.keras
  volumes:
    - ./models:/app/models
    - ./data:/app/data
```

### Hosting Options

- **Local:** `python app.py`
- **Docker:** `docker run -p 8000:8000 firefusion-model-api`
- **Cloud:** AWS Lambda, Google Cloud Run, Azure Container Instances
- **Production:** Kubernetes with auto-scaling

---

## Best Practices

1. **Keep-Alive Endpoint:** Always include `/healthcheck` for monitoring
2. **Input Validation:** Use Pydantic models to validate request schema
3. **Error Handling:** Return meaningful error messages (invalid shapes, out-of-range values)
4. **API Versioning:** Support `/v1/predict` and `/v2/predict` for model updates
5. **Rate Limiting:** Implement throttling during peak demand
6. **Logging:** Track predictions for audit and debugging
7. **Model Monitoring:** Log inference times and prediction confidence

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow Serving](https://www.tensorflow.org/tfx/guide/serving)
- [Docker Compose Guide](https://docs.docker.com/compose/)
