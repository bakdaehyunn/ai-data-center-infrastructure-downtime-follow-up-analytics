from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "ai-data-center-infrastructure-followup-api"
    database_url: str = "postgresql+psycopg://infrastructure:infrastructure@localhost:5432/infrastructure"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
