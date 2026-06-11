"""
app/websockets/manager.py
Gerenciador de conexiones WebSocket para sincronización en tiempo real
"""

from typing import List, Set, Dict
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gerencia todas las conexiones WebSocket activas
    Permite enviar actualizaciones a clientes conectados en tiempo real
    """
    
    def __init__(self):
        # active_connections[cliente_id] = {'websocket': ws, 'cursos_suscritos': set()}
        self.active_connections: Dict[str, Dict] = {}
        self.conexiones_por_curso: Dict[str, Set[str]] = {}  # curso_id -> {cliente_id1, cliente_id2, ...}
    
    async def conectar(self, websocket: WebSocket, cliente_id: str):
        """Establece una nueva conexión WebSocket"""
        await websocket.accept()
        self.active_connections[cliente_id] = {
            'websocket': websocket,
            'cursos_suscritos': set(),
            'conectado_desde': datetime.utcnow().isoformat()
        }
        logger.info(f"Cliente {cliente_id} conectado. Total conexiones: {len(self.active_connections)}")
        
        # Enviar confirmación de conexión
        await websocket.send_json({
            "tipo": "conexion_establecida",
            "mensaje": "Conectado al servidor en tiempo real",
            "cliente_id": cliente_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def desconectar(self, cliente_id: str):
        """Elimina una conexión WebSocket"""
        if cliente_id in self.active_connections:
            # Limpiar suscripciones
            for curso_id in list(self.active_connections[cliente_id]['cursos_suscritos']):
                if curso_id in self.conexiones_por_curso:
                    self.conexiones_por_curso[curso_id].discard(cliente_id)
                    if not self.conexiones_por_curso[curso_id]:
                        del self.conexiones_por_curso[curso_id]
            
            del self.active_connections[cliente_id]
            logger.info(f"Cliente {cliente_id} desconectado. Total conexiones: {len(self.active_connections)}")
    
    async def suscribir_curso(self, cliente_id: str, curso_id: str):
        """Suscribe un cliente a las actualizaciones de un curso específico"""
        if cliente_id not in self.active_connections:
            return False
        
        self.active_connections[cliente_id]['cursos_suscritos'].add(curso_id)
        
        if curso_id not in self.conexiones_por_curso:
            self.conexiones_por_curso[curso_id] = set()
        self.conexiones_por_curso[curso_id].add(cliente_id)
        
        logger.info(f"Cliente {cliente_id} suscrito a curso {curso_id}")
        return True
    
    async def desuscribir_curso(self, cliente_id: str, curso_id: str):
        """Desuscribe un cliente de un curso"""
        if cliente_id not in self.active_connections:
            return False
        
        self.active_connections[cliente_id]['cursos_suscritos'].discard(curso_id)
        
        if curso_id in self.conexiones_por_curso:
            self.conexiones_por_curso[curso_id].discard(cliente_id)
            if not self.conexiones_por_curso[curso_id]:
                del self.conexiones_por_curso[curso_id]
        
        logger.info(f"Cliente {cliente_id} desuscrito de curso {curso_id}")
        return True
    
    async def enviar_actualizacion_curso(self, curso_id: str, datos_curso: Dict):
        """
        Envía actualización de un curso a todos los clientes suscritos
        """
        if curso_id not in self.conexiones_por_curso:
            return 0
        
        mensaje = {
            "tipo": "curso_actualizado",
            "curso_id": curso_id,
            "datos": datos_curso,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        clientes_notificados = 0
        desconectados = []
        
        for cliente_id in list(self.conexiones_por_curso[curso_id]):
            try:
                if cliente_id in self.active_connections:
                    ws = self.active_connections[cliente_id]['websocket']
                    await ws.send_json(mensaje)
                    clientes_notificados += 1
                else:
                    desconectados.append(cliente_id)
            except Exception as e:
                logger.error(f"Error enviando a {cliente_id}: {e}")
                desconectados.append(cliente_id)
        
        # Limpiar conexiones muertas
        for cliente_id in desconectados:
            await self.desconectar(cliente_id)
        
        logger.info(f"Actualización de {curso_id} enviada a {clientes_notificados} clientes")
        return clientes_notificados
    
    async def notificar_inscripcion(self, curso_id: str, cupos_disponibles: int, nombre_usuario: str):
        """
        Notifica a todos los clientes sobre una nueva inscripción
        (reducción de cupos)
        """
        if curso_id not in self.conexiones_por_curso:
            return 0
        
        mensaje = {
            "tipo": "inscripcion_procesada",
            "curso_id": curso_id,
            "cupos_disponibles": cupos_disponibles,
            "nuevo_usuario": nombre_usuario,
            "timestamp": datetime.utcnow().isoformat(),
            "evento": "Un nuevo estudiante se inscribió"
        }
        
        clientes_notificados = 0
        desconectados = []
        
        for cliente_id in list(self.conexiones_por_curso[curso_id]):
            try:
                if cliente_id in self.active_connections:
                    ws = self.active_connections[cliente_id]['websocket']
                    await ws.send_json(mensaje)
                    clientes_notificados += 1
                else:
                    desconectados.append(cliente_id)
            except Exception as e:
                logger.error(f"Error notificando a {cliente_id}: {e}")
                desconectados.append(cliente_id)
        
        # Limpiar conexiones muertas
        for cliente_id in desconectados:
            await self.desconectar(cliente_id)
        
        return clientes_notificados
    
    async def enviar_mensaje_personal(self, cliente_id: str, mensaje: Dict):
        """Envía un mensaje a un cliente específico"""
        if cliente_id not in self.active_connections:
            return False
        
        try:
            ws = self.active_connections[cliente_id]['websocket']
            await ws.send_json(mensaje)
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje personal a {cliente_id}: {e}")
            await self.desconectar(cliente_id)
            return False
    
    async def enviar_heartbeat(self):
        """Envía un latido a todos los clientes conectados"""
        desconectados = []
        
        for cliente_id in list(self.active_connections.keys()):
            try:
                ws = self.active_connections[cliente_id]['websocket']
                await ws.send_json({
                    "tipo": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.warning(f"Heartbeat falló para {cliente_id}: {e}")
                desconectados.append(cliente_id)
        
        # Limpiar conexiones muertas
        for cliente_id in desconectados:
            await self.desconectar(cliente_id)
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de las conexiones"""
        return {
            "conexiones_activas": len(self.active_connections),
            "cursos_con_suscriptores": len(self.conexiones_por_curso),
            "suscriptores_por_curso": {
                curso_id: len(clientes)
                for curso_id, clientes in self.conexiones_por_curso.items()
            }
        }


# Instancia global del gerenciador de conexiones
manager = ConnectionManager()
