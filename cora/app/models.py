"""Modelos ORM (SQLAlchemy 2.0) — os dados transacionais do Cora.

Dados de referência/analytics de demonstração (engajamento, integrações,
cardápio, frequência, financeiro) seguem em data.py por enquanto; no MVP
completo eles vêm de integrações com o ERP.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Papéis de usuário
COORDENACAO = "coordenacao"
PROFESSOR = "professor"
FAMILIA = "familia"


class Escola(Base):
    __tablename__ = "escolas"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160))
    cidade: Mapped[str] = mapped_column(String(120), default="")

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="escola")


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20))  # coordenacao | professor | familia
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))

    # Específico do perfil Família
    filho_nome: Mapped[str] = mapped_column(String(120), default="")
    turma: Mapped[str] = mapped_column(String(60), default="")
    idioma: Mapped[str] = mapped_column(String(10), default="pt-BR")

    escola: Mapped["Escola"] = relationship(back_populates="usuarios")


class Comunicado(Base):
    __tablename__ = "comunicados"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    titulo: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str] = mapped_column(String(120))
    turma: Mapped[str] = mapped_column(String(60))
    categoria: Mapped[str] = mapped_column(String(40))
    corpo: Mapped[str] = mapped_column(Text)
    precisa_confirmar: Mapped[bool] = mapped_column(Boolean, default=False)
    enviado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Contadores denormalizados (no produto completo, derivados da tabela Leitura)
    total_familias: Mapped[int] = mapped_column(Integer, default=0)
    leram: Mapped[int] = mapped_column(Integer, default=0)
    confirmaram: Mapped[int] = mapped_column(Integer, default=0)


class Leitura(Base):
    """Estado de leitura/confirmação por usuário — persistência real de verdade."""

    __tablename__ = "leituras"
    id: Mapped[int] = mapped_column(primary_key=True)
    comunicado_id: Mapped[int] = mapped_column(ForeignKey("comunicados.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    lido: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    lido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Tarefa(Base):
    __tablename__ = "tarefas"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    turma: Mapped[str] = mapped_column(String(60), default="")
    disciplina: Mapped[str] = mapped_column(String(60))
    titulo: Mapped[str] = mapped_column(String(200))
    entrega: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pendente")


class Evento(Base):
    __tablename__ = "eventos"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    data: Mapped[date] = mapped_column(Date)
    titulo: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(40), default="evento")


class Autorizacao(Base):
    __tablename__ = "autorizacoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    data_evento: Mapped[date] = mapped_column(Date)
    descricao: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pendente")
