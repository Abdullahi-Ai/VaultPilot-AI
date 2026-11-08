import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "VaultPilot AI - Financial Evidence Intelligence"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vaultpilot.db")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    # UGREEN NAS Storage & Evidence Acquisition Configuration
    UGREEN_NAS_MODE: str = os.getenv("UGREEN_NAS_MODE", "emulated") # "real" or "emulated"
    UGREEN_NAS_ROOT: str = os.getenv("UGREEN_NAS_ROOT", "/volume1/NGO_Projects")

    @field_validator("UGREEN_NAS_MODE")
    @classmethod
    def validate_nas_mode(cls, v: str) -> str:
        mode = v.lower().strip()
        if mode not in ("real", "emulated"):
            raise ValueError(f"Invalid UGREEN_NAS_MODE: '{v}'. Must be 'real' or 'emulated'.")
        return mode

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
