"""
app/models/schemas.py
Esquemas de datos para validación y serialización
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class NivelCurso(str, Enum):
    """Niveles disponibles de cursos"""
    PRINCIPIANTE = "principiante"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class CursoBase(BaseModel):
    """Esquema base para cursos"""
    id: str
    nombre: str
    nivel: NivelCurso
    descripcion: str
    instructor: str
    duracion_semanas: int
    cupos_totales: int
    cupos_disponibles: int
    precio: float
    fechas_inicio: List[str]
    imagen_url: Optional[str] = None


class CursoResponse(CursoBase):
    """Response para listar cursos"""
    porcentaje_disponibilidad: float
    estado: str  # "disponible", "casi_lleno", "lleno"
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "curso_001",
                "nombre": "Ajedrez para Principiantes",
                "nivel": "principiante",
                "descripcion": "Aprende los fundamentos del ajedrez",
                "instructor": "Maestro Carlos",
                "duracion_semanas": 4,
                "cupos_totales": 30,
                "cupos_disponibles": 5,
                "porcentaje_disponibilidad": 16.67,
                "estado": "casi_lleno",
                "precio": 29.99,
                "fechas_inicio": ["2024-07-01", "2024-07-15"],
                "imagen_url": "https://example.com/curso.jpg"
            }
        }


class UsuarioRegistro(BaseModel):
    """Esquema para registro de usuarios"""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telefono: Optional[str] = Field(None, regex=r"^\+?[0-9\s\-\(\)]{10,}$")
    nivel_experiencia: NivelCurso
    fecha_nacimiento: Optional[str] = None
    

class InscripcionRequest(BaseModel):
    """Esquema para procesar inscripciones"""
    usuario: UsuarioRegistro
    curso_id: str
    fecha_inicio_preferida: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    notas: Optional[str] = Field(None, max_length=500)


class InscripcionResponse(BaseModel):
    """Response de inscripción exitosa"""
    id_inscripcion: str
    usuario_nombre: str
    curso_nombre: str
    fecha_inscripcion: str
    estado: str = "confirmada"
    numero_referencia: str
    proximo_evento: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_inscripcion": "insc_123456",
                "usuario_nombre": "Juan García",
                "curso_nombre": "Ajedrez para Principiantes",
                "fecha_inscripcion": "2024-06-15T10:30:00",
                "estado": "confirmada",
                "numero_referencia": "REF-2024-001",
                "proximo_evento": "2024-07-01"
            }
        }


class ActualizacionCursoWS(BaseModel):
    """Esquema para notificaciones WebSocket de cursos"""
    tipo: str = "curso_actualizado"  # curso_actualizado, cupo_reducido
    curso_id: str
    cupos_disponibles: int
    timestamp: str
    mensaje: str


class ErrorResponse(BaseModel):
    """Esquema estándar para errores"""
    error: str
    detalle: Optional[str] = None
    codigo: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response para health check"""
    status: str = "healthy"
    version: str
    timestamp: str
    ambiente: str
