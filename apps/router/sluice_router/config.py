from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SLUICE_", extra="ignore")

    worker_url: str = "http://llama-server:8080"
    model_id: str = "qwen2.5-0.5b-instruct"
    # CPU generation is slow; a 256-token completion can take ~10s.
    upstream_timeout: float = 300.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
