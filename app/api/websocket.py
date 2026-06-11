"""
app/api/websocket.py
Endpoint WebSocket para sincronización en tiempo real
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from datetime import datetime
import json
import logging
import uuid

from app.websockets.manager import manager
from app.core.database import db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{cliente_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    cliente_id: str = Query(..., description="ID único del cliente")
):
    """
    Endpoint WebSocket para sincronización en tiempo real
    
    Conexión:
    ws://localhost:8000/ws/cliente_123
    
    Mensajes soportados:
    {
        "tipo": "suscribir",
        "curso_id": "curso_001"
    }
    
    {
        "tipo": "desuscribir",
        "curso_id": "curso_001"
    }
    
    {
        "tipo": "obtener_cursos"
    }
    
    Eventos recibidos:
    - conexion_establecida: Confirmación de conexión
    - curso_actualizado: Cambio en disponibilidad
    - inscripcion_procesada: Nueva inscripción (cupos reducidos)
    - heartbeat: Latido cada 30 segundos
    """
    
    try:
        # Establecer conexión
        await manager.conectar(websocket, cliente_id)
        
        # Bucle principal para recibir mensajes
        while True:
            data = await websocket.receive_text()
            
            try:
                mensaje = json.loads(data)
                tipo = mensaje.get("tipo")
                
                logger.info(f"Cliente {cliente_id} - Mensaje recibido: {tipo}")
                
                # ========== SUSCRIPCIÓN A CURSO ==========
                if tipo == "suscribir":
                    curso_id = mensaje.get("curso_id")
                    if not curso_id:
                        await websocket.send_json({
                            "tipo": "error",
                            "mensaje": "curso_id es requerido",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    # Verificar que el curso existe
                    if not db.obtener_curso(curso_id):
                        await websocket.send_json({
                            "tipo": "error",
                            "mensaje": f"Curso {curso_id} no existe",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    await manager.suscribir_curso(cliente_id, curso_id)
                    
                    # Enviar estado actual del curso
                    curso = db.obtener_curso(curso_id)
                    await websocket.send_json({
                        "tipo": "suscripcion_confirmada",
                        "curso_id": curso_id,
                        "nombre_curso": curso["nombre"],
                        "cupos_disponibles": curso["cupos_disponibles"],
                        "cupos_totales": curso["cupos_totales"],
                        "estado": db.get_estado_curso(curso_id),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Cliente {cliente_id} suscrito a {curso_id}")
                
                # ========== DESUSCRIPCIÓN DE CURSO ==========
                elif tipo == "desuscribir":
                    curso_id = mensaje.get("curso_id")
                    if not curso_id:
                        await websocket.send_json({
                            "tipo": "error",
                            "mensaje": "curso_id es requerido",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    await manager.desuscribir_curso(cliente_id, curso_id)
                    
                    await websocket.send_json({
                        "tipo": "desuscripcion_confirmada",
                        "curso_id": curso_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # ========== OBTENER ESTADO DE CURSOS ==========
                elif tipo == "obtener_cursos":
                    cursos = db.obtener_todos_cursos()
                    cursos_data = []
                    
                    for curso in cursos:
                        porcentaje = (curso["cupos_disponibles"] / curso["cupos_totales"] * 100) if curso["cupos_totales"] > 0 else 0
                        cursos_data.append({
                            "id": curso["id"],
                            "nombre": curso["nombre"],
                            "nivel": curso["nivel"],
                            "cupos_disponibles": curso["cupos_disponibles"],
                            "cupos_totales": curso["cupos_totales"],
                            "porcentaje_disponibilidad": round(porcentaje, 2),
                            "estado": db.get_estado_curso(curso["id"]),
                            "precio": curso["precio"]
                        })
                    
                    await websocket.send_json({
                        "tipo": "lista_cursos",
                        "cursos": cursos_data,
                        "total": len(cursos_data),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # ========== OBTENER ESTADÍSTICAS ==========
                elif tipo == "obtener_estadisticas":
                    stats = db.obtener_estadisticas()
                    await websocket.send_json({
                        "tipo": "estadisticas",
                        "datos": stats,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # ========== PING (LATIDO) ==========
                elif tipo == "ping":
                    await websocket.send_json({
                        "tipo": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # ========== TIPO DESCONOCIDO ==========
                else:
                    await websocket.send_json({
                        "tipo": "error",
                        "mensaje": f"Tipo de mensaje no reconocido: {tipo}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "tipo": "error",
                    "mensaje": "JSON inválido",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}")
                await websocket.send_json({
                    "tipo": "error",
                    "mensaje": "Error procesando mensaje",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        await manager.desconectar(cliente_id)
        logger.info(f"Cliente {cliente_id} desconectado")
    
    except Exception as e:
        logger.error(f"Error WebSocket para cliente {cliente_id}: {str(e)}")
        await manager.desconectar(cliente_id)


# Ruta alternativa para obtener ID cliente
@router.get("/ws/generate-client-id")
async def generar_cliente_id():
    """
    Genera un ID de cliente único para la conexión WebSocket
    El frontend puede usar este endpoint para obtener un ID único
    """
    cliente_id = f"cliente_{uuid.uuid4().hex[:12]}"
    return {
        "cliente_id": cliente_id,
        "timestamp": datetime.utcnow().isoformat(),
        "instrucciones": f"Usa este ID para conectarte a /ws/{cliente_id}"
    }
