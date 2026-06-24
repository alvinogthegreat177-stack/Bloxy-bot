from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Platform"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///platform.db"

    class Config:
        env_file = ".env"


settings = Settings()
