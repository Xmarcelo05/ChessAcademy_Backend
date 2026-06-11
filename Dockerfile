# Dockerfile
# Construcción multi-etapa para optimizar el tamaño de la imagen

# ===================== ETAPA 1: BUILDER =====================
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar herramientas de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos
COPY requirements.txt .

# Crear wheels en una carpeta
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ===================== ETAPA 2: RUNTIME =====================
FROM python:3.11-slim

WORKDIR /app

# Instalar solo las dependencias necesarias en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root por seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar wheels del builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Instalar las ruedas
RUN pip install --no-cache /wheels/*

# Copiar código de la aplicación
COPY . .

# Cambiar propietario del directorio
RUN chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check para AWS App Runner
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando para iniciar la aplicación
# AWS App Runner usará este comando para iniciar el servidor
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
