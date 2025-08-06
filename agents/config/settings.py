import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Serenite API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    CLIENT_URL: str = "http://localhost:3000"
    GRAPHQL_ENDPOINT: str = f"{CLIENT_URL}/api/graphql"

    AUTH_TIMEOUT: int = 10  # seconds

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    DATABASE_URL: str
    GROQ_API_KEY: str
    TAVILY_API_KEY: str
    ASTRA_DB_ID: str
    ASTRA_DB_APPLICATION_TOKEN: str
    ASTRA_DB_API_ENDPOINT: str

    # Cache settings
    CACHE_TTL: int = 3600  # 1 hour

    # API settings
    API_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]

    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".txt", ".jpg", ".jpeg", ".png", ".pdf"]

    # JWT settings
    # JWT_SECRET: str

    # Security settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    TF_ENABLE_ONEDNN_OPTS: int = 0  # Disable oneDNN optimizations for TensorFlow


    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
