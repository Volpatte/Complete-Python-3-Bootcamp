"""Central de notificações unificada (agregada por usuário)."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.main import app


def _uid(email: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(models.Usuario).where(models.Usuario.email == email)).id


def test_familia_central_lista(familia):
    r = familia.get("/familia/notificacoes")
    assert r.status_code == 200
    assert "Fatura em aberto" in r.text and "Autorização pendente" in r.text


def test_pagar_remove_da_central(familia):
    fin = TestClient(app)
    fin.get("/login/demo/financeiro")
    fam_id = _uid("familia@cora.app")
    fin.post("/financeiro/cobranca", data={"descricao": "Cobranca Notif Teste", "valor": "99", "alvo": f"familia:{fam_id}"})
    assert "Cobranca Notif Teste" in familia.get("/familia/notificacoes").text
    with SessionLocal() as db:
        cid = db.scalar(select(models.Cobranca).where(models.Cobranca.descricao == "Cobranca Notif Teste")).id
    familia.post(f"/familia/financeiro/{cid}/pagar")
    assert "Cobranca Notif Teste" not in familia.get("/familia/notificacoes").text


def test_staff_central_mostra_mensagem():
    prof = TestClient(app)
    prof.get("/login/demo/professor")
    coord = TestClient(app)
    coord.get("/login/demo/coordenacao")
    prof.post(f"/equipe/{_uid('coord@cora.app')}/enviar", data={"corpo": "notif teste msg"})
    r = coord.get("/notificacoes")
    assert r.status_code == 200 and "Nova mensagem" in r.text and "Prof. Marina" in r.text


def test_bell_no_contexto(coord):
    assert "🔔" in coord.get("/coordenacao").text


def test_familia_nao_acessa_notif_staff(familia):
    r = familia.get("/notificacoes", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/familia")


def test_staff_nao_acessa_notif_familia(coord):
    r = coord.get("/familia/notificacoes", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/coordenacao")
