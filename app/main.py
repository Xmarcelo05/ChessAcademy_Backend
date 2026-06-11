"""
app/main.py
Archivo principal de la aplicación FastAPI
Configura CORS, middleware, y registra routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.core.config import settings
from app.api import routes, websocket

# ===================== CONFIGURACIÓN DE LOGGING =====================

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# ===================== CICLO DE VIDA DE LA APP =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación
    startup: Al iniciar
    shutdown: Al apagar
    """
    # STARTUP
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"Orígenes CORS permitidos: {settings.get_allowed_origins}")
    yield
    
    # SHUTDOWN
    logger.info("🛑 Apagando aplicación...")


# ===================== CREAR APP FASTAPI =====================

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API para Chess Academy - Landing Page de Cursos de Ajedrez",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ===================== MIDDLEWARE DE SEGURIDAD =====================

# 1. Middleware CORS - Muy importante para Azure
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,  # Solo dominios permitidos
    allow_credentials=True,  # Permitir cookies/credenciales
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],  # Permitir todos los headers
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    max_age=3600,  # Cache de preflight por 1 hora
)

logger.info(f"✅ CORS configurado - Orígenes: {settings.get_allowed_origins}")

# 2. Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar dominios exactos
)


# ===================== MANEJO DE ERRORES GLOBAL =====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    logger.error(f"Error no capturado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc) if settings.DEBUG else "Error del servidor",
            "codigo": "INTERNAL_ERROR"
        }
    )


# ===================== REGISTRAR ROUTERS =====================

# Routers de API REST
app.include_router(routes.router)

# Router de WebSocket
app.include_router(websocket.router)


# ===================== RUTAS RAÍZ =====================

@app.get("/", tags=["Root"])
async def root():
    """Ruta raíz de la API"""
    return {
        "mensaje": "Bienvenido a Chess Academy API",
        "nombre": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentacion": "/docs",
        "estado": "activo"
    }


@app.options("/{full_path:path}", include_in_schema=False)
async def preflight(full_path: str):
    """Maneja peticiones OPTIONS para CORS preflight"""
    return JSONResponse(status_code=200)


# ===================== INSTRUCCIONES =====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Iniciando servidor en http://localhost:8000")
    logger.info(f"Documentación disponible en http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
