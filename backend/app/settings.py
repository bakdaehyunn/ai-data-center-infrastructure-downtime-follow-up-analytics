from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "procurement-bottleneck-api"
    database_url: str = "postgresql+psycopg://procurement:procurement@localhost:5432/procurement"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
