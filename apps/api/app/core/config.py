from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix = "SLUICE_",env_file = ".env",extra="ignore"
    )
    app_name:str = "Sluice API"
    app_env:str = "dev"
    log_level:str = "INFO"
    api_version:str = "v1"

@lru_cache
def get_settings() -> Settings:
    return Settings()