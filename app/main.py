from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.core.config import settings
from app.api import routes

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"Orígenes CORS permitidos: {settings.get_allowed_origins}")
    yield
    logger.info("Apagando aplicación...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    max_age=3600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no capturado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detalle": str(exc) if settings.DEBUG else "Error del servidor",
            "codigo": "INTERNAL_ERROR"
        }
    )

app.include_router(routes.router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "mensaje": "Bienvenido a Chess Academy API",
        "nombre": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "documentacion": "/docs",
        "estado": "activo"
    }

@app.options("/{full_path:path}", include_in_schema=False)
async def preflight(full_path: str):
    return JSONResponse(status_code=200)

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
