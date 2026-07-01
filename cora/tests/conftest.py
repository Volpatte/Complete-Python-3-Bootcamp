"""Fixtures de teste.

Aponta o banco para um SQLite temporário e garante modo offline (sem IA/WhatsApp
reais) ANTES de importar o app — o app cria/popula o banco no import.
"""

import os
import tempfile

# Configura o ambiente antes de qualquer import do app.
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test_cora.db"
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("WHATSAPP_TOKEN", None)
os.environ.pop("WHATSAPP_PHONE_ID", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def _logado(papel: str) -> TestClient:
    c = TestClient(app)
    c.get(f"/login/demo/{papel}")
    return c


@pytest.fixture
def familia():
    return _logado("familia")


@pytest.fixture
def professor():
    return _logado("professor")


@pytest.fixture
def coord():
    return _logado("coordenacao")
