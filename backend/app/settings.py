from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "maintenance-downtime-followup-api"
    database_url: str = "postgresql+psycopg://maintenance:maintenance@localhost:5432/maintenance"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
