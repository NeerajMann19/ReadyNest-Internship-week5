"""
System configurations mapping.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Prism IQ"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://prism-iq.vercel.app",  # Placeholder Vercel production URL — replace with real URL after Vercel deployment
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Local file storage configurations
    STORAGE_ROOT: str = "uploads"
    RAW_UPLOAD_DIR: str = "uploads/raw"
    CLEANED_UPLOAD_DIR: str = "uploads/cleaned"
    MAX_FILE_SIZE_MB: int = 50

    # Data profiling weights
    QUALITY_MISSING_WEIGHT: float = 50.0
    QUALITY_DUPLICATE_WEIGHT: float = 50.0

    # Exploratory Data Analysis (EDA) Settings
    EDA_HISTOGRAM_BINS: int = 20
    EDA_CORRELATION_THRESHOLD: float = 0.3
    EDA_MAX_SAMPLE_ROWS: int = 100000

    # Reports Settings
    REPORT_RETENTION_DAYS: int = 30
    MAX_REPORT_SIZE_MB: int = 25
    DEFAULT_PDF_THEME: str = "classic"


settings = Settings()

