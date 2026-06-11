from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Chess Academy API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    @property
    def get_allowed_origins(self) -> List[str]:
        return [
            "http://localhost:3000",   # Si usan React/Node local
            "http://localhost:5500",   # Puerto típico de Live Server (VSCode)
            "http://127.0.0.1:5500",   # Alternativa de Live Server
            "http://localhost:8000",   # El propio backend
            "https://kind-plant-0a0193f10.7.azurestaticapps.net"  # TU FRONTEND EN AZURE
        ]

settings = Settings()
