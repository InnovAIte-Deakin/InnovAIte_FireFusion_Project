from fastapi import FastAPI
from app.routes.api import router

app = FastAPI(
    title="FireFusion API",
    version="1.0"
)

app.include_router(router)