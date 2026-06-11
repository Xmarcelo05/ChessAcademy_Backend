"""
app/api/routes.py
Endpoints REST de la API - Versión CRUD (Modelado Ágil)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["Cursos Admin"])

# ===================== ESQUEMAS PYDANTIC (Validación) =====================
class CursoBase(BaseModel):
    nombre: str
    nivel: str
    precio: float
    cupos_totales: int

class CursoCreate(CursoBase):
    pass

class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    nivel: Optional[str] = None
    precio: Optional[float] = None
    cupos_totales: Optional[int] = None

class CursoResponse(CursoBase):
    id: str

# ===================== BASE DE DATOS EN MEMORIA =====================
db_cursos = {
    "curso_001": {
        "id": "curso_001", 
        "nombre": "Ajedrez Básico", 
        "nivel": "principiante", 
        "precio": 29.99, 
        "cupos_totales": 30
    },
    "curso_002": {
        "id": "curso_002", 
        "nombre": "Defensa Siciliana", 
        "nivel": "avanzado", 
        "precio": 49.99, 
        "cupos_totales": 15
    }
}

# ===================== ENDPOINTS CRUD =====================

@router.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para que AWS sepa que la API está viva"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# 1. READ (GET) - Obtener todos los cursos
@router.get("/cursos", response_model=List[CursoResponse])
async def listar_cursos():
    """Devuelve la lista completa de cursos"""
    return list(db_cursos.values())

# 2. READ (GET) - Obtener un curso específico
@router.get("/cursos/{curso_id}", response_model=CursoResponse)
async def obtener_curso(curso_id: str):
    """Busca un curso por su ID"""
    if curso_id not in db_cursos:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return db_cursos[curso_id]

# 3. CREATE (POST) - Crear un nuevo curso
@router.post("/cursos", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
async def crear_curso(curso: CursoCreate):
    """Añade un nuevo curso a la base de datos"""
    nuevo_id = f"curso_{str(uuid.uuid4())[:8]}"
    
    nuevo_curso = {
        "id": nuevo_id,
        "nombre": curso.nombre,
        "nivel": curso.nivel,
        "precio": curso.precio,
        "cupos_totales": curso.cupos_totales
    }
    
    db_cursos[nuevo_id] = nuevo_curso
    return nuevo_curso

# 4. UPDATE (PUT) - Modificar un curso existente
@router.put("/cursos/{curso_id}", response_model=CursoResponse)
async def actualizar_curso(curso_id: str, curso_actualizado: CursoUpdate):
    """Modifica los datos de un curso existente"""
    if curso_id not in db_cursos:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    curso_existente = db_cursos[curso_id]
    
    # Actualizar solo los campos que se enviaron
    if curso_actualizado.nombre is not None:
        curso_existente["nombre"] = curso_actualizado.nombre
    if curso_actualizado.nivel is not None:
        curso_existente["nivel"] = curso_actualizado.nivel
    if curso_actualizado.precio is not None:
        curso_existente["precio"] = curso_actualizado.precio
    if curso_actualizado.cupos_totales is not None:
        curso_existente["cupos_totales"] = curso_actualizado.cupos_totales
        
    db_cursos[curso_id] = curso_existente
    return curso_existente

# 5. DELETE (DELETE) - Borrar un curso
@router.delete("/cursos/{curso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_curso(curso_id: str):
    """Elimina un curso de la base de datos"""
    if curso_id not in db_cursos:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    del db_cursos[curso_id]
    return None
