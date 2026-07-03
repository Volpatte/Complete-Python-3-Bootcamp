"""Mensagens internas da equipe (staff ↔ staff)."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.main import app


def _uid(email: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(models.Usuario).where(models.Usuario.email == email)).id


def _msg(corpo: str):
    with SessionLocal() as db:
        return db.scalar(select(models.MensagemStaff).where(models.MensagemStaff.corpo == corpo))


def test_inbox_lista_colegas(coord):
    r = coord.get("/equipe")
    assert r.status_code == 200 and "Prof. Marina" in r.text


def test_enviar_mensagem(coord):
    prof_id = _uid("prof@cora.app")
    coord.post(f"/equipe/{prof_id}/enviar", data={"corpo": "Mensagem teste equipe"})
    m = _msg("Mensagem teste equipe")
    assert m is not None and m.de_nome == "Ana Coordenação" and m.para_id == prof_id


def test_abrir_conversa_marca_lido():
    prof = TestClient(app)
    prof.get("/login/demo/professor")
    coord = TestClient(app)
    coord.get("/login/demo/coordenacao")
    coord_id, prof_id = _uid("coord@cora.app"), _uid("prof@cora.app")
    prof.post(f"/equipe/{coord_id}/enviar", data={"corpo": "ping nao lido"})
    assert _msg("ping nao lido").lido is False
    coord.get(f"/equipe/{prof_id}")  # coordenação abre a conversa
    assert _msg("ping nao lido").lido is True


def test_nao_envia_para_familia(coord):
    fam_id = _uid("familia@cora.app")
    coord.post(f"/equipe/{fam_id}/enviar", data={"corpo": "nao deve criar"})
    assert _msg("nao deve criar") is None


def test_nao_conversa_consigo(coord):
    r = coord.get(f"/equipe/{_uid('coord@cora.app')}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/equipe")


def test_familia_nao_acessa_equipe(familia):
    r = familia.get("/equipe", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/familia")
