"""Cria as tabelas e popula o banco com os dados de exemplo (idempotente).

Usuários de demonstração (senha: cora123):
    coord@cora.app    — Coordenação
    prof@cora.app     — Professor
    familia@cora.app  — Família (responsável pelo Pedro)
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import data, models
from .db import Base, SessionLocal, engine
from .security import hash_senha

SENHA_DEMO = "cora123"


def init_db() -> None:
    """Cria as tabelas e faz o seed se o banco estiver vazio."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(models.Escola).limit(1)) is None:
            _seed(db)


def _seed(db: Session) -> None:
    escola = models.Escola(nome=data.ESCOLA["nome"], cidade=data.ESCOLA["cidade"])
    db.add(escola)
    db.flush()  # garante escola.id

    senha = hash_senha(SENHA_DEMO)
    coord = models.Usuario(
        nome="Ana Coordenação", email="coord@cora.app", senha_hash=senha,
        papel=models.COORDENACAO, escola_id=escola.id,
    )
    prof = models.Usuario(
        nome="Prof. Marina", email="prof@cora.app", senha_hash=senha,
        papel=models.PROFESSOR, escola_id=escola.id,
    )
    familia = models.Usuario(
        nome=data.RESPONSAVEL["nome"], email="familia@cora.app", senha_hash=senha,
        papel=models.FAMILIA, escola_id=escola.id,
        filho_nome=data.RESPONSAVEL["filho"], turma=data.RESPONSAVEL["turma"],
        idioma=data.RESPONSAVEL["idioma"],
    )
    db.add_all([coord, prof, familia])

    for c in data.COMUNICADOS:
        db.add(models.Comunicado(
            escola_id=escola.id, titulo=c["titulo"], autor=c["autor"], turma=c["turma"],
            categoria=c["categoria"], corpo=c["corpo"], precisa_confirmar=c["precisa_confirmar"],
            enviado_em=c["enviado_em"], total_familias=c["total_familias"],
            leram=c["leram"], confirmaram=c["confirmaram"],
        ))

    for t in data.TAREFAS:
        db.add(models.Tarefa(
            escola_id=escola.id, turma="5º Ano A", disciplina=t["disciplina"],
            titulo=t["titulo"], entrega=t["entrega"], status=t["status"],
        ))

    for e in data.EVENTOS:
        db.add(models.Evento(escola_id=escola.id, data=e["data"], titulo=e["titulo"], tipo=e["tipo"]))

    db.flush()  # garante familia.id
    for a in data.AUTORIZACOES:
        db.add(models.Autorizacao(
            usuario_id=familia.id, titulo=a["titulo"], data_evento=a["data_evento"],
            descricao=a["descricao"], status=a["status"],
        ))

    db.commit()
