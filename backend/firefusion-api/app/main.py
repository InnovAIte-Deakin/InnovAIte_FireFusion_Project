from fastapi import FastAPI
from app.routers import hello
from app.routers import weather_router

app = FastAPI()

app.include_router(hello.router)
app.include_router(weather_router.router, prefix="/api")
