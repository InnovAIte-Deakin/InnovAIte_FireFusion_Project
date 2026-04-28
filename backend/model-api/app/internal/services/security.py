import os
from fastapi import HTTPException, Header

VALID_API_KEY = os.getenv("VALID_API_KEY")

def verify_api_key(x_api_key: str = Header(...)):
    if not x_api_key or x_api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Invalid API Key"
        )