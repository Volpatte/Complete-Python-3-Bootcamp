"""Cora — MVP (FastAPI + SQLAlchemy + Jinja2).

Rodar:
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    # abra http://127.0.0.1:8000  → faça login

Banco: SQLite por padrão (cora.db). Defina DATABASE_URL p/ usar Postgres.
Usuários demo (senha: cora123): coord@cora.app · prof@cora.app · familia@cora.app
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import ai, assistant, data, models
from .db import get_db
from .seed import init_db
from .security import autenticar

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Cora", description="Plataforma de relação escola-família")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("CORA_SECRET_KEY", "cora-dev-secret-troque-em-producao"),
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

templates.env.filters["dia"] = lambda d: d.strftime("%d/%m")
templates.env.filters["data_hora"] = lambda d: d.strftime("%d/%m %H:%M")

# Cria as tabelas e faz o seed na carga do app (idempotente).
init_db()


# --------------------------------------------------------------------------- #
# Autenticação / autorização
# --------------------------------------------------------------------------- #
class Redirecionar(Exception):
    def __init__(self, destino: str):
        self.destino = destino


@app.exception_handler(Redirecionar)
async def _handle_redirect(request: Request, exc: Redirecionar):
    return RedirectResponse(exc.destino, status_code=303)


def _home_do(papel: str) -> str:
    return {"coordenacao": "/coordenacao", "professor": "/professor", "familia": "/familia"}.get(papel, "/")


def exigir(*papeis: str):
    """Dependency que garante usuário logado (e, opcionalmente, com certo papel)."""

    def dep(request: Request, db: Session = Depends(get_db)) -> models.Usuario:
        uid = request.session.get("uid")
        user = db.get(models.Usuario, uid) if uid else None
        if user is None:
            raise Redirecionar("/login")
        if papeis and user.papel not in papeis:
            raise Redirecionar(_home_do(user.papel))
        return user

    return dep


def _ctx(request: Request, user: models.Usuario | None = None, **extra) -> dict:
    base = {"request": request, "escola": data.ESCOLA, "ai": ai, "user": user}
    base.update(extra)
    return base


def _responsavel(user: models.Usuario) -> dict:
    return {"nome": user.nome, "filho": user.filho_nome, "turma": user.turma, "idioma": user.idioma}


# --------------------------------------------------------------------------- #
# Login / logout
# --------------------------------------------------------------------------- #
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, erro: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "erro": erro})


@app.post("/login")
def login_post(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    user = autenticar(db, email, senha)
    if not user:
        return RedirectResponse("/login?erro=1", status_code=303)
    request.session["uid"] = user.id
    return RedirectResponse(_home_do(user.papel), status_code=303)


@app.get("/login/demo/{papel}")
def login_demo(request: Request, papel: str, db: Session = Depends(get_db)):
    """Login rápido para demonstração (remover/desativar em produção)."""
    emails = {"coordenacao": "coord@cora.app", "professor": "prof@cora.app", "familia": "familia@cora.app"}
    user = db.scalar(select(models.Usuario).where(models.Usuario.email == emails.get(papel, "")))
    if not user:
        return RedirectResponse("/login", status_code=303)
    request.session["uid"] = user.id
    return RedirectResponse(_home_do(user.papel), status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# --------------------------------------------------------------------------- #
# Home / landing (pública)
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", _ctx(request))


# --------------------------------------------------------------------------- #
# Coordenação
# --------------------------------------------------------------------------- #
@app.get("/coordenacao", response_class=HTMLResponse)
def coordenacao(request: Request, db: Session = Depends(get_db), user=Depends(exigir("coordenacao"))):
    comunicados = list(
        db.scalars(
            select(models.Comunicado)
            .where(models.Comunicado.escola_id == user.escola_id)
            .order_by(models.Comunicado.enviado_em.desc())
        )
    )
    com_total = [c for c in comunicados if c.total_familias]
    media_leitura = (
        round(sum(c.leram / c.total_familias * 100 for c in com_total) / len(com_total))
        if com_total else 0
    )
    return templates.TemplateResponse(
        "coordenacao.html",
        _ctx(
            request, user,
            engajamento=data.ENGAJAMENTO_POR_TURMA,
            familias_risco=data.FAMILIAS_RISCO,
            integracoes=data.INTEGRACOES,
            comunicados=comunicados,
            insight=ai.insight_coordenacao(data.ENGAJAMENTO_POR_TURMA),
            media_leitura=media_leitura,
        ),
    )


# --------------------------------------------------------------------------- #
# Professor
# --------------------------------------------------------------------------- #
def _tarefas(db: Session, escola_id: int):
    return list(db.scalars(select(models.Tarefa).where(models.Tarefa.escola_id == escola_id)))


def _comunicados_prof(db: Session, escola_id: int):
    return list(
        db.scalars(
            select(models.Comunicado)
            .where(models.Comunicado.escola_id == escola_id, models.Comunicado.autor.startswith("Prof"))
            .order_by(models.Comunicado.enviado_em.desc())
        )
    )


@app.get("/professor", response_class=HTMLResponse)
def professor(request: Request, db: Session = Depends(get_db), user=Depends(exigir("professor")), enviado: int = 0):
    return templates.TemplateResponse(
        "professor.html",
        _ctx(
            request, user,
            turmas=data.TURMAS,
            tarefas=_tarefas(db, user.escola_id),
            comunicados=_comunicados_prof(db, user.escola_id),
            preview=None,
            enviado=enviado,
        ),
    )


@app.post("/professor/preview", response_class=HTMLResponse)
def professor_preview(
    request: Request,
    titulo: str = Form(""),
    corpo: str = Form(""),
    turma: str = Form("Toda a escola"),
    db: Session = Depends(get_db),
    user=Depends(exigir("professor")),
):
    prio = ai.prioridade(titulo, corpo)
    preview = {
        "titulo": titulo or "(sem título)",
        "corpo": corpo,
        "turma": turma,
        "resumo": ai.resumir(corpo) if corpo else "",
        "prioridade": prio,
        "traducoes": [ai.traduzir_rotulo(i) for i in ("es", "en", "ht")],
    }
    return templates.TemplateResponse(
        "professor.html",
        _ctx(
            request, user,
            turmas=data.TURMAS,
            tarefas=_tarefas(db, user.escola_id),
            comunicados=_comunicados_prof(db, user.escola_id),
            preview=preview,
            enviado=0,
        ),
    )


@app.post("/professor/enviar")
def professor_enviar(
    request: Request,
    titulo: str = Form(...),
    corpo: str = Form(...),
    turma: str = Form("Toda a escola"),
    precisa_confirmar: bool = Form(False),
    db: Session = Depends(get_db),
    user=Depends(exigir("professor")),
):
    """Envia (persiste) um comunicado de verdade — aparece no feed da família."""
    prio = ai.prioridade(titulo, corpo)
    turma_obj = next((t for t in data.TURMAS if t["nome"] == turma), None)
    db.add(models.Comunicado(
        escola_id=user.escola_id,
        titulo=titulo,
        autor=user.nome,
        turma=turma,
        categoria="urgente" if prio["nivel"] == "alta" else "pedagogico",
        corpo=corpo,
        precisa_confirmar=precisa_confirmar,
        enviado_em=datetime.utcnow(),
        total_familias=turma_obj["alunos"] if turma_obj else data.ESCOLA["familias"],
        leram=0,
        confirmaram=0,
    ))
    db.commit()
    return RedirectResponse("/professor?enviado=1", status_code=303)


# --------------------------------------------------------------------------- #
# Família
# --------------------------------------------------------------------------- #
@app.get("/familia", response_class=HTMLResponse)
def familia(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    comunicados = list(db.scalars(select(models.Comunicado).where(models.Comunicado.escola_id == user.escola_id)))
    ordem = {"alta": 0, "media": 1, "baixa": 2}
    comunicados.sort(key=lambda c: (ordem[ai.prioridade(c.titulo, c.corpo)["nivel"]], -c.id))
    return templates.TemplateResponse(
        "familia.html",
        _ctx(
            request, user,
            responsavel=_responsavel(user),
            comunicados=comunicados,
            tarefas=_tarefas(db, user.escola_id),
            eventos=list(db.scalars(select(models.Evento).where(models.Evento.escola_id == user.escola_id).order_by(models.Evento.data))),
            autorizacoes=list(db.scalars(select(models.Autorizacao).where(models.Autorizacao.usuario_id == user.id))),
        ),
    )


@app.get("/familia/mensagens", response_class=HTMLResponse)
def familia_mensagens(request: Request, user=Depends(exigir("familia"))):
    return templates.TemplateResponse("mensagens.html", _ctx(request, user, responsavel=_responsavel(user)))


@app.get("/familia/agenda", response_class=HTMLResponse)
def familia_agenda(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    eventos = list(db.scalars(select(models.Evento).where(models.Evento.escola_id == user.escola_id).order_by(models.Evento.data)))
    return templates.TemplateResponse("agenda.html", _ctx(request, user, responsavel=_responsavel(user), eventos=eventos))


@app.get("/familia/assistente", response_class=HTMLResponse)
def familia_assistente(request: Request, user=Depends(exigir("familia"))):
    return templates.TemplateResponse(
        "assistente.html", _ctx(request, user, responsavel=_responsavel(user), saudacao=assistant.responder("")),
    )


class Pergunta(BaseModel):
    mensagem: str = ""


@app.post("/api/assistente")
def api_assistente(p: Pergunta, user=Depends(exigir("familia"))):
    """Endpoint JSON consumido pelo chat. No MVP, chama a Claude API (tool use)."""
    return JSONResponse(assistant.responder(p.mensagem))


@app.get("/familia/comunicado/{cid}", response_class=HTMLResponse)
def familia_comunicado(request: Request, cid: int, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    c = db.get(models.Comunicado, cid)
    if not c or c.escola_id != user.escola_id:
        return RedirectResponse("/familia", status_code=303)

    # Persiste a leitura de verdade (estado por usuário).
    leit = db.scalar(
        select(models.Leitura).where(
            models.Leitura.comunicado_id == cid, models.Leitura.usuario_id == user.id
        )
    )
    if leit is None:
        leit = models.Leitura(comunicado_id=cid, usuario_id=user.id)
        db.add(leit)
    if not leit.lido:
        leit.lido = True
        leit.lido_em = datetime.utcnow()
        c.leram += 1  # atualiza contador agregado
    db.commit()

    prio = ai.prioridade(c.titulo, c.corpo)
    return templates.TemplateResponse(
        "comunicado.html",
        _ctx(
            request, user,
            c=c,
            prioridade=prio,
            resumo=ai.resumir(c.corpo),
            acao=ai.acao_sugerida(c.categoria, c.precisa_confirmar),
            sugestoes=ai.sugestoes_resposta(c.categoria, c.precisa_confirmar),
            traducao=ai.traduzir_rotulo(user.idioma),
        ),
    )


@app.get("/health")
def health():
    return {"status": "ok", "produto": "Cora"}
