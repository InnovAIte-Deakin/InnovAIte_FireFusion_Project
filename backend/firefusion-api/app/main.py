from fastapi import FastAPI
import logging
from app.routes.api import router   

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

app = FastAPI(
    title="FireFusion API",
    description="Central API Gateway for bushfire prediction system",
    version="1.0"
)

app.include_router(router)   