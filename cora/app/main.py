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
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import ai, analytics, assistant, data, i18n, models, whatsapp
from .db import get_db
from .seed import init_db
from .security import autenticar, hash_senha, senha_temporaria

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
    return {
        "coordenacao": "/coordenacao", "professor": "/professor", "familia": "/familia",
        "direcao": "/admin", "secretaria": "/admin", "financeiro": "/admin",
    }.get(papel, "/")


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
    lang = i18n.resolve(request)
    base = {
        "request": request, "escola": data.ESCOLA, "ai": ai, "user": user,
        "lang": lang, "t": i18n.translator(lang), "langs": i18n.LANGS,
        "is_admin": bool(user and user.papel in models.PAPEIS_ADMIN),
    }
    base.update(extra)
    return base


def _responsavel(user: models.Usuario) -> dict:
    return {
        "nome": user.nome, "filho": user.filho_nome, "turma": user.turma,
        "idioma": user.idioma, "whatsapp": user.whatsapp_optin,
    }


# --------------------------------------------------------------------------- #
# Login / logout
# --------------------------------------------------------------------------- #
@app.get("/lang/{code}")
def set_lang(code: str, request: Request):
    """Troca o idioma da interface (pt/en/es) e volta para a página anterior."""
    destino = request.headers.get("referer") or "/"
    resp = RedirectResponse(destino, status_code=303)
    resp.set_cookie(
        i18n.COOKIE, i18n.normalize(code),
        max_age=60 * 60 * 24 * 365, samesite="lax",
    )
    return resp


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, erro: str = ""):
    return templates.TemplateResponse("login.html", _ctx(request, erro=erro))


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
    emails = {
        "coordenacao": "coord@cora.app", "professor": "prof@cora.app", "familia": "familia@cora.app",
        "direcao": "dir@cora.app", "secretaria": "sec@cora.app", "financeiro": "fin@cora.app",
    }
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
# Gestão da escola — administração de funcionários e famílias
# --------------------------------------------------------------------------- #
def _usuarios_da_escola(db: Session, escola_id: int):
    return list(
        db.scalars(
            select(models.Usuario)
            .where(models.Usuario.escola_id == escola_id)
            .order_by(models.Usuario.papel, models.Usuario.nome)
        )
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_home(
    request: Request, nova_senha: str = "", nome_reset: str = "", msg: str = "", erro: str = "",
    db: Session = Depends(get_db), user=Depends(exigir(*models.PAPEIS_ADMIN)),
):
    usuarios = _usuarios_da_escola(db, user.escola_id)
    return templates.TemplateResponse(
        "admin.html",
        _ctx(
            request, user, active="admin",
            equipe=[u for u in usuarios if u.papel in models.PAPEIS_STAFF],
            familias=[u for u in usuarios if u.papel == models.FAMILIA],
            papeis=models.PAPEIS_CRIAVEIS, turmas=data.TURMAS,
            nova_senha=nova_senha, nome_reset=nome_reset, msg=msg, erro=erro,
        ),
    )


@app.post("/admin/usuario")
def admin_criar(
    request: Request,
    nome: str = Form(...), email: str = Form(...), papel: str = Form(...),
    senha: str = Form(""), filho_nome: str = Form(""), turma: str = Form(""),
    db: Session = Depends(get_db), user=Depends(exigir(*models.PAPEIS_ADMIN)),
):
    nome, email, papel = nome.strip(), email.strip().lower(), papel.strip()
    if papel not in models.PAPEIS_CRIAVEIS or not nome or not email:
        return RedirectResponse("/admin?erro=dados", status_code=303)
    if db.scalar(select(models.Usuario).where(models.Usuario.email == email)):
        return RedirectResponse("/admin?erro=email", status_code=303)
    gerada = not senha.strip()
    senha_final = senha.strip() or senha_temporaria()
    novo = models.Usuario(
        nome=nome, email=email, senha_hash=hash_senha(senha_final),
        papel=papel, escola_id=user.escola_id, ativo=True,
    )
    if papel == models.FAMILIA:
        novo.filho_nome = filho_nome.strip()
        novo.turma = turma.strip()
    db.add(novo)
    db.commit()
    if gerada:  # mostra a senha inicial uma vez
        return RedirectResponse(
            f"/admin?msg=criado&nova_senha={quote(senha_final)}&nome_reset={quote(nome)}",
            status_code=303,
        )
    return RedirectResponse("/admin?msg=criado", status_code=303)


@app.post("/admin/usuario/{uid}/senha")
def admin_reset_senha(
    request: Request, uid: int,
    db: Session = Depends(get_db), user=Depends(exigir(*models.PAPEIS_ADMIN)),
):
    alvo = db.get(models.Usuario, uid)
    if not alvo or alvo.escola_id != user.escola_id:
        return RedirectResponse("/admin", status_code=303)
    nova = senha_temporaria()
    alvo.senha_hash = hash_senha(nova)
    db.commit()
    return RedirectResponse(
        f"/admin?msg=senha&nova_senha={quote(nova)}&nome_reset={quote(alvo.nome)}",
        status_code=303,
    )


@app.post("/admin/usuario/{uid}/status")
def admin_toggle_status(
    request: Request, uid: int,
    db: Session = Depends(get_db), user=Depends(exigir(*models.PAPEIS_ADMIN)),
):
    alvo = db.get(models.Usuario, uid)
    if not alvo or alvo.escola_id != user.escola_id:
        return RedirectResponse("/admin", status_code=303)
    if alvo.id == user.id:
        return RedirectResponse("/admin?erro=self", status_code=303)
    # não desativar o último administrador ativo da escola
    if alvo.ativo and alvo.papel in models.PAPEIS_ADMIN:
        admins_ativos = db.scalar(
            select(func.count()).select_from(models.Usuario).where(
                models.Usuario.escola_id == user.escola_id,
                models.Usuario.papel.in_(models.PAPEIS_ADMIN),
                models.Usuario.ativo.is_(True),
            )
        )
        if admins_ativos <= 1:
            return RedirectResponse("/admin?erro=ultimo_admin", status_code=303)
    alvo.ativo = not alvo.ativo
    db.commit()
    return RedirectResponse("/admin?msg=status", status_code=303)


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
    lang = i18n.resolve(request)
    engajamento = analytics.engajamento_por_turma(db, user.escola_id, lang=lang)
    familias_risco = analytics.familias_em_risco(db, user.escola_id, lang=lang)
    media_leitura = (
        round(sum(t["taxa_leitura"] for t in engajamento) / len(engajamento))
        if engajamento else 0
    )
    insight = (
        ai.insight_coordenacao(engajamento, lang) if engajamento
        else i18n.tr("Ainda sem dados de leitura suficientes.", lang)
    )
    return templates.TemplateResponse(
        "coordenacao.html",
        _ctx(
            request, user,
            engajamento=engajamento,
            familias_risco=familias_risco,
            integracoes=data.INTEGRACOES,
            comunicados=comunicados,
            insight=insight,
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
def professor(request: Request, db: Session = Depends(get_db), user=Depends(exigir("professor")),
              enviado: int = 0, ok: str = ""):
    return templates.TemplateResponse(
        "professor.html",
        _ctx(
            request, user,
            turmas=data.TURMAS,
            tarefas=_tarefas(db, user.escola_id),
            eventos=list(db.scalars(select(models.Evento).where(models.Evento.escola_id == user.escola_id).order_by(models.Evento.data))),
            comunicados=_comunicados_prof(db, user.escola_id),
            preview=None,
            enviado=enviado,
            ok=ok,
        ),
    )


@app.post("/professor/tarefa")
def professor_tarefa(
    request: Request, disciplina: str = Form(...), titulo: str = Form(...),
    entrega: str = Form(""), turma: str = Form("Toda a escola"),
    db: Session = Depends(get_db), user=Depends(exigir("professor")),
):
    try:
        venc = date.fromisoformat(entrega) if entrega else date.today()
    except ValueError:
        venc = date.today()
    if titulo.strip():
        db.add(models.Tarefa(
            escola_id=user.escola_id, turma=turma, disciplina=disciplina.strip(),
            titulo=titulo.strip(), entrega=venc, status="pendente",
        ))
        db.commit()
    return RedirectResponse("/professor?ok=tarefa", status_code=303)


@app.post("/professor/evento")
def professor_evento(
    request: Request, titulo: str = Form(...), data_evento: str = Form(""), tipo: str = Form("evento"),
    db: Session = Depends(get_db), user=Depends(exigir("professor")),
):
    try:
        quando = date.fromisoformat(data_evento) if data_evento else date.today()
    except ValueError:
        quando = date.today()
    if titulo.strip():
        db.add(models.Evento(escola_id=user.escola_id, data=quando, titulo=titulo.strip(), tipo=tipo.strip() or "evento"))
        db.commit()
    return RedirectResponse("/professor?ok=evento", status_code=303)


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
    comunicado = models.Comunicado(
        escola_id=user.escola_id,
        titulo=titulo,
        autor=user.nome,
        turma=turma,
        categoria="urgente" if prio["nivel"] == "alta" else "pedagogico",
        corpo=corpo,
        resumo=ai.resumir(corpo),   # computa o resumo uma vez, no envio
        precisa_confirmar=precisa_confirmar,
        enviado_em=datetime.utcnow(),
        total_familias=turma_obj["alunos"] if turma_obj else data.ESCOLA["familias"],
        leram=0,
        confirmaram=0,
    )
    db.add(comunicado)
    db.flush()

    # Espelha o comunicado no WhatsApp das famílias inscritas (omnichannel).
    familias = db.scalars(
        select(models.Usuario).where(
            models.Usuario.escola_id == user.escola_id,
            models.Usuario.papel == models.FAMILIA,
            models.Usuario.whatsapp_optin == True,  # noqa: E712
        )
    )
    for fam in familias:
        if turma == "Toda a escola" or fam.turma == turma:
            whatsapp.enviar(db, fam, titulo, f"comunicado:{comunicado.id}")

    db.commit()
    return RedirectResponse("/professor?enviado=1", status_code=303)


# --------------------------------------------------------------------------- #
# Família
# --------------------------------------------------------------------------- #
@app.get("/familia", response_class=HTMLResponse)
def familia(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    comunicados = list(db.scalars(
        select(models.Comunicado).where(
            models.Comunicado.escola_id == user.escola_id,
            or_(models.Comunicado.turma == "Toda a escola", models.Comunicado.turma == user.turma),
        )
    ))
    ordem = {"alta": 0, "media": 1, "baixa": 2}
    comunicados.sort(key=lambda c: (ordem[ai.prioridade(c.titulo, c.corpo)["nivel"]], -c.id))
    tarefas = list(db.scalars(
        select(models.Tarefa).where(
            models.Tarefa.escola_id == user.escola_id,
            or_(models.Tarefa.turma == "Toda a escola", models.Tarefa.turma == user.turma),
        )
    ))
    return templates.TemplateResponse(
        "familia.html",
        _ctx(
            request, user,
            responsavel=_responsavel(user),
            comunicados=comunicados,
            tarefas=tarefas,
            eventos=list(db.scalars(select(models.Evento).where(models.Evento.escola_id == user.escola_id).order_by(models.Evento.data))),
            autorizacoes=list(db.scalars(select(models.Autorizacao).where(models.Autorizacao.usuario_id == user.id))),
        ),
    )


@app.get("/familia/mensagens", response_class=HTMLResponse)
def familia_mensagens(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    conversas = list(
        db.scalars(
            select(models.Conversa)
            .where(models.Conversa.familia_id == user.id)
            .order_by(models.Conversa.atualizado_em.desc())
        )
    )
    return templates.TemplateResponse(
        "mensagens.html", _ctx(request, user, responsavel=_responsavel(user), conversas=conversas)
    )


def _conversa_da_familia(db: Session, cid: int, user) -> models.Conversa | None:
    c = db.get(models.Conversa, cid)
    return c if c and c.familia_id == user.id else None


@app.get("/familia/mensagens/{cid}", response_class=HTMLResponse)
def familia_conversa(request: Request, cid: int, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    conversa = _conversa_da_familia(db, cid, user)
    if not conversa:
        return RedirectResponse("/familia/mensagens", status_code=303)
    return templates.TemplateResponse(
        "conversa.html", _ctx(request, user, responsavel=_responsavel(user), conversa=conversa)
    )


@app.post("/familia/mensagens/{cid}/enviar")
def familia_conversa_enviar(
    request: Request, cid: int, corpo: str = Form(...),
    db: Session = Depends(get_db), user=Depends(exigir("familia")),
):
    conversa = _conversa_da_familia(db, cid, user)
    if conversa and corpo.strip():
        agora = datetime.utcnow()
        db.add(models.Mensagem(
            conversa_id=conversa.id, autor_id=user.id, autor_nome=user.nome,
            autor_papel=models.FAMILIA, corpo=corpo.strip(), enviado_em=agora,
        ))
        conversa.atualizado_em = agora
        db.commit()
    return RedirectResponse(f"/familia/mensagens/{cid}", status_code=303)


# --------------------------------------------------------------------------- #
# Mensageria do lado da escola (professor / coordenação)
# --------------------------------------------------------------------------- #
@app.get("/mensagens", response_class=HTMLResponse)
def staff_mensagens(request: Request, db: Session = Depends(get_db), user=Depends(exigir("professor", "coordenacao"))):
    conversas = list(
        db.scalars(
            select(models.Conversa)
            .where(models.Conversa.escola_id == user.escola_id, models.Conversa.staff_papel == user.papel)
            .order_by(models.Conversa.atualizado_em.desc())
        )
    )
    return templates.TemplateResponse(
        "staff_mensagens.html", _ctx(request, user, conversas=conversas, active="msg")
    )


def _conversa_do_staff(db: Session, cid: int, user) -> models.Conversa | None:
    c = db.get(models.Conversa, cid)
    if c and c.escola_id == user.escola_id and c.staff_papel == user.papel:
        return c
    return None


@app.get("/mensagens/{cid}", response_class=HTMLResponse)
def staff_conversa(request: Request, cid: int, db: Session = Depends(get_db), user=Depends(exigir("professor", "coordenacao"))):
    conversa = _conversa_do_staff(db, cid, user)
    if not conversa:
        return RedirectResponse("/mensagens", status_code=303)
    return templates.TemplateResponse(
        "staff_conversa.html", _ctx(request, user, conversa=conversa, active="msg")
    )


@app.post("/mensagens/{cid}/enviar")
def staff_conversa_enviar(
    request: Request, cid: int, corpo: str = Form(...),
    db: Session = Depends(get_db), user=Depends(exigir("professor", "coordenacao")),
):
    conversa = _conversa_do_staff(db, cid, user)
    if conversa and corpo.strip():
        agora = datetime.utcnow()
        db.add(models.Mensagem(
            conversa_id=conversa.id, autor_id=user.id, autor_nome=user.nome,
            autor_papel=user.papel, corpo=corpo.strip(), enviado_em=agora,
        ))
        conversa.atualizado_em = agora
        # Espelha a resposta no WhatsApp da família (se inscrita).
        familia = db.get(models.Usuario, conversa.familia_id)
        if familia:
            whatsapp.enviar(db, familia, f"{user.nome}: {corpo.strip()}", f"mensagem:{conversa.id}")
        db.commit()
    return RedirectResponse(f"/mensagens/{cid}", status_code=303)


# --------------------------------------------------------------------------- #
# WhatsApp — opt-in da família + Central da coordenação
# --------------------------------------------------------------------------- #
@app.post("/familia/whatsapp/ativar")
def familia_whatsapp_ativar(
    request: Request, telefone: str = Form(""),
    db: Session = Depends(get_db), user=Depends(exigir("familia")),
):
    user.whatsapp_optin = True
    if telefone.strip():
        user.telefone = telefone.strip()
    db.commit()
    return RedirectResponse("/familia", status_code=303)


@app.get("/whatsapp", response_class=HTMLResponse)
def whatsapp_central(request: Request, db: Session = Depends(get_db), user=Depends(exigir("coordenacao"))):
    entregas = list(
        db.scalars(
            select(models.EntregaWhatsApp)
            .where(models.EntregaWhatsApp.escola_id == user.escola_id)
            .order_by(models.EntregaWhatsApp.atualizado_em.desc())
        )
    )
    total = len(entregas)
    contagem = {s: sum(1 for e in entregas if e.status == s) for s in ("enviado", "entregue", "lido", "falhou")}
    entregues = contagem["entregue"] + contagem["lido"]
    taxa_entrega = round(entregues / total * 100) if total else 0
    taxa_leitura = round(contagem["lido"] / total * 100) if total else 0
    return templates.TemplateResponse(
        "whatsapp.html",
        _ctx(
            request, user, active="wa", entregas=entregas, contagem=contagem,
            total=total, taxa_entrega=taxa_entrega, taxa_leitura=taxa_leitura,
            modo=whatsapp.modo(),
        ),
    )


@app.post("/whatsapp/simular-leitura")
def whatsapp_simular(request: Request, db: Session = Depends(get_db), user=Depends(exigir("coordenacao"))):
    entregas = list(
        db.scalars(select(models.EntregaWhatsApp).where(models.EntregaWhatsApp.escola_id == user.escola_id))
    )
    whatsapp.avancar_simulado(entregas)
    db.commit()
    return RedirectResponse("/whatsapp", status_code=303)


# --------------------------------------------------------------------------- #
# Saúde — enfermaria / coordenação registra administração de medicação
# --------------------------------------------------------------------------- #
@app.get("/saude", response_class=HTMLResponse)
def saude_central(request: Request, db: Session = Depends(get_db), user=Depends(exigir("coordenacao"))):
    medicacoes = list(
        db.scalars(select(models.Medicacao).where(
            models.Medicacao.escola_id == user.escola_id,
            models.Medicacao.ativo == True, models.Medicacao.autorizado == True,  # noqa: E712
        ).order_by(models.Medicacao.aluno_nome))
    )
    fichas = {
        f.usuario_id: f
        for f in db.scalars(select(models.FichaSaude).where(models.FichaSaude.escola_id == user.escola_id))
    }
    return templates.TemplateResponse(
        "staff_saude.html", _ctx(request, user, active="saude", medicacoes=medicacoes, fichas=fichas)
    )


@app.post("/saude/administrar/{med_id}")
def saude_administrar(
    request: Request, med_id: int, dose: str = Form(""), observacao: str = Form(""),
    db: Session = Depends(get_db), user=Depends(exigir("coordenacao")),
):
    med = db.get(models.Medicacao, med_id)
    if med and med.escola_id == user.escola_id:
        db.add(models.AdministracaoMed(
            medicacao_id=med.id, administrado_por=user.nome, administrado_em=datetime.utcnow(),
            dose=dose.strip() or med.dosagem, observacao=observacao.strip(),
        ))
        # Avisa a família pelo WhatsApp (transparência + diferencial omnichannel).
        familia = db.get(models.Usuario, med.usuario_id)
        if familia:
            whatsapp.enviar(
                db, familia,
                f"💊 Medicação administrada: {med.nome} ({dose.strip() or med.dosagem}). Qualquer dúvida, fale conosco.",
                f"saude:{med.id}",
            )
        db.commit()
    return RedirectResponse("/saude", status_code=303)


@app.get("/familia/agenda", response_class=HTMLResponse)
def familia_agenda(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    eventos = list(db.scalars(select(models.Evento).where(models.Evento.escola_id == user.escola_id).order_by(models.Evento.data)))
    return templates.TemplateResponse("agenda.html", _ctx(request, user, responsavel=_responsavel(user), eventos=eventos))


@app.get("/familia/loja", response_class=HTMLResponse)
def familia_loja(request: Request, user=Depends(exigir("familia"))):
    return templates.TemplateResponse(
        "loja.html", _ctx(request, user, responsavel=_responsavel(user), produtos=data.LOJA)
    )


def _ficha_da_familia(db: Session, user) -> models.FichaSaude:
    ficha = db.scalar(select(models.FichaSaude).where(models.FichaSaude.usuario_id == user.id))
    if ficha is None:  # cria vazia na primeira visita
        ficha = models.FichaSaude(escola_id=user.escola_id, usuario_id=user.id, aluno_nome=user.filho_nome)
        db.add(ficha)
        db.commit()
    return ficha


@app.get("/familia/saude", response_class=HTMLResponse)
def familia_saude(request: Request, db: Session = Depends(get_db), user=Depends(exigir("familia"))):
    ficha = _ficha_da_familia(db, user)
    medicacoes = list(
        db.scalars(select(models.Medicacao).where(
            models.Medicacao.usuario_id == user.id, models.Medicacao.ativo == True  # noqa: E712
        ).order_by(models.Medicacao.criado_em.desc()))
    )
    administracoes = list(db.scalars(
        select(models.AdministracaoMed)
        .join(models.Medicacao)
        .where(models.Medicacao.usuario_id == user.id)
        .order_by(models.AdministracaoMed.administrado_em.desc())
    ))
    medicacoes_nome = {m.id: m.nome for m in medicacoes}
    return templates.TemplateResponse(
        "saude.html",
        _ctx(request, user, responsavel=_responsavel(user), ficha=ficha,
             medicacoes=medicacoes, administracoes=administracoes, medicacoes_nome=medicacoes_nome),
    )


@app.post("/familia/saude/ficha")
def familia_saude_ficha(
    request: Request,
    tipo_sanguineo: str = Form(""), alergias: str = Form(""), condicoes: str = Form(""),
    restricoes: str = Form(""), contato_emergencia: str = Form(""), convenio: str = Form(""),
    observacoes: str = Form(""),
    db: Session = Depends(get_db), user=Depends(exigir("familia")),
):
    ficha = _ficha_da_familia(db, user)
    ficha.tipo_sanguineo = tipo_sanguineo.strip()
    ficha.alergias = alergias.strip()
    ficha.condicoes = condicoes.strip()
    ficha.restricoes = restricoes.strip()
    ficha.contato_emergencia = contato_emergencia.strip()
    ficha.convenio = convenio.strip()
    ficha.observacoes = observacoes.strip()
    db.commit()
    return RedirectResponse("/familia/saude", status_code=303)


@app.post("/familia/saude/medicacao")
def familia_saude_medicacao(
    request: Request,
    nome: str = Form(...), dosagem: str = Form(""), horario: str = Form(""), instrucoes: str = Form(""),
    db: Session = Depends(get_db), user=Depends(exigir("familia")),
):
    if nome.strip():
        db.add(models.Medicacao(
            escola_id=user.escola_id, usuario_id=user.id, aluno_nome=user.filho_nome,
            nome=nome.strip(), dosagem=dosagem.strip(), horario=horario.strip(),
            instrucoes=instrucoes.strip(), autorizado=True, ativo=True, criado_em=datetime.utcnow(),
        ))
        db.commit()
    return RedirectResponse("/familia/saude", status_code=303)


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
    if not c or c.escola_id != user.escola_id or c.turma not in ("Toda a escola", user.turma):
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
    lang = i18n.resolve(request)
    corpo_loc = i18n.tr(c.corpo, lang)
    resumo = ai.resumir(corpo_loc, lang=lang)
    return templates.TemplateResponse(
        "comunicado.html",
        _ctx(
            request, user,
            c=c,
            prioridade=prio,
            resumo=resumo,
            acao=ai.acao_sugerida(c.categoria, c.precisa_confirmar),
            sugestoes=ai.sugestoes_resposta(c.categoria, c.precisa_confirmar),
            traducao=ai.traduzir_rotulo(user.idioma),
        ),
    )


@app.get("/sw.js")
def service_worker():
    """Serve o service worker da raiz para que seu escopo cubra todo o app."""
    return FileResponse(
        BASE_DIR / "static" / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/health")
def health():
    return {"status": "ok", "produto": "Cora"}
