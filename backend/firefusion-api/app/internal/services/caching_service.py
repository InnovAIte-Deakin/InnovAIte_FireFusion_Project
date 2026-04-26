from redis import asyncio as redis
import os

cache_url = os.environ.get("CACHE_URL", "redis://cache:6379")

# IMPORTANT: use Redis URL (Docker-safe)
cache_client = redis.from_url(cache_url, decode_responses=True)