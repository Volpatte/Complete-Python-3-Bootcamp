"""Portal Financeiro — cobranças, pagamento via Pix e painel da escola."""

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


def test_familia_ve_cobrancas(familia):
    r = familia.get("/familia/financeiro")
    assert r.status_code == 200 and "Total em aberto" in r.text


def test_familia_paga_via_pix(familia):
    fam_id = _uid("familia@cora.app")
    with SessionLocal() as db:
        cid = db.scalar(select(models.Cobranca).where(
            models.Cobranca.usuario_id == fam_id, models.Cobranca.status != "pago")).id
    familia.post(f"/familia/financeiro/{cid}/pagar")
    with SessionLocal() as db:
        c = db.get(models.Cobranca, cid)
        assert c.status == "pago" and c.metodo == "Pix" and c.pago_em is not None


def test_financeiro_role_cai_no_painel():
    c = TestClient(app)
    r = c.get("/login/demo/financeiro", follow_redirects=False)
    assert r.headers["location"] == "/financeiro"
    assert c.get("/financeiro").status_code == 200


def test_lancar_cobranca_por_familia():
    c = _financeiro()
    fid = _uid("souza@cora.app")
    c.post("/financeiro/cobranca", data={
        "descricao": "Taxa de teste", "valor": "R$ 1.480,00",
        "vencimento": "2026-07-10", "alvo": f"familia:{fid}"})
    with SessionLocal() as db:
        cob = db.scalar(select(models.Cobranca).where(models.Cobranca.descricao == "Taxa de teste"))
        assert cob is not None and cob.valor_centavos == 148000 and cob.usuario_id == fid


def test_lancar_cobranca_por_turma():
    c = _financeiro()
    c.post("/financeiro/cobranca", data={
        "descricao": "Excursao 5A", "valor": "50", "alvo": "turma:5º Ano A"})
    with SessionLocal() as db:
        n = len(list(db.scalars(select(models.Cobranca).where(models.Cobranca.descricao == "Excursao 5A"))))
    assert n >= 2  # várias famílias com filho na turma


def test_valor_invalido_nao_lanca():
    c = _financeiro()
    r = c.post("/financeiro/cobranca", data={"descricao": "Zero", "valor": "abc", "alvo": "familia:1"},
               follow_redirects=False)
    assert "msg=erro" in r.headers["location"]
    with SessionLocal() as db:
        assert db.scalar(select(models.Cobranca).where(models.Cobranca.descricao == "Zero")) is None


def test_parse_valor_centavos():
    from app.main import _centavos
    assert _centavos("R$ 1.480,00") == 148000
    assert _centavos("1480.00") == 148000
    assert _centavos("1.480") == 148000   # milhar BR sem decimais
    assert _centavos("2.500") == 250000
    assert _centavos("50") == 5000
    assert _centavos("10,5") == 1050
    assert _centavos("abc") == 0


def test_professor_nao_ve_financeiro(professor):
    r = professor.get("/financeiro", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/professor")


def test_familia_nao_lanca_cobranca(familia):
    r = familia.post("/financeiro/cobranca", data={"descricao": "x", "valor": "10", "alvo": "familia:1"},
                     follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/familia")
