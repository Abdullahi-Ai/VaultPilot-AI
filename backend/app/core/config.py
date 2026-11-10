import os
from enum import Enum
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageMode(str, Enum):
    LOCAL_DEV = "local_dev"       # Mode A: Isolated local fixtures, reproducible tests
    EMULATED_NAS = "emulated_nas" # Mode B: Offline demonstration sandbox, fixed synthetic scenarios
    PHYSICAL_NAS = "physical_nas" # Mode C: Genuine UGREEN NAS mount, strict read-only boundary


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
    UGREEN_NAS_MODE: str = os.getenv("UGREEN_NAS_MODE", "emulated") # Strictly "real" or "emulated"
    UGREEN_NAS_ROOT: str = os.getenv("UGREEN_NAS_ROOT", "/volume1/NGO_Projects")
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "emulated_nas")   # "local_dev", "emulated_nas", "physical_nas"
    LOCAL_DEV_ROOT: str = os.getenv("LOCAL_DEV_ROOT", "./storage/dev_fixtures")

    # Scalability & DoS Safeguards
    MAX_DISCOVERY_FILES: int = int(os.getenv("MAX_DISCOVERY_FILES", "500"))
    MAX_DISCOVERY_DEPTH: int = int(os.getenv("MAX_DISCOVERY_DEPTH", "5"))
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", str(25 * 1024 * 1024))) # 25 MB

    @field_validator("UGREEN_NAS_MODE")
    @classmethod
    def validate_nas_mode(cls, v: str) -> str:
        mode = v.lower().strip()
        if mode not in ("real", "emulated"):
            raise ValueError(f"Invalid UGREEN_NAS_MODE: '{v}'. Must be 'real' or 'emulated'.")
        return mode

    @property
    def effective_storage_mode(self) -> StorageMode:
        """Resolves the active StorageMode from UGREEN_NAS_MODE or STORAGE_MODE."""
        # UGREEN_NAS_MODE takes precedence to preserve legacy test monkeypatching
        if self.UGREEN_NAS_MODE == "real":
            return StorageMode.PHYSICAL_NAS
        elif self.STORAGE_MODE == "local_dev":
            return StorageMode.LOCAL_DEV
        else:
            return StorageMode.EMULATED_NAS

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
