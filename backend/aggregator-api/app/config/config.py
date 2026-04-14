from pydantic_settings import BaseSettings

# gets from environment variables (case-insensitive)
class Environment(BaseSettings):
    relational_db_url: str
    broker_url: str
    api_key: str

environment = Environment() # type: ignore