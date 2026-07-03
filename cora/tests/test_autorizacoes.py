"""Autorizações reais — resposta da família + painel de solicitações do staff."""

from sqlalchemy import select

from app import models
from app.db import SessionLocal


def _uid(email: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(models.Usuario).where(models.Usuario.email == email)).id


def _autoriz(titulo: str, usuario_id: int):
    with SessionLocal() as db:
        return db.scalar(select(models.Autorizacao).where(
            models.Autorizacao.titulo == titulo, models.Autorizacao.usuario_id == usuario_id))


def test_familia_autoriza(coord, familia):
    coord.post("/autorizacoes", data={"titulo": "Teste Autoriza", "alvo": "escola", "data_evento": "2026-07-20"})
    a = _autoriz("Teste Autoriza", _uid("familia@cora.app"))
    familia.post(f"/familia/autorizacao/{a.id}/responder", data={"resposta": "autorizado"})
    with SessionLocal() as db:
        got = db.get(models.Autorizacao, a.id)
        assert got.status == "autorizado" and got.respondido_em is not None


def test_familia_recusa(coord, familia):
    coord.post("/autorizacoes", data={"titulo": "Teste Recusa", "alvo": "escola"})
    a = _autoriz("Teste Recusa", _uid("familia@cora.app"))
    familia.post(f"/familia/autorizacao/{a.id}/responder", data={"resposta": "recusado"})
    with SessionLocal() as db:
        assert db.get(models.Autorizacao, a.id).status == "recusado"


def test_resposta_invalida_nao_muda(coord, familia):
    coord.post("/autorizacoes", data={"titulo": "Teste Invalida", "alvo": "escola"})
    a = _autoriz("Teste Invalida", _uid("familia@cora.app"))
    familia.post(f"/familia/autorizacao/{a.id}/responder", data={"resposta": "talvez"})
    with SessionLocal() as db:
        assert db.get(models.Autorizacao, a.id).status == "pendente"


def test_familia_nao_responde_de_outra(coord, familia):
    """IDOR: uma família não pode responder a autorização de outra."""
    coord.post("/autorizacoes", data={"titulo": "Teste IDOR", "alvo": "escola"})
    a = _autoriz("Teste IDOR", _uid("souza@cora.app"))
    familia.post(f"/familia/autorizacao/{a.id}/responder", data={"resposta": "autorizado"})
    with SessionLocal() as db:
        assert db.get(models.Autorizacao, a.id).status == "pendente"  # inalterado


def test_staff_ve_painel(coord):
    r = coord.get("/autorizacoes")
    assert r.status_code == 200 and "Passeio ao Jardim" in r.text


def test_staff_solicita_por_turma(coord):
    coord.post("/autorizacoes", data={"titulo": "Excursao Turma 5A", "alvo": "turma:5º Ano A"})
    with SessionLocal() as db:
        n = len(list(db.scalars(select(models.Autorizacao).where(
            models.Autorizacao.titulo == "Excursao Turma 5A"))))
    assert n >= 2  # várias famílias na turma


def test_staff_solicita_escola(coord):
    coord.post("/autorizacoes", data={"titulo": "Aviso Toda Escola", "alvo": "escola"})
    with SessionLocal() as db:
        n = len(list(db.scalars(select(models.Autorizacao).where(
            models.Autorizacao.titulo == "Aviso Toda Escola"))))
    assert n >= 9  # todas as famílias


def test_professor_acessa(professor):
    assert professor.get("/autorizacoes").status_code == 200


def test_familia_nao_acessa_painel(familia):
    r = familia.get("/autorizacoes", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/familia")
