"""
FireFusion AI Model API — Application Entrypoint

Run with:
    cd ai-modelling
    uvicorn api.main:app --reload --port 8000

Interactive docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import model_lifespan
from api.routers import health, predict

app = FastAPI(
    title="FireFusion AI Model API",
    description=(
        "Lightweight model-serving API for the FireFusion bushfire "
        "forecasting platform.  Accepts terrain and weather features "
        "per grid cell and returns fire-spread predictions."
    ),
    version="1.0.0",
    lifespan=model_lifespan,
)

# ── CORS — allow cross-origin requests during development ───────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(predict.router)
