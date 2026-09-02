from pydantic_settings import BaseSettings


# Reads service configuration from environment variables.
# Pydantic environment variable matching is case-insensitive.
class Environment(BaseSettings):
    db_url: str
    broker_url: str
    cache_url: str

    # Internal Backend service used to retrieve prepared DE records.
    aggregator_url: str = "http://aggregator-api:8080"

    # AI Modelling service address.
    #
    # host.docker.internal allows the Docker-based Backend to reach an
    # AI Modelling FastAPI process running directly on the developer's host.
    # This can later be replaced by a container/service URL without changing
    # the client implementation.
    ai_modelling_url: str = "http://host.docker.internal:8090"


environment = Environment()  # type: ignore