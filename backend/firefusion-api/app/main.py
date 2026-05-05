from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import hello
from app.routers import auth_demo

app = FastAPI(
    title="FireFusion API",
    description="FireFusion API with Auth0 JWT authentication demo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hello.router)
app.include_router(auth_demo.router)