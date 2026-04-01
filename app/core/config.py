from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )  # .env 裡有但 Settings 沒定義的欄位，直接忽略不要報錯

    SQLALCHEMY_DATABASE_URL: PostgresDsn
    REDIS_DATABASE_URL: RedisDsn
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ISS: str = "task-management-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TASK_CACHE_EXPIRE_MINUTES: int = 10
    LOGIN_LIMIT: int = 5
    LOGIN_WINDOW: int = 60
    TASK_LIMIT: int = 60
    TASK_WINDOW: int = 60


settings = Settings()
