from sqlalchemy import select

from app import models
from app.db import SessionLocal


def _conversa_prof_id():
    with SessionLocal() as db:
        return db.scalar(select(models.Conversa.id).where(models.Conversa.canal == "Prof. Marina"))


def test_familia_ve_conversas(familia):
    h = familia.get("/familia/mensagens").text
    assert "Prof. Marina" in h and "Coordenação" in h


def test_mensageria_bidirecional(familia, professor):
    cid = _conversa_prof_id()
    # família envia
    familia.post(f"/familia/mensagens/{cid}/enviar",
                 data={"corpo": "Vou buscar às 11h30"}, follow_redirects=False)
    # professor lê e responde
    assert "Vou buscar às 11h30" in professor.get(f"/mensagens/{cid}").text
    professor.post(f"/mensagens/{cid}/enviar",
                   data={"corpo": "Perfeito, combinado!"}, follow_redirects=False)
    # família vê a resposta
    assert "Perfeito, combinado!" in familia.get(f"/familia/mensagens/{cid}").text


def test_coordenacao_nao_abre_conversa_de_professor(coord):
    cid = _conversa_prof_id()
    r = coord.get(f"/mensagens/{cid}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/mensagens"


def test_familia_nao_acessa_conversa_alheia(client):
    cid = _conversa_prof_id()
    r = client.get(f"/familia/mensagens/{cid}", follow_redirects=False)
    assert r.headers["location"] == "/login"
