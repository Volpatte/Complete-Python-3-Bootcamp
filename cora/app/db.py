"""Camada de banco de dados do Cora.

SQLite por padrão (roda em qualquer lugar, zero infra). Em produção, basta
definir DATABASE_URL apontando para um Postgres — nenhum código muda.

    export DATABASE_URL=postgresql+psycopg://user:pass@host:5432/cora
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cora.db")

# SQLite precisa desta flag para uso com múltiplas threads (uvicorn).
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency do FastAPI: abre uma sessão por request e fecha ao final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
