"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Proporciona un cliente de prueba para la API"""
    return TestClient(app)


@pytest.fixture
def sample_usuario():
    """Usuario de prueba"""
    return {
        "nombre": "Juan",
        "apellido": "García",
        "email": "juan@example.com",
        "telefono": "+34 600 123 456",
        "nivel_experiencia": "principiante",
        "fecha_nacimiento": "1990-05-15"
    }
