#/backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    EMAIL_FROM: str = "noreply@smartcampus.com"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025  # MailDev default port
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

    