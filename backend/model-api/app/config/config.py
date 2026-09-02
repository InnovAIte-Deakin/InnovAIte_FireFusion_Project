from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    broker_url: str
    cache_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


environment = Environment()