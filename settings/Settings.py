from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB 접속 정보
    db_host: str
    db_port: int
    db_service_name: str
    db_user: str
    db_password: str

    # .env에서 읽어오기
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
