"""Cria as tabelas e popula o banco com os dados de exemplo (idempotente).

Usuários de demonstração (senha: cora123):
    coord@cora.app    — Coordenação
    prof@cora.app     — Professor
    familia@cora.app  — Família (responsável pelo Pedro)
"""

from __future__ import annotations

from datetime import datetime

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
        telefone="+5548999990000", whatsapp_optin=True,
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

    # Conversas de exemplo (mensageria pessoa↔pessoa)
    conv_prof = models.Conversa(
        escola_id=escola.id, familia_id=familia.id, canal="Prof. Marina",
        staff_papel=models.PROFESSOR,
        criado_em=datetime(2026, 6, 17, 14, 0), atualizado_em=datetime(2026, 6, 17, 14, 11),
    )
    conv_coord = models.Conversa(
        escola_id=escola.id, familia_id=familia.id, canal="Coordenação",
        staff_papel=models.COORDENACAO,
        criado_em=datetime(2026, 6, 16, 9, 0), atualizado_em=datetime(2026, 6, 16, 9, 30),
    )
    db.add_all([conv_prof, conv_coord])
    db.flush()

    db.add_all([
        models.Mensagem(
            conversa_id=conv_prof.id, autor_id=prof.id, autor_nome=prof.nome,
            autor_papel=models.PROFESSOR, enviado_em=datetime(2026, 6, 17, 14, 2),
            corpo=f"Oi {familia.nome.split(' ')[0]}! O {familia.filho_nome.split(' ')[0]} foi muito bem na atividade de frações hoje 😊",
        ),
        models.Mensagem(
            conversa_id=conv_prof.id, autor_id=prof.id, autor_nome=prof.nome,
            autor_papel=models.PROFESSOR, enviado_em=datetime(2026, 6, 17, 14, 3),
            corpo="Só não esqueça que amanhã a saída é antecipada, às 11h30.",
        ),
        models.Mensagem(
            conversa_id=conv_coord.id, autor_id=coord.id, autor_nome=coord.nome,
            autor_papel=models.COORDENACAO, enviado_em=datetime(2026, 6, 16, 9, 30),
            corpo="Bom dia! A reunião de pais do 5º Ano A está confirmada para 24/06, às 19h.",
        ),
    ])

    # Entregas de WhatsApp de exemplo (status variados para a Central)
    db.add_all([
        models.EntregaWhatsApp(
            escola_id=escola.id, usuario_id=familia.id, destinatario_nome=familia.nome,
            referencia="comunicado:2", resumo="URGENTE: saída antecipada amanhã às 11h30.",
            status="lido", modo="simulado",
            criado_em=datetime(2026, 6, 17, 7, 6), atualizado_em=datetime(2026, 6, 17, 7, 20),
        ),
        models.EntregaWhatsApp(
            escola_id=escola.id, usuario_id=familia.id, destinatario_nome=familia.nome,
            referencia="comunicado:3", resumo="Mensalidade de junho disponível (vence 20/06).",
            status="entregue", modo="simulado",
            criado_em=datetime(2026, 6, 15, 14, 1), atualizado_em=datetime(2026, 6, 15, 14, 2),
        ),
        models.EntregaWhatsApp(
            escola_id=escola.id, usuario_id=familia.id, destinatario_nome=familia.nome,
            referencia="mensagem:1", resumo="Prof. Marina: lembrete da saída antecipada.",
            status="enviado", modo="simulado",
            criado_em=datetime(2026, 6, 17, 14, 3), atualizado_em=datetime(2026, 6, 17, 14, 3),
        ),
    ])

    db.commit()
