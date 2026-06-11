"""
app/core/config.py
Configuración centralizada de la aplicación
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información de la app
    APP_NAME: str = "Chess Academy API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # CORS - Orígenes permitidos
    AZURE_FRONTEND_URL: str = os.getenv(
        "AZURE_FRONTEND_URL",
        "http://localhost:3000"  # Para desarrollo local
    )
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5000",
    ]
    
    # Se actualiza dinámicamente desde env
    @property
    def get_allowed_origins(self) -> List[str]:
        """Obtiene los orígenes permitidos"""
        origins = self.ALLOWED_ORIGINS.copy()
        if self.AZURE_FRONTEND_URL and self.AZURE_FRONTEND_URL not in origins:
            origins.append(self.AZURE_FRONTEND_URL)
        return origins
    
    # Configuración de API
    API_V1_STR: str = "/api/v1"
    
    # WebSocket
    WEBSOCKET_TIMEOUT: int = 30
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-clave-secreta-cambiar-en-produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Límites de la aplicación
    MAX_INSCRIPCIONES_POR_CORREO: int = 5  # Max 5 inscripciones por email
    TIMEOUT_SOLICITUD: int = 60  # segundos
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración cacheada"""
    return Settings()


# Instancia global de configuración
settings = get_settings()
