import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Rayhan AI Engineering Workbench API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/rayhan_workbench"
    )
    
    # Auth & JWT Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "rayhan-ai-engineering-workbench-secure-key-32-chars-minimum-token"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_PUBLIC_PER_MINUTE: int = 30
    
    # AI Gateway Settings (Keys strictly server-side)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    PRIMARY_PROVIDER: str = os.getenv("PRIMARY_PROVIDER", "gemini")
    FALLBACK_PROVIDER: str = os.getenv("FALLBACK_PROVIDER", "claude")
    MAX_TOKENS_DEFAULT: int = int(os.getenv("MAX_TOKENS_DEFAULT", "1000"))
    COST_ALERT_THRESHOLD_USD: float = float(os.getenv("COST_ALERT_THRESHOLD_USD", "10.0"))

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
