from functools import lru_cache
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix = "SLUICE_",env_file = ".env",extra="ignore"
    )
    app_name:str = "Sluice"
    app_version:str = "0.1.0"
    version:str = "0.1.0"
    environment:str = "dev"
    log_level:str = "INFO"
    api_version:str = "v1"
    database_url:PostgresDsn

@lru_cache
def get_settings() -> Settings:
    return Settings()