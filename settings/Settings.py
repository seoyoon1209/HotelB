# .env 값을 읽어 앱 전역 설정으로 노출한다. DB 접속 정보 외에 새 환경변수가 필요하면
# 여기에 필드를 추가하고 .env / .env.example에도 같이 반영할 것.
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
