import os
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
AUTH0_ISSUER = f"https://{AUTH0_DOMAIN}/"

if not AUTH0_DOMAIN:
    print("Warning: AUTH0_DOMAIN is not configured.")

if not AUTH0_AUDIENCE:
    print("Warning: AUTH0_AUDIENCE is not configured.")