"""
FastAPI entrypoint for ai-modelling inference API.

Run from ``ai-modelling/``::

    uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.model_loader import load_models
from api.routers import health, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield


app = FastAPI(title="InnovAIte AI modelling API", lifespan=lifespan)
app.include_router(health.router)
app.include_router(predict.router)