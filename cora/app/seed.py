"""Cria as tabelas e popula o banco com os dados de exemplo (idempotente).

Usuários de demonstração (senha: cora123):
    coord@cora.app    — Coordenação
    prof@cora.app     — Professor
    familia@cora.app  — Família (responsável pelo Pedro)
"""

from __future__ import annotations

import math
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import ai, data, models
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
    direcao = models.Usuario(
        nome="Roberto Diretor", email="dir@cora.app", senha_hash=senha,
        papel=models.DIRECAO, escola_id=escola.id,
    )
    secretaria = models.Usuario(
        nome="Carla Secretaria", email="sec@cora.app", senha_hash=senha,
        papel=models.SECRETARIA, escola_id=escola.id,
    )
    financeiro = models.Usuario(
        nome="Marcos Financeiro", email="fin@cora.app", senha_hash=senha,
        papel=models.FINANCEIRO, escola_id=escola.id,
    )
    familia = models.Usuario(
        nome=data.RESPONSAVEL["nome"], email="familia@cora.app", senha_hash=senha,
        papel=models.FAMILIA, escola_id=escola.id,
        filho_nome=data.RESPONSAVEL["filho"], turma=data.RESPONSAVEL["turma"],
        idioma=data.RESPONSAVEL["idioma"],
        telefone="+5548999990000", whatsapp_optin=True,
    )
    db.add_all([coord, prof, direcao, secretaria, financeiro, familia])

    coms_objs = []
    for c in data.COMUNICADOS:
        obj = models.Comunicado(
            escola_id=escola.id, titulo=c["titulo"], autor=c["autor"], turma=c["turma"],
            categoria=c["categoria"], corpo=c["corpo"], resumo=ai.resumir(c["corpo"]),
            precisa_confirmar=c["precisa_confirmar"],
            enviado_em=c["enviado_em"], total_familias=0, leram=0, confirmaram=c["confirmaram"],
        )
        db.add(obj)
        coms_objs.append(obj)

    for t in data.TAREFAS:
        db.add(models.Tarefa(
            escola_id=escola.id, turma="5º Ano A", disciplina=t["disciplina"],
            titulo=t["titulo"], entrega=t["entrega"], status=t["status"],
        ))

    for e in data.EVENTOS:
        db.add(models.Evento(escola_id=escola.id, data=e["data"], titulo=e["titulo"], tipo=e["tipo"]))

    db.flush()  # garante familia.id e os ids dos comunicados
    for a in data.AUTORIZACOES:
        db.add(models.Autorizacao(
            usuario_id=familia.id, titulo=a["titulo"], data_evento=a["data_evento"],
            descricao=a["descricao"], status=a["status"],
        ))

    # --- Famílias extras + leituras (alimentam os analytics reais) ---
    # perfil -> (fração de comunicados lidos, dias desde a última leitura)
    perfis = {"alto": (0.95, 1), "medio": (0.70, 3), "baixo": (0.40, 6), "sumido": (0.15, 12)}
    extras_def = [
        ("5º Ano A", "Família Souza", "souza@cora.app", True, "alto"),
        ("5º Ano A", "Família Mendes", "mendes@cora.app", True, "medio"),
        ("5º Ano B", "Família Oliveira", "oliveira@cora.app", False, "baixo"),
        ("5º Ano B", "Família Lima", "lima@cora.app", True, "sumido"),
        ("3º Ano A", "Família Dias", "dias@cora.app", True, "baixo"),
        ("3º Ano A", "Família Castro", "castro@cora.app", False, "sumido"),
        ("Infantil II", "Família Rocha", "rocha@cora.app", True, "alto"),
        ("Infantil II", "Família Pires", "pires@cora.app", True, "medio"),
    ]
    extras = []
    for turma, nome, email, optin, perfil in extras_def:
        u = models.Usuario(
            nome=nome, email=email, senha_hash=senha, papel=models.FAMILIA, escola_id=escola.id,
            filho_nome=nome.replace("Família ", "") + " Jr.", turma=turma,
            telefone="+5548900000000", whatsapp_optin=optin,
        )
        db.add(u)
        extras.append((u, perfil))
    db.flush()

    leram = {c.id: 0 for c in coms_objs}
    total = {c.id: 0 for c in coms_objs}
    for u, perfil in extras:
        frac, dias = perfis[perfil]
        addr = sorted([c for c in coms_objs if c.turma in (u.turma, "Toda a escola")],
                      key=lambda c: c.enviado_em, reverse=True)
        for c in addr:
            total[c.id] += 1
        for c in addr[:math.ceil(frac * len(addr))]:
            db.add(models.Leitura(
                comunicado_id=c.id, usuario_id=u.id, lido=True, confirmado=False,
                lido_em=datetime.combine(data.HOJE - timedelta(days=dias), time(9, 0)),
            ))
            leram[c.id] += 1
    # A família demo (Pedro) conta como destinatária, mas começa sem leituras.
    for c in coms_objs:
        if c.turma in (familia.turma, "Toda a escola"):
            total[c.id] += 1
    for c in coms_objs:
        c.total_familias = total[c.id] or 1
        c.leram = leram[c.id]

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

    # Ficha de saúde + medicação autorizada + uma administração registrada
    db.add(models.FichaSaude(
        escola_id=escola.id, usuario_id=familia.id, aluno_nome=familia.filho_nome,
        tipo_sanguineo="O+",
        alergias="Amendoim e frutos do mar (reação moderada).",
        condicoes="Asma leve — pode precisar da bombinha após esforço físico.",
        restricoes="Sem amendoim na alimentação.",
        contato_emergencia="Juliana Prado — (48) 99999-0000",
        convenio="Unimed — carteirinha 1234 5678",
        observacoes="",
    ))
    med = models.Medicacao(
        escola_id=escola.id, usuario_id=familia.id, aluno_nome=familia.filho_nome,
        nome="Salbutamol (bombinha)", dosagem="2 jatos", horario="se necessário",
        instrucoes="Em caso de falta de ar após educação física. Avisar a família.",
        autorizado=True, ativo=True, criado_em=datetime(2026, 6, 10, 8, 0),
    )
    db.add(med)
    db.flush()
    db.add(models.AdministracaoMed(
        medicacao_id=med.id, administrado_por="Enfermaria — Coordenação",
        administrado_em=datetime(2026, 6, 16, 15, 20), dose="2 jatos",
        observacao="Após a aula de Ed. Física; melhorou em 10 min.",
    ))

    db.commit()
