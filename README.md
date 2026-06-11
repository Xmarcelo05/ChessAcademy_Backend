# 🏰 Chess Academy Backend API

Backend profesional en **FastAPI** para la plataforma de cursos de ajedrez. Diseñado para desplegarse en **AWS App Runner** con **CI/CD automatizado**.

---

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación Local](#instalación-local)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [API REST Endpoints](#api-rest-endpoints)
6. [WebSocket - Tiempo Real](#websocket---tiempo-real)
7. [Configuración CORS](#configuración-cors)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Despliegue en AWS App Runner](#despliegue-en-aws-app-runner)
10. [Variables de Entorno](#variables-de-entorno)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción del Proyecto

Backend de alta disponibilidad que proporciona:

✅ **API REST** para gestionar cursos e inscripciones
✅ **WebSocket** para sincronización en tiempo real
✅ **CORS seguro** configurado para Azure Frontend
✅ **Datos en memoria** (sin BD para MVP)
✅ **Logging y monitoreo** listo para producción
✅ **Health checks** para AWS App Runner
✅ **CI/CD automático** con GitHub Actions

**Stack Tecnológico:**
- Framework: FastAPI (Python 3.11)
- Servidor ASGI: Uvicorn
- WebSocket: FastAPI WebSockets nativo
- Contenedor: Docker
- Orquestación: AWS App Runner
- CI/CD: GitHub Actions
- Registry: Amazon ECR (Elastic Container Registry)

---

## 📦 Requisitos Previos

### Local
- Python 3.11+
- Docker & Docker Compose
- Git

### Para AWS Deployment
- Cuenta de AWS
- AWS CLI v2 configurado
- GitHub cuenta con acceso al repo
- ECR repository creado en AWS

---

## 🚀 Instalación Local

### 1. Clonar Repositorio
```bash
git clone https://github.com/tuusername/chess-backend.git
cd chess-backend
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv

# En Linux/Mac
source venv/bin/activate

# En Windows
venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env

# Editar .env con tus valores
nano .env  # O usa tu editor favorito
```

### 5. Ejecutar Localmente
```bash
# Opción A: Con Uvicorn directamente
python -m uvicorn app.main:app --reload

# Opción B: Con Docker Compose
docker-compose up -d
```

**La API estará disponible en:**
- http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📁 Estructura del Proyecto

```
chess-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal FastAPI
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # Endpoints REST
│   │   └── websocket.py       # Endpoint WebSocket
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuración global
│   │   └── database.py        # Simulación BD en memoria
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Esquemas Pydantic
│   │
│   └── websockets/
│       ├── __init__.py
│       └── manager.py         # Gerenciador de conexiones WS
│
├── tests/
│   ├── __init__.py
│   └── conftest.py           # Fixtures de pytest
│
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD Pipeline (GitHub Actions)
│
├── requirements.txt           # Dependencias Python
├── Dockerfile                 # Imagen Docker
├── docker-compose.yml        # Desarrollo local
├── .env.example             # Ejemplo de variables
└── README.md                # Este archivo
```

---

## 🔌 API REST Endpoints

### Health Check
```bash
GET /api/v1/health
Response: { "status": "healthy", "version": "1.0.0", ... }
```

### Listar Cursos
```bash
GET /api/v1/cursos
GET /api/v1/cursos?nivel=principiante
GET /api/v1/cursos?skip=0&limit=10

Response:
[
  {
    "id": "curso_001",
    "nombre": "Ajedrez para Principiantes",
    "nivel": "principiante",
    "cupos_disponibles": 12,
    "cupos_totales": 30,
    "porcentaje_disponibilidad": 40.0,
    "estado": "disponible",
    "precio": 29.99,
    ...
  }
]
```

### Obtener Curso Específico
```bash
GET /api/v1/cursos/{curso_id}

Response: { curso completo con estado }
```

### Verificar Disponibilidad
```bash
GET /api/v1/cursos/{curso_id}/disponibilidad

Response:
{
  "curso_id": "curso_001",
  "cupos_disponibles": 12,
  "cupos_totales": 30,
  "porcentaje_disponibilidad": 40.0,
  "estado": "disponible",
  "timestamp": "2024-06-15T10:30:00"
}
```

### Crear Inscripción ⭐
```bash
POST /api/v1/inscripciones
Content-Type: application/json

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

Response: (201 Created)
{
  "id_inscripcion": "insc_abc123",
  "usuario_nombre": "Juan García",
  "curso_nombre": "Ajedrez para Principiantes",
  "estado": "confirmada",
  "numero_referencia": "REF-20240615-ABC123",
  "proximo_evento": "2024-07-01"
}
```

### Obtener Inscripciones de Usuario
```bash
GET /api/v1/usuarios/{email}/inscripciones

Response:
{
  "email": "juan@example.com",
  "total_inscripciones": 2,
  "inscripciones": [...]
}
```

### Cancelar Inscripción
```bash
POST /api/v1/inscripciones/{id_inscripcion}/cancelar

Response: (200 OK)
{
  "mensaje": "Inscripción cancelada exitosamente",
  "id_inscripcion": "insc_abc123",
  "estado": "cancelada"
}
```

### Estadísticas
```bash
GET /api/v1/stats

Response:
{
  "datos_cursos": {
    "total_cursos": 4,
    "total_usuarios": 50,
    "inscripciones_activas": 45,
    "tasa_ocupacion": "75.00%"
  },
  "conexiones_websocket": {
    "conexiones_activas": 12,
    "cursos_con_suscriptores": 3
  }
}
```

---

## 🌐 WebSocket - Tiempo Real

### Conectar al WebSocket

```javascript
// Frontend JavaScript
const clienteId = 'cliente_123';
const ws = new WebSocket(`wss://tu-dominio.com/ws/${clienteId}`);

ws.onopen = (event) => {
  console.log('Conectado');
  
  // Suscribirse a un curso
  ws.send(JSON.stringify({
    tipo: 'suscribir',
    curso_id: 'curso_001'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Mensaje recibido:', data);
  
  if (data.tipo === 'inscripcion_procesada') {
    // Actualizar interfaz con nuevos cupos
    console.log(`Cupos disponibles: ${data.cupos_disponibles}`);
  }
};
```

### Mensajes del Cliente

**Suscribirse a Curso**
```json
{
  "tipo": "suscribir",
  "curso_id": "curso_001"
}
```

**Desuscribirse de Curso**
```json
{
  "tipo": "desuscribir",
  "curso_id": "curso_001"
}
```

**Obtener Lista de Cursos**
```json
{
  "tipo": "obtener_cursos"
}
```

**Obtener Estadísticas**
```json
{
  "tipo": "obtener_estadisticas"
}
```

**Latido (Ping)**
```json
{
  "tipo": "ping"
}
```

### Mensajes del Servidor

**Conexión Establecida**
```json
{
  "tipo": "conexion_establecida",
  "cliente_id": "cliente_123",
  "mensaje": "Conectado al servidor en tiempo real",
  "timestamp": "2024-06-15T10:30:00"
}
```

**Inscripción Procesada** ⭐
```json
{
  "tipo": "inscripcion_procesada",
  "curso_id": "curso_001",
  "cupos_disponibles": 11,
  "nuevo_usuario": "Juan García",
  "evento": "Un nuevo estudiante se inscribió",
  "timestamp": "2024-06-15T10:30:00"
}
```

**Curso Actualizado**
```json
{
  "tipo": "curso_actualizado",
  "curso_id": "curso_001",
  "datos": { /* Datos completos del curso */ },
  "timestamp": "2024-06-15T10:30:00"
}
```

---

## 🔒 Configuración CORS

El backend está configurado para aceptar peticiones **SOLO** desde:

```python
# app/core/config.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",              # Desarrollo local
    "https://tudominio.azurewebsites.net" # Azure Production
]
```

**Para cambiar los orígenes permitidos:**

1. Editar `.env`:
   ```
   AZURE_FRONTEND_URL=https://tu-nuevo-dominio.azurewebsites.net
   ```

2. Reiniciar la aplicación

**Verificar CORS:**
```bash
# Test desde línea de comandos
curl -X GET http://localhost:8000/api/v1/cursos \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

---

## 🚀 CI/CD Pipeline

### Flujo Automático

```
1. Push a GitHub (rama main/develop)
   ↓
2. GitHub Actions dispara workflow
   ↓
3. Build & Test (Pytest, Flake8, MyPy)
   ↓
4. Build imagen Docker
   ↓
5. Push a Amazon ECR
   ↓
6. Deploy a AWS App Runner
   ↓
7. Verificar Health Checks
   ↓
8. Notificación en Slack (opcional)
```

### Workflow en .github/workflows/deploy.yml

**Pasos del Pipeline:**

1. **Build & Test** (Ubuntu Latest)
   - Checkout código
   - Setup Python 3.11
   - Instalar dependencias
   - Correr tests (Pytest)
   - Linting (Flake8)
   - Type checking (MyPy)

2. **Build & Push Docker**
   - Autenticar con AWS
   - Login a ECR
   - Build imagen Docker (multi-stage)
   - Push a ECR con tag latest + SHA

3. **Deploy**
   - Trigger despliegue en App Runner
   - Esperar confirmación (polling cada 10s)
   - Máximo 10 minutos de espera

4. **Notificaciones**
   - Notificación a Slack del resultado

---

## 🏗️ Despliegue en AWS App Runner

### Paso 1: Configuración Inicial en AWS

```bash
# 1. Crear repositorio ECR público
aws ecr create-repository \
  --repository-name chess-backend \
  --encryption-configuration encryptionType=AES256 \
  --region us-east-1

# 2. Crear App Runner Service
aws apprunner create-service \
  --service-name chess-backend \
  --source-configuration '
    {
      "ImageRepository": {
        "ImageIdentifier": "public.ecr.aws/YOUR_ACCOUNT_ID/chess-backend:latest",
        "ImageRepositoryType": "ECR_PUBLIC",
        "ImageConfiguration": {
          "Port": "8000"
        }
      },
      "AutoDeploymentsEnabled": true
    }
  ' \
  --instance-configuration "Cpu=1 vCPU,Memory=2GB" \
  --tags Key=Project,Value=ChessAcademy Key=Environment,Value=Production \
  --region us-east-1
```

### Paso 2: Configurar GitHub Secrets

En **Settings → Secrets and Variables → Actions**:

```
AWS_ACCESS_KEY_ID = tu_access_key
AWS_SECRET_ACCESS_KEY = tu_secret_key
AWS_APPRUNNER_SERVICE_ARN = arn:aws:apprunner:us-east-1:xxxxx:service/chess-backend/xxxxx
SLACK_WEBHOOK_URL = https://hooks.slack.com/... (opcional)
```

### Paso 3: Variables de Entorno en App Runner

En AWS Console → App Runner → chess-backend → Configuration:

```
ENVIRONMENT = production
AZURE_FRONTEND_URL = https://tu-landing-page.azurewebsites.net
SECRET_KEY = tu-clave-secreta-produccion
LOG_LEVEL = INFO
```

### Paso 4: Primera Ejecución

```bash
# Push a main para disparar workflow
git add .
git commit -m "Initial deployment configuration"
git push origin main

# Monitorear en GitHub Actions
# o en AWS Console → App Runner → chess-backend → Deployment logs
```

### Monitoreo Post-Despliegue

```bash
# Verificar estado del servicio
aws apprunner describe-service \
  --service-arn arn:aws:apprunner:us-east-1:xxxxx:service/chess-backend/xxxxx \
  --region us-east-1

# Ver logs
aws apprunner list-service-deployments \
  --service-arn arn:aws:apprunner:us-east-1:xxxxx:service/chess-backend/xxxxx \
  --region us-east-1
```

---

## 🔧 Variables de Entorno

### Desarrollo (.env)
```env
ENVIRONMENT=development
AZURE_FRONTEND_URL=http://localhost:3000
DEBUG=True
LOG_LEVEL=DEBUG
```

### Producción (AWS)
```env
ENVIRONMENT=production
AZURE_FRONTEND_URL=https://tu-dominio.azurewebsites.net
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=clave-muy-larga-y-aleatoria
```

---

## 🧪 Testing

```bash
# Correr todos los tests
pytest

# Con cobertura
pytest --cov=app

# Solo un archivo
pytest tests/test_routes.py

# Con output verbose
pytest -v

# Solo tests que matchean un patrón
pytest -k "test_inscripcion"
```

---

## 📊 Monitoreo y Logs

### CloudWatch Logs (AWS)

```bash
# Ver logs en tiempo real
aws logs tail /aws/apprunner/chess-backend/logs --follow
```

### Localmente

```bash
# Con nivel DEBUG
LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload

# Ver logs en archivo
python -m uvicorn app.main:app > chess-backend.log 2>&1
```

---

## 🐛 Troubleshooting

### Error: CORS no funciona

```bash
# Verificar que el origen está en la lista
grep "AZURE_FRONTEND_URL" .env

# Reiniciar la app para aplicar cambios
docker-compose restart

# Test CORS
curl -X OPTIONS http://localhost:8000/api/v1/cursos \
  -H "Origin: http://localhost:3000" -v
```

### Error: Puerto 8000 en uso

```bash
# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: Conexión WebSocket rechazada

1. Verificar URL correcta: `wss://` en producción, `ws://` en desarrollo
2. Verificar que cliente_id no está vacío
3. Revisar logs en CloudWatch

### Error: Tests fallan localmente

```bash
# Limpiar caché de Python
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Recursos Adicionales

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

## 📝 Notas Importantes

⚠️ **Seguridad en Producción:**
- Cambiar `SECRET_KEY` en `.env`
- Usar HTTPS/WSS en producción
- Implementar autenticación cuando sea necesario
- No commitear `.env` con valores reales

💾 **Futuras Mejoras:**
- Integración con PostgreSQL
- Autenticación con JWT
- Rate limiting
- Caché distribuido (Redis)
- Pagos con Stripe/PayPal
- Emails con SendGrid/SES

---

## 🤝 Contribuir

1. Crear rama: `git checkout -b feature/mi-feature`
2. Hacer cambios
3. Tests: `pytest`
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/mi-feature`
6. Pull Request

---

## 📞 Soporte

Para dudas o problemas:
1. Revisar logs: `docker-compose logs chess-backend`
2. Verificar `.env`: `cat .env | grep -v "^#"`
3. Crear issue en GitHub

---

**Creado con ❤️ para Chess Academy**

**Versión:** 1.0.0  
**Última actualización:** 2024-06-15
