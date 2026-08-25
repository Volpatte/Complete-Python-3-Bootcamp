"""Recibos, 2ª via de cobrança e histórico de pagamentos."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.main import app


def _uid(email: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(models.Usuario).where(models.Usuario.email == email)).id


def _financeiro() -> TestClient:
    c = TestClient(app)
    c.get("/login/demo/financeiro")
    return c


def _cobranca(usuario_email: str, status: str) -> models.Cobranca:
    """Uma cobrança da família informada com o status pedido."""
    uid = _uid(usuario_email)
    with SessionLocal() as db:
        return db.scalar(
            select(models.Cobranca).where(
                models.Cobranca.usuario_id == uid, models.Cobranca.status == status)
        )


def test_familia_ve_recibo_de_paga(familia):
    c = _cobranca("familia@cora.app", "pago")
    r = familia.get(f"/familia/financeiro/{c.id}")
    assert r.status_code == 200
    assert "Recibo de pagamento" in r.text
    assert f"{c.id:06d}" in r.text          # número do documento
    assert "Pix copia e cola" not in r.text  # paga não mostra 2ª via


def test_familia_ve_segunda_via_de_aberta(familia):
    c = _cobranca("familia@cora.app", "aberto")
    r = familia.get(f"/familia/financeiro/{c.id}")
    assert r.status_code == 200
    assert "Pix copia e cola" in r.text
    assert "CORADEMO" in r.text and r.text.count("6304DEMO") >= 1
    assert "Recibo de pagamento" not in r.text


def test_pagar_pelo_detalhe_vira_recibo(familia):
    c = _cobranca("familia@cora.app", "aberto")
    r = familia.post(f"/familia/financeiro/{c.id}/pagar", data={"origem": "detalhe"},
                     follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/familia/financeiro/{c.id}?pago=1"
    assert "Recibo de pagamento" in familia.get(f"/familia/financeiro/{c.id}").text


def test_familia_nao_ve_cobranca_de_outra(familia):
    """IDOR: a cobrança de outra família redireciona, não vaza."""
    alheia = _cobranca("souza@cora.app", "aberto")
    r = familia.get(f"/familia/financeiro/{alheia.id}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/familia/financeiro"


def test_staff_ve_detalhe_de_qualquer_cobranca():
    fin = _financeiro()
    c = _cobranca("souza@cora.app", "aberto")
    r = fin.get(f"/financeiro/cobranca/{c.id}")
    assert r.status_code == 200 and "Pix copia e cola" in r.text


def test_staff_nao_ve_botao_pagar():
    """Só a família paga: o staff vê a 2ª via sem o botão de pagamento."""
    fin = _financeiro()
    c = _cobranca("souza@cora.app", "aberto")
    assert "/pagar" not in fin.get(f"/financeiro/cobranca/{c.id}").text


def test_cobranca_inexistente_redireciona(familia):
    r = familia.get("/familia/financeiro/999999", follow_redirects=False)
    assert r.status_code == 303


def test_professor_nao_acessa_detalhe(professor):
    c = _cobranca("familia@cora.app", "pago")
    r = professor.get(f"/financeiro/cobranca/{c.id}", follow_redirects=False)
    assert r.status_code == 303 and not r.headers["location"].startswith("/financeiro")


def test_historico_no_painel():
    fin = _financeiro()
    r = fin.get("/financeiro")
    assert r.status_code == 200
    assert "Histórico de pagamentos" in r.text and "últimos 30 dias" in r.text
