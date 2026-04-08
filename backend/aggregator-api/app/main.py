from fastapi import FastAPI
from app.routers import hello, items
from app.database import engine, Base
from app.internal.models import item  

# Initialise the FastAPI application
app = FastAPI()

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(hello.router)
app.include_router(items.router)