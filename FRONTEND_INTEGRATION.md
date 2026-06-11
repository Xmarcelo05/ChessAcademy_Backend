# 🔗 INTEGRACIÓN FRONTEND-BACKEND

Guía para conectar el **Frontend en Azure** con el **Backend en AWS**.

---

## 📝 Tabla de Contenidos

1. [URLs de los Servidores](#urls-de-los-servidores)
2. [Configuración de CORS](#configuración-de-cors)
3. [Cliente HTTP (REST)](#cliente-http-rest)
4. [Cliente WebSocket](#cliente-websocket)
5. [Flujo de Inscripción Completo](#flujo-de-inscripción-completo)
6. [Troubleshooting](#troubleshooting)

---

## 🌍 URLs de los Servidores

### Desarrollo Local
```
Frontend:  http://localhost:3000
Backend:   http://localhost:8000
WebSocket: ws://localhost:8000/ws/cliente_123
```

### Producción (Azure + AWS)
```
Frontend:  https://tu-landing-page.azurewebsites.net
Backend:   https://chess-backend.xxxx.run.amazonaws.com
WebSocket: wss://chess-backend.xxxx.run.amazonaws.com/ws/cliente_123
```

---

## 🔒 Configuración de CORS

El backend está configurado en `app/core/config.py` para permitir orígenes específicos.

### Variable de Entorno
```env
AZURE_FRONTEND_URL=https://tu-landing-page.azurewebsites.net
```

**El backend automáticamente:**
- Agregará este origen a la lista permitida
- Permitirá métodos: GET, POST, PUT, DELETE, OPTIONS, PATCH
- Permitirá todos los headers
- Habilitará credentials (cookies)

### Verificar CORS (desde tu frontend)
```javascript
// Si ves este error, CORS no está configurado correctamente:
// "Access to XMLHttpRequest at 'https://backend.com/api/v1/cursos'
//  from origin 'https://frontend.com' has been blocked by CORS policy"

// Solucionarlo:
// 1. Verificar que AZURE_FRONTEND_URL en .env del backend es correcto
// 2. Asegurarse que estás usando exactamente esa URL (sin www., con https, etc)
// 3. Reiniciar el backend
```

---

## 🔌 Cliente HTTP (REST)

### Instalación
```bash
npm install axios
# O si usas fetch (nativo, sin dependencias)
```

### Configuración Base
```javascript
// src/api/client.js
import axios from 'axios';

// Detectar ambiente
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true  // Importante para CORS con cookies
});

export default apiClient;
```

### Ejemplo: Listar Cursos
```javascript
// src/api/cursos.js
import apiClient from './client';

export const listarCursos = async (nivel = null) => {
  try {
    const params = nivel ? { nivel } : {};
    const response = await apiClient.get('/api/v1/cursos', { params });
    return response.data;
  } catch (error) {
    console.error('Error listando cursos:', error);
    throw error;
  }
};

export const obtenerCursoDetalle = async (cursoId) => {
  try {
    const response = await apiClient.get(`/api/v1/cursos/${cursoId}`);
    return response.data;
  } catch (error) {
    console.error('Error obteniendo curso:', error);
    throw error;
  }
};

export const verificarDisponibilidad = async (cursoId) => {
  try {
    const response = await apiClient.get(`/api/v1/cursos/${cursoId}/disponibilidad`);
    return response.data;
  } catch (error) {
    console.error('Error verificando disponibilidad:', error);
    throw error;
  }
};
```

### Ejemplo: Crear Inscripción
```javascript
// src/api/inscripciones.js
import apiClient from './client';

export const crearInscripcion = async (datosInscripcion) => {
  try {
    const response = await apiClient.post('/api/v1/inscripciones', {
      usuario: {
        nombre: datosInscripcion.nombre,
        apellido: datosInscripcion.apellido,
        email: datosInscripcion.email,
        telefono: datosInscripcion.telefono,
        nivel_experiencia: datosInscripcion.nivelExperiencia,
        fecha_nacimiento: datosInscripcion.fechaNacimiento,
      },
      curso_id: datosInscripcion.cursoId,
      fecha_inicio_preferida: datosInscripcion.fechaInicioPref,
      notas: datosInscripcion.notas || '',
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 409) {
      throw new Error('No hay cupos disponibles');
    }
    throw error;
  }
};

export const obtenerInscripcionesUsuario = async (email) => {
  try {
    const response = await apiClient.get(`/api/v1/usuarios/${email}/inscripciones`);
    return response.data;
  } catch (error) {
    console.error('Error obteniendo inscripciones:', error);
    throw error;
  }
};
```

### Uso en Componente React
```jsx
// src/components/CursosList.jsx
import { useEffect, useState } from 'react';
import { listarCursos } from '../api/cursos';

export default function CursosList() {
  const [cursos, setCursos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cargarCursos = async () => {
      try {
        setLoading(true);
        const data = await listarCursos();
        setCursos(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    cargarCursos();
  }, []);

  if (loading) return <div>Cargando cursos...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {cursos.map(curso => (
        <div key={curso.id}>
          <h3>{curso.nombre}</h3>
          <p>Nivel: {curso.nivel}</p>
          <p>Cupos: {curso.cupos_disponibles}/{curso.cupos_totales}</p>
          <p>Estado: {curso.estado}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## 🔌 Cliente WebSocket

### Configuración
```javascript
// src/api/websocket.js
class WebSocketClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.ws = null;
    this.clienteId = this.generarClienteId();
    this.listeners = {};
  }

  generarClienteId() {
    return `cliente_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  conectar() {
    return new Promise((resolve, reject) => {
      try {
        const url = `${this.baseURL}/ws/${this.clienteId}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('WebSocket conectado');
          this.emit('conectado');
          resolve();
        };

        this.ws.onmessage = (event) => {
          const mensaje = JSON.parse(event.data);
          console.log('Mensaje recibido:', mensaje);
          this.emit(mensaje.tipo, mensaje);
        };

        this.ws.onerror = (error) => {
          console.error('Error WebSocket:', error);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket desconectado');
          this.emit('desconectado');
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  enviar(mensaje) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(mensaje));
    } else {
      console.error('WebSocket no está abierto');
    }
  }

  suscribirse(cursoId) {
    this.enviar({
      tipo: 'suscribir',
      curso_id: cursoId,
    });
  }

  desuscribirse(cursoId) {
    this.enviar({
      tipo: 'desuscribir',
      curso_id: cursoId,
    });
  }

  obtenerCursos() {
    this.enviar({
      tipo: 'obtener_cursos',
    });
  }

  on(evento, callback) {
    if (!this.listeners[evento]) {
      this.listeners[evento] = [];
    }
    this.listeners[evento].push(callback);
  }

  emit(evento, datos) {
    if (this.listeners[evento]) {
      this.listeners[evento].forEach(callback => callback(datos));
    }
  }

  desconectar() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Exportar instancia singleton
export const ws = new WebSocketClient(
  process.env.REACT_APP_WS_URL || 'ws://localhost:8000'
);
```

### Uso en React
```jsx
// src/components/InscripcionFormulario.jsx
import { useEffect, useState } from 'react';
import { ws } from '../api/websocket';
import { crearInscripcion } from '../api/inscripciones';

export default function InscripcionFormulario({ cursoId }) {
  const [cuposDisponibles, setCuposDisponibles] = useState(null);
  const [inscribiendo, setInscribiendo] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    email: '',
    telefono: '',
    nivelExperiencia: 'principiante',
  });

  useEffect(() => {
    // Conectar WebSocket y suscribirse al curso
    const conectar = async () => {
      try {
        await ws.conectar();
        ws.suscribirse(cursoId);

        // Escuchar actualizaciones de inscripción
        ws.on('inscripcion_procesada', (datos) => {
          console.log('Nueva inscripción procesada:', datos);
          setCuposDisponibles(datos.cupos_disponibles);
          // Aquí puedes actualizar la UI con los nuevos cupos
        });
      } catch (error) {
        console.error('Error conectando WebSocket:', error);
      }
    };

    conectar();

    return () => {
      ws.desuscribirse(cursoId);
    };
  }, [cursoId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setInscribiendo(true);

    try {
      const resultado = await crearInscripcion({
        ...formData,
        cursoId,
        fechaInicioPref: '2024-07-01', // Del formulario
      });

      alert(`¡Inscripción exitosa! 🎉\nNúmero de referencia: ${resultado.numero_referencia}`);
      
      // Limpiar formulario
      setFormData({
        nombre: '',
        apellido: '',
        email: '',
        telefono: '',
        nivelExperiencia: 'principiante',
      });
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setInscribiendo(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        name="nombre"
        placeholder="Nombre"
        value={formData.nombre}
        onChange={handleChange}
        required
      />
      <input
        type="text"
        name="apellido"
        placeholder="Apellido"
        value={formData.apellido}
        onChange={handleChange}
        required
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleChange}
        required
      />
      <input
        type="tel"
        name="telefono"
        placeholder="Teléfono"
        value={formData.telefono}
        onChange={handleChange}
      />
      <select
        name="nivelExperiencia"
        value={formData.nivelExperiencia}
        onChange={handleChange}
      >
        <option value="principiante">Principiante</option>
        <option value="intermedio">Intermedio</option>
        <option value="avanzado">Avanzado</option>
      </select>
      <button type="submit" disabled={inscribiendo}>
        {inscribiendo ? 'Inscribiendo...' : 'Inscribirse'}
      </button>
    </form>
  );
}
```

---

## 🎯 Flujo de Inscripción Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                      USUARIO EN FRONTEND                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ↓
                    1. VE LISTA DE CURSOS
                    GET /api/v1/cursos
                                │
                                ↓
        ┌─────────────────────────────────────────┐
        │ WebSocket: se suscribe al curso        │
        │ ws.send({tipo: 'suscribir',            │
        │          curso_id: 'curso_001'})       │
        └─────────────────────────────────────────┘
                                │
                                ↓
                    2. RELLENA FORMULARIO
                    3. HACE CLIC EN "INSCRIBIRSE"
                                │
                                ↓
        ┌─────────────────────────────────────────┐
        │ POST /api/v1/inscripciones             │
        │ Body: {usuario, curso_id, fecha, ...}  │
        └─────────────────────────────────────────┘
                                │
                                ↓
        ┌─────────────────────────────────────────┐
        │ BACKEND PROCESA INSCRIPCIÓN            │
        │ - Valida datos                          │
        │ - Verifica cupos                        │
        │ - Reduce cupos en 1                     │
        │ - Genera número de referencia           │
        └─────────────────────────────────────────┘
                                │
                                ↓
        ┌─────────────────────────────────────────┐
        │ WebSocket NOTIFICACIÓN A TODOS         │
        │ {tipo: 'inscripcion_procesada',         │
        │  cupos_disponibles: 11,                 │
        │  nuevo_usuario: 'Juan García'}          │
        └─────────────────────────────────────────┘
                                │
                                ↓
        ┌─────────────────────────────────────────┐
        │ FRONTEND RECIBE EN TIEMPO REAL          │
        │ - Actualiza cupos sin recargar          │
        │ - Muestra confirmación al usuario       │
        │ - Actualiza lista de cursos             │
        └─────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Error: "CORS Policy" o "No 'Access-Control-Allow-Origin' header"

**Solución:**
```javascript
// 1. Verificar que el origen es exactamente igual
console.log(window.location.origin);
// Debe ser igual a AZURE_FRONTEND_URL en el backend

// 2. Verificar que usas http/https consistentemente
// Incorrecto: mezclando http y https
// Correcto: ambos https en producción

// 3. Reiniciar backend
docker-compose restart
```

### Error: "WebSocket connection failed"

**Solución:**
```javascript
// 1. Verificar protocolo (ws vs wss)
const wsUrl = window.location.protocol === 'https:' 
  ? 'wss://...'  // HTTPS → WSS
  : 'ws://...';  // HTTP → WS

// 2. Verificar que la URL es correcta
const ws = new WebSocket('wss://chess-backend.xxxx.run.amazonaws.com/ws/cliente_123');

// 3. Ver logs en navegador (F12 → Console)
```

### Error: "404 Not Found" en inscripción

**Solución:**
```javascript
// 1. Verificar que el cursoId es válido
console.log('Curso ID:', cursoId);

// 2. Listar cursos disponibles
fetch('https://backend.com/api/v1/cursos')
  .then(r => r.json())
  .then(cursos => console.log(cursos));

// 3. Usar un ID válido de los resultados
```

### Los cupos no se actualizan en tiempo real

**Solución:**
```javascript
// 1. Verificar que WebSocket está conectado
console.log(ws.ws?.readyState); // Debe ser 1 (OPEN)

// 2. Verificar que te suscribiste al curso
ws.suscribirse('curso_001');

// 3. Escuchar el evento correcto
ws.on('inscripcion_procesada', (datos) => {
  console.log('Evento recibido:', datos);
  // Actualizar UI aquí
});
```

---

## 📊 Variables de Entorno (.env del Frontend)

```env
# Development
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Production
REACT_APP_API_URL=https://chess-backend.xxxx.run.amazonaws.com
REACT_APP_WS_URL=wss://chess-backend.xxxx.run.amazonaws.com
```

---

## 📈 Monitoreo

### Desde el Frontend
```javascript
// Verificar conectividad al backend
async function verificarBackend() {
  try {
    const response = await fetch('https://backend.com/api/v1/health');
    const data = await response.json();
    console.log('Backend OK:', data);
  } catch (error) {
    console.error('Backend NO disponible:', error);
  }
}

// Llamar periódicamente
setInterval(verificarBackend, 60000); // Cada minuto
```

### Desde la Línea de Comandos
```bash
# Verificar disponibilidad
curl https://chess-backend.xxxx.run.amazonaws.com/api/v1/health

# Listar cursos
curl https://chess-backend.xxxx.run.amazonaws.com/api/v1/cursos

# Verificar CORS
curl -i -X OPTIONS \
  -H "Origin: https://tu-frontend.azurewebsites.net" \
  https://chess-backend.xxxx.run.amazonaws.com/api/v1/cursos
```

---

## ✅ Checklist de Integración

- [ ] Backend desplegado en AWS App Runner
- [ ] Frontend desplegado en Azure
- [ ] URLs correctas en variables de entorno
- [ ] CORS configurado (AZURE_FRONTEND_URL en backend)
- [ ] REST API funcionando (pruebado con curl)
- [ ] WebSocket funcionando (conecta sin errores)
- [ ] Inscripción completa (desde formulario hasta confirmación)
- [ ] Sincronización en tiempo real (cupos se actualizan)
- [ ] Manejo de errores implementado
- [ ] Logs monitoreados en ambos lados

---

**¡Tu aplicación está lista para producción! 🚀**
