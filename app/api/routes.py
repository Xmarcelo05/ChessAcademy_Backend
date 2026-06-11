"""
app/api/routes.py
Endpoints REST de la API
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
import logging

from app.core.database import db
from app.core.config import get_settings
from app.models.schemas import (
    CursoResponse, InscripcionRequest, InscripcionResponse,
    NivelCurso, ErrorResponse
)
from app.websockets.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["API V1"])


# ===================== ENDPOINTS DE SALUD =====================

@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check para monitoreo y balanceadores de carga
    Usado por AWS App Runner para verificar que la app está viva
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "ambiente": "production"
    }


@router.get("/stats", tags=["Stats"])
async def obtener_estadisticas():
    """
    Obtiene estadísticas generales de la plataforma
    Útil para dashboards administrativos
    """
    return {
        "datos_cursos": db.obtener_estadisticas(),
        "conexiones_websocket": manager.obtener_estadisticas(),
        "timestamp": datetime.utcnow().isoformat()
    }


# ===================== ENDPOINTS DE CURSOS =====================

@router.get("/cursos", response_model=List[CursoResponse])
async def listar_cursos(
    nivel: Optional[NivelCurso] = Query(None, description="Filtrar por nivel"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Lista todos los cursos disponibles
    
    Parámetros:
    - nivel: Filtrar por nivel (principiante, intermedio, avanzado)
    - skip: Número de registros a saltar (paginación)
    - limit: Número máximo de registros a devolver
    
    Response:
    - Lista de cursos con información de disponibilidad
    """
    try:
        if nivel:
            cursos = db.obtener_cursos_por_nivel(nivel)
        else:
            cursos = db.obtener_todos_cursos()
        
        # Enriquecer respuesta con información adicional
        respuesta = []
        for curso in cursos[skip:skip + limit]:
            # Calcular porcentaje de disponibilidad
            porcentaje = (curso["cupos_disponibles"] / curso["cupos_totales"] * 100) if curso["cupos_totales"] > 0 else 0
            
            # Obtener estado del curso
            estado = db.get_estado_curso(curso["id"])
            
            respuesta.append(CursoResponse(
                **curso,
                porcentaje_disponibilidad=round(porcentaje, 2),
                estado=estado
            ))
        
        logger.info(f"Se listaron {len(respuesta)} cursos")
        return respuesta
    
    except Exception as e:
        logger.error(f"Error listando cursos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar cursos"
        )


@router.get("/cursos/{curso_id}", response_model=CursoResponse)
async def obtener_curso_detalle(curso_id: str):
    """
    Obtiene los detalles de un curso específico
    
    Parámetros:
    - curso_id: ID del curso
    
    Response:
    - Información completa del curso incluyendo estado
    """
    try:
        curso = db.obtener_curso(curso_id)
        
        if not curso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Curso {curso_id} no encontrado"
            )
        
        # Enriquecer respuesta
        porcentaje = (curso["cupos_disponibles"] / curso["cupos_totales"] * 100) if curso["cupos_totales"] > 0 else 0
        estado = db.get_estado_curso(curso_id)
        
        return CursoResponse(
            **curso,
            porcentaje_disponibilidad=round(porcentaje, 2),
            estado=estado
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo curso {curso_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener curso"
        )


@router.get("/cursos/{curso_id}/disponibilidad")
async def verificar_disponibilidad(curso_id: str):
    """
    Verifica la disponibilidad actual de cupos en un curso
    Endpoint rápido para consultas frecuentes
    """
    try:
        curso = db.obtener_curso(curso_id)
        
        if not curso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curso no encontrado"
            )
        
        return {
            "curso_id": curso_id,
            "nombre": curso["nombre"],
            "cupos_disponibles": curso["cupos_disponibles"],
            "cupos_totales": curso["cupos_totales"],
            "porcentaje_disponibilidad": round((curso["cupos_disponibles"] / curso["cupos_totales"] * 100), 2),
            "estado": db.get_estado_curso(curso_id),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando disponibilidad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error verificando disponibilidad")


# ===================== ENDPOINTS DE INSCRIPCIONES =====================

@router.post("/inscripciones", response_model=InscripcionResponse, status_code=status.HTTP_201_CREATED)
async def crear_inscripcion(inscripcion: InscripcionRequest):
    """
    Procesa una nueva inscripción a un curso
    
    Body:
    {
        "usuario": {
            "nombre": "Juan",
            "apellido": "García",
            "email": "juan@example.com",
            "telefono": "+34 600 123 456",
            "nivel_experiencia": "principiante",
            "fecha_nacimiento": "1990-05-15"
        },
        "curso_id": "curso_001",
        "fecha_inicio_preferida": "2024-07-01",
        "notas": "Quiero aprender desde cero"
    }
    
    Response:
    - Datos de la inscripción confirmada con número de referencia
    """
    try:
        # Validaciones previas
        curso = db.obtener_curso(inscripcion.curso_id)
        if not curso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curso no encontrado"
            )
        
        # Verificar disponibilidad
        if curso["cupos_disponibles"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay cupos disponibles en este curso"
            )
        
        # Crear inscripción
        resultado = db.crear_inscripcion(inscripcion)
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo procesar la inscripción. Verifica los datos."
            )
        
        # ========== SINCRONIZACIÓN EN TIEMPO REAL ==========
        # Notificar a todos los clientes WebSocket que hay cupos reducidos
        cupos_actuales = db.obtener_curso(inscripcion.curso_id)["cupos_disponibles"]
        await manager.notificar_inscripcion(
            curso_id=inscripcion.curso_id,
            cupos_disponibles=cupos_actuales,
            nombre_usuario=f"{inscripcion.usuario.nombre} {inscripcion.usuario.apellido}"
        )
        
        logger.info(f"Inscripción creada: {resultado['id']} para curso {inscripcion.curso_id}")
        
        return InscripcionResponse(
            id_inscripcion=resultado["id"],
            usuario_nombre=resultado["nombre_usuario"],
            curso_nombre=resultado["curso_nombre"],
            fecha_inscripcion=resultado["fecha_inscripcion"],
            estado=resultado["estado"],
            numero_referencia=resultado["numero_referencia"],
            proximo_evento=resultado["proximo_evento"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando inscripción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando inscripción"
        )


@router.get("/inscripciones/{id_inscripcion}")
async def obtener_inscripcion(id_inscripcion: str):
    """
    Obtiene los detalles de una inscripción específica
    """
    try:
        inscripcion = db.obtener_inscripcion(id_inscripcion)
        
        if not inscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inscripción no encontrada"
            )
        
        return inscripcion
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo inscripción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo inscripción")


@router.get("/usuarios/{email}/inscripciones")
async def obtener_inscripciones_usuario(email: str):
    """
    Obtiene todas las inscripciones de un usuario específico
    """
    try:
        inscripciones = db.obtener_inscripciones_usuario(email)
        
        return {
            "email": email,
            "total_inscripciones": len(inscripciones),
            "inscripciones": inscripciones,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error obteniendo inscripciones: {str(e)}")
        raise HTTPException(status_code=500, detail="Error obteniendo inscripciones")


@router.post("/inscripciones/{id_inscripcion}/cancelar", status_code=status.HTTP_200_OK)
async def cancelar_inscripcion(id_inscripcion: str):
    """
    Cancela una inscripción existente y restaura el cupo
    """
    try:
        success = db.cancelar_inscripcion(id_inscripcion)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inscripción no encontrada"
            )
        
        inscripcion = db.obtener_inscripcion(id_inscripcion)
        
        # Notificar cambio en tiempo real
        curso_id = inscripcion["curso_id"]
        cupos_actuales = db.obtener_curso(curso_id)["cupos_disponibles"]
        await manager.notificar_inscripcion(
            curso_id=curso_id,
            cupos_disponibles=cupos_actuales,
            nombre_usuario="Cupo liberado"
        )
        
        logger.info(f"Inscripción cancelada: {id_inscripcion}")
        
        return {
            "mensaje": "Inscripción cancelada exitosamente",
            "id_inscripcion": id_inscripcion,
            "estado": "cancelada",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelando inscripción: {str(e)}")
        raise HTTPException(status_code=500, detail="Error cancelando inscripción")


# ===================== INFORMACIÓN =====================

@router.get("/info")
async def obtener_informacion():
    """
    Obtiene información sobre la API y variables de configuración
    """
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "endpoints": {
            "cursos": "/api/v1/cursos",
            "inscripciones": "/api/v1/inscripciones",
            "websocket": "/ws/{cliente_id}",
            "health": "/api/v1/health",
            "stats": "/api/v1/stats"
        },
        "documentacion": "/docs",
        "openapi": "/openapi.json"
    }
