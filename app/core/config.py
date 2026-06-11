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
            "http://localhost:3000",   
            "http://localhost:5500",   
            "http://127.0.0.1:5500",  
            "http://localhost:8000",   
            "https://kind-plant-0a0193f10.7.azurestaticapps.net"  
        ]

settings = Settings()
