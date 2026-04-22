from fastapi import Header, HTTPException
from jose import jwt, JWTError

SECRET = "mysecret"
ALGORITHM = "HS256"

def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid scheme")

        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")