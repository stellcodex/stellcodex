from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/stellcodex"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: str = "/tmp/stellcodex"
    api_prefix: str = "/api"


settings = Settings()
