"""
app/core/database.py
Simulación de base de datos en memoria (In-Memory Database)
En producción, esto sería reemplazado por una BD real
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from threading import Lock
from app.models.schemas import (
    NivelCurso, InscripcionRequest, InscripcionResponse
)


class InMemoryDatabase:
    """Base de datos simulada en memoria"""
    
    def __init__(self):
        self.lock = Lock()  # Para operaciones thread-safe
        self._inicializar_cursos()
        self._inicializar_inscripciones()
        
    def _inicializar_cursos(self):
        """Inicializa los cursos disponibles"""
        self.cursos: Dict = {
            "curso_001": {
                "id": "curso_001",
                "nombre": "Ajedrez para Principiantes",
                "nivel": NivelCurso.PRINCIPIANTE,
                "descripcion": "Aprende los fundamentos del ajedrez desde cero. Perfecto si nunca has jugado.",
                "instructor": "Maestro Carlos García",
                "duracion_semanas": 4,
                "cupos_totales": 30,
                "cupos_disponibles": 12,
                "precio": 29.99,
                "fechas_inicio": ["2024-07-01", "2024-07-15", "2024-08-01"],
                "imagen_url": "https://via.placeholder.com/400x300?text=Principiante",
                "contenido": [
                    "Movimiento de piezas",
                    "Reglas básicas",
                    "Primeras estrategias",
                    "Práctica guiada"
                ]
            },
            "curso_002": {
                "id": "curso_002",
                "nombre": "Ajedrez Intermedio - Estrategia",
                "nivel": NivelCurso.INTERMEDIO,
                "descripcion": "Domina la estrategia posicional y mejora tu rating significativamente.",
                "instructor": "Maestro Ana Rodríguez",
                "duracion_semanas": 6,
                "cupos_totales": 25,
                "cupos_disponibles": 3,
                "precio": 49.99,
                "fechas_inicio": ["2024-07-08", "2024-07-22", "2024-08-05"],
                "imagen_url": "https://via.placeholder.com/400x300?text=Intermedio",
                "contenido": [
                    "Control posicional",
                    "Estructura de peones",
                    "Táctica avanzada",
                    "Análisis de partidas",
                    "Apertura científica"
                ]
            },
            "curso_003": {
                "id": "curso_003",
                "nombre": "Ajedrez Avanzado - Finales",
                "nivel": NivelCurso.AVANZADO,
                "descripcion": "Domina los finales de partida con técnicas de maestría internacional.",
                "instructor": "Gran Maestro Roberto López",
                "duracion_semanas": 8,
                "cupos_totales": 20,
                "cupos_disponibles": 8,
                "precio": 79.99,
                "fechas_inicio": ["2024-07-05", "2024-07-19", "2024-08-02"],
                "imagen_url": "https://via.placeholder.com/400x300?text=Avanzado",
                "contenido": [
                    "Finales de torres",
                    "Finales de damas",
                    "Sacrificios profundos",
                    "Teoría de Kasparov",
                    "Análisis computacional",
                    "Preparación de torneos"
                ]
            },
            "curso_004": {
                "id": "curso_004",
                "nombre": "Táctica Acelerada",
                "nivel": NivelCurso.PRINCIPIANTE,
                "descripcion": "Aprende los patrones tácticos más comunes en 2 semanas intensas.",
                "instructor": "Maestro Carlos García",
                "duracion_semanas": 2,
                "cupos_totales": 40,
                "cupos_disponibles": 0,
                "precio": 19.99,
                "fechas_inicio": ["2024-06-25", "2024-07-10"],
                "imagen_url": "https://via.placeholder.com/400x300?text=Tactica",
                "contenido": [
                    "Horquillas",
                    "Clavadas",
                    "Descubiertos",
                    "Mates básicos"
                ]
            }
        }
    
    def _inicializar_inscripciones(self):
        """Inicializa el registro de inscripciones"""
        self.inscripciones: Dict[str, Dict] = {}
        self.usuarios: Dict[str, Dict] = {}  # email -> datos usuario
    
    # ===================== MÉTODOS DE CURSOS =====================
    
    def obtener_todos_cursos(self) -> List[Dict]:
        """Obtiene todos los cursos disponibles"""
        with self.lock:
            return list(self.cursos.values())
    
    def obtener_curso(self, curso_id: str) -> Optional[Dict]:
        """Obtiene un curso por ID"""
        with self.lock:
            return self.cursos.get(curso_id)
    
    def obtener_cursos_por_nivel(self, nivel: NivelCurso) -> List[Dict]:
        """Obtiene cursos filtrados por nivel"""
        with self.lock:
            return [
                curso for curso in self.cursos.values()
                if curso["nivel"] == nivel
            ]
    
    def actualizar_cupos(self, curso_id: str, cantidad: int = -1) -> bool:
        """
        Actualiza los cupos disponibles de un curso
        cantidad: número a restar (negativo) o sumar (positivo)
        """
        with self.lock:
            if curso_id not in self.cursos:
                return False
            
            curso = self.cursos[curso_id]
            nuevos_cupos = curso["cupos_disponibles"] + cantidad
            
            # Validar que no queden cupos negativos
            if nuevos_cupos < 0:
                return False
            
            # Validar que no supere total
            if nuevos_cupos > curso["cupos_totales"]:
                return False
            
            curso["cupos_disponibles"] = nuevos_cupos
            return True
    
    def get_estado_curso(self, curso_id: str) -> Optional[str]:
        """Obtiene el estado textual de un curso"""
        with self.lock:
            if curso_id not in self.cursos:
                return None
            
            curso = self.cursos[curso_id]
            disponibles = curso["cupos_disponibles"]
            totales = curso["cupos_totales"]
            porcentaje = (disponibles / totales) * 100
            
            if disponibles == 0:
                return "lleno"
            elif porcentaje <= 25:
                return "casi_lleno"
            else:
                return "disponible"
    
    # ===================== MÉTODOS DE INSCRIPCIONES =====================
    
    def crear_inscripcion(self, inscripcion_request: InscripcionRequest) -> Optional[Dict]:
        """
        Crea una nueva inscripción
        Retorna los datos de la inscripción o None si falla
        """
        with self.lock:
            # Validar que el curso existe
            if inscripcion_request.curso_id not in self.cursos:
                return None
            
            curso = self.cursos[inscripcion_request.curso_id]
            usuario = inscripcion_request.usuario
            
            # Validar que hay cupos disponibles
            if curso["cupos_disponibles"] <= 0:
                return None
            
            # Validar que el usuario no se ha inscrito 5 veces (límite)
            inscripciones_usuario = [
                i for i in self.inscripciones.values()
                if i["email_usuario"] == usuario.email
            ]
            if len(inscripciones_usuario) >= 5:
                return None
            
            # Crear inscripción
            id_inscripcion = f"insc_{uuid.uuid4().hex[:8]}"
            numero_referencia = f"REF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
            
            inscripcion_data = {
                "id": id_inscripcion,
                "numero_referencia": numero_referencia,
                "curso_id": inscripcion_request.curso_id,
                "curso_nombre": curso["nombre"],
                "nivel_curso": curso["nivel"],
                "nombre_usuario": f"{usuario.nombre} {usuario.apellido}",
                "email_usuario": usuario.email,
                "telefono": usuario.telefono,
                "nivel_experiencia": usuario.nivel_experiencia,
                "fecha_inscripcion": datetime.utcnow().isoformat(),
                "fecha_inicio_preferida": inscripcion_request.fecha_inicio_preferida,
                "notas": inscripcion_request.notas or "",
                "estado": "confirmada",
                "precio_pagado": curso["precio"],
                "proximo_evento": inscripcion_request.fecha_inicio_preferida
            }
            
            # Guardar inscripción y datos de usuario
            self.inscripciones[id_inscripcion] = inscripcion_data
            self.usuarios[usuario.email] = {
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "email": usuario.email,
                "telefono": usuario.telefono,
                "fecha_nacimiento": usuario.fecha_nacimiento,
                "fecha_registro": datetime.utcnow().isoformat()
            }
            
            # Reducir cupos disponibles
            self.cursos[inscripcion_request.curso_id]["cupos_disponibles"] -= 1
            
            return inscripcion_data
    
    def obtener_inscripcion(self, id_inscripcion: str) -> Optional[Dict]:
        """Obtiene los detalles de una inscripción"""
        with self.lock:
            return self.inscripciones.get(id_inscripcion)
    
    def obtener_inscripciones_usuario(self, email: str) -> List[Dict]:
        """Obtiene todas las inscripciones de un usuario"""
        with self.lock:
            return [
                i for i in self.inscripciones.values()
                if i["email_usuario"] == email
            ]
    
    def cancelar_inscripcion(self, id_inscripcion: str) -> bool:
        """Cancela una inscripción y restaura el cupo"""
        with self.lock:
            if id_inscripcion not in self.inscripciones:
                return False
            
            inscripcion = self.inscripciones[id_inscripcion]
            curso_id = inscripcion["curso_id"]
            
            # Restaurar cupo
            if curso_id in self.cursos:
                if self.cursos[curso_id]["cupos_disponibles"] < self.cursos[curso_id]["cupos_totales"]:
                    self.cursos[curso_id]["cupos_disponibles"] += 1
            
            # Marcar como cancelada
            inscripcion["estado"] = "cancelada"
            inscripcion["fecha_cancelacion"] = datetime.utcnow().isoformat()
            
            return True
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas generales"""
        with self.lock:
            total_inscripciones = len(self.inscripciones)
            total_usuarios = len(self.usuarios)
            inscripciones_activas = len([
                i for i in self.inscripciones.values()
                if i["estado"] == "confirmada"
            ])
            cupos_totales = sum(c["cupos_totales"] for c in self.cursos.values())
            cupos_disponibles = sum(c["cupos_disponibles"] for c in self.cursos.values())
            
            return {
                "total_cursos": len(self.cursos),
                "total_usuarios": total_usuarios,
                "total_inscripciones": total_inscripciones,
                "inscripciones_activas": inscripciones_activas,
                "cupos_totales": cupos_totales,
                "cupos_disponibles": cupos_disponibles,
                "tasa_ocupacion": f"{((cupos_totales - cupos_disponibles) / cupos_totales * 100):.2f}%" if cupos_totales > 0 else "0%"
            }


# Instancia global de la BD en memoria
db = InMemoryDatabase()
