from app import analytics
from app.db import SessionLocal
from sqlalchemy import select
from app import models


def _escola_id():
    with SessionLocal() as db:
        return db.scalar(select(models.Escola.id))


def test_engajamento_por_turma_ao_vivo():
    with SessionLocal() as db:
        eng = analytics.engajamento_por_turma(db, _escola_id())
    assert eng, "deve haver engajamento calculado"
    turmas = {e["turma"] for e in eng}
    assert "5º Ano A" in turmas and "5º Ano B" in turmas
    for e in eng:
        assert 0 <= e["taxa_leitura"] <= 100          # taxa real, limitada
        assert e["risco"] >= 0


def test_familias_em_risco_detecta_churn():
    with SessionLocal() as db:
        risco = analytics.familias_em_risco(db, _escola_id())
    # famílias 'sumido' (Lima, Castro) e Pedro (nunca leu) devem aparecer
    nomes = " ".join(r["nome"] for r in risco)
    motivos = " ".join(r["motivo"] for r in risco)
    assert "Lima" in nomes or "Castro" in nomes
    assert ("dias" in motivos) or ("Nunca" in motivos)


def test_coordenacao_dashboard_renderiza(coord):
    h = coord.get("/coordenacao").text
    assert "Engajamento por turma" in h and "famílias em risco" in h.lower()
