import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "E-Commerce Sales Analytics API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database Configuration (PostgreSQL in production, SQLite fallback locally)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./data/database/superstore.db"
    )
    
    # Default sample dataset locations for auto-seeding
    DEFAULT_DATA_PATH: str = os.path.join("data", "raw", "Sample_Superstore.csv")
    CLEANED_DATA_PATH: str = os.path.join("data", "cleaned", "superstore_cleaned.csv")
    
    # CORS Origins
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return ["*"]
        
    @field_validator("DATABASE_URL", mode="before")
    def fix_postgres_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
