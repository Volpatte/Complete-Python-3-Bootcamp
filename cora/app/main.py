"""Cora — protótipo navegável (FastAPI + Jinja2).

Rodar:
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    # abra http://127.0.0.1:8000

Três perfis navegáveis: Coordenação, Professor e Família.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import ai, data

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Cora", description="Plataforma de relação escola-família")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Filtros úteis nos templates
templates.env.filters["dia"] = lambda d: d.strftime("%d/%m")
templates.env.filters["data_hora"] = lambda d: d.strftime("%d/%m %H:%M")


def _ctx(request: Request, **extra) -> dict:
    base = {"request": request, "escola": data.ESCOLA, "ai": ai}
    base.update(extra)
    return base


# --------------------------------------------------------------------------- #
# Home / seletor de perfil
# --------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", _ctx(request))


# --------------------------------------------------------------------------- #
# Perfil: Coordenação / Direção (analytics + IA + integrações)
# --------------------------------------------------------------------------- #
@app.get("/coordenacao", response_class=HTMLResponse)
def coordenacao(request: Request):
    insight = ai.insight_coordenacao(data.ENGAJAMENTO_POR_TURMA)
    media_leitura = round(
        sum(t["taxa_leitura"] for t in data.ENGAJAMENTO_POR_TURMA)
        / len(data.ENGAJAMENTO_POR_TURMA)
    )
    return templates.TemplateResponse(
        "coordenacao.html",
        _ctx(
            request,
            engajamento=data.ENGAJAMENTO_POR_TURMA,
            familias_risco=data.FAMILIAS_RISCO,
            integracoes=data.INTEGRACOES,
            comunicados=data.COMUNICADOS,
            insight=insight,
            media_leitura=media_leitura,
        ),
    )


# --------------------------------------------------------------------------- #
# Perfil: Professor (compor comunicado com assistência da IA)
# --------------------------------------------------------------------------- #
@app.get("/professor", response_class=HTMLResponse)
def professor(request: Request):
    return templates.TemplateResponse(
        "professor.html",
        _ctx(
            request,
            turmas=data.TURMAS,
            tarefas=data.TAREFAS,
            comunicados=[c for c in data.COMUNICADOS if c["autor"].startswith("Prof")],
            preview=None,
        ),
    )


@app.post("/professor/preview", response_class=HTMLResponse)
def professor_preview(
    request: Request,
    titulo: str = Form(""),
    corpo: str = Form(""),
    turma: str = Form("Toda a escola"),
):
    """A IA pré-processa o comunicado antes de enviar: resumo, prioridade,
    sugestão de ação e prévia de tradução."""
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
            request,
            turmas=data.TURMAS,
            tarefas=data.TAREFAS,
            comunicados=[c for c in data.COMUNICADOS if c["autor"].startswith("Prof")],
            preview=preview,
        ),
    )


# --------------------------------------------------------------------------- #
# Perfil: Família (feed com IA, agenda, tarefas, autorizações)
# --------------------------------------------------------------------------- #
@app.get("/familia", response_class=HTMLResponse)
def familia(request: Request):
    # ordena por prioridade da IA (urgente primeiro)
    ordem = {"alta": 0, "media": 1, "baixa": 2}
    comunicados = sorted(
        data.COMUNICADOS,
        key=lambda c: ordem[ai.prioridade(c["titulo"], c["corpo"])["nivel"]],
    )
    return templates.TemplateResponse(
        "familia.html",
        _ctx(
            request,
            responsavel=data.RESPONSAVEL,
            comunicados=comunicados,
            tarefas=data.TAREFAS,
            eventos=data.EVENTOS,
            autorizacoes=data.AUTORIZACOES,
        ),
    )


@app.get("/familia/mensagens", response_class=HTMLResponse)
def familia_mensagens(request: Request):
    return templates.TemplateResponse(
        "mensagens.html", _ctx(request, responsavel=data.RESPONSAVEL)
    )


@app.get("/familia/agenda", response_class=HTMLResponse)
def familia_agenda(request: Request):
    return templates.TemplateResponse(
        "agenda.html",
        _ctx(request, responsavel=data.RESPONSAVEL, eventos=data.EVENTOS),
    )


@app.get("/familia/comunicado/{cid}", response_class=HTMLResponse)
def familia_comunicado(request: Request, cid: int):
    c = data.comunicado_por_id(cid)
    if not c:
        return RedirectResponse("/familia")
    prio = ai.prioridade(c["titulo"], c["corpo"])
    return templates.TemplateResponse(
        "comunicado.html",
        _ctx(
            request,
            c=c,
            prioridade=prio,
            resumo=ai.resumir(c["corpo"]),
            acao=ai.acao_sugerida(c["categoria"], c["precisa_confirmar"]),
            sugestoes=ai.sugestoes_resposta(c["categoria"], c["precisa_confirmar"]),
            traducao=ai.traduzir_rotulo(data.RESPONSAVEL["idioma"]),
        ),
    )


@app.get("/health")
def health():
    return {"status": "ok", "produto": "Cora"}
