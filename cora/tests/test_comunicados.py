from sqlalchemy import func, select

from app import models
from app.db import SessionLocal


def test_feed_familia(familia):
    h = familia.get("/familia").text
    assert "Resumo Cora IA" in h          # chip de IA
    assert "URGENTE" in h                  # comunicado urgente seedado


def test_abrir_comunicado_grava_leitura(familia):
    with SessionLocal() as db:
        com = db.scalars(select(models.Comunicado)).first()
        cid, antes = com.id, com.leram
    assert familia.get(f"/familia/comunicado/{cid}").status_code == 200
    with SessionLocal() as db:
        com = db.get(models.Comunicado, cid)
        leit = db.scalar(select(models.Leitura).where(models.Leitura.comunicado_id == cid))
    assert com.leram == antes + 1
    assert leit is not None and leit.lido


def test_professor_envia_aparece_no_feed(professor, familia):
    professor.post("/professor/enviar", data={
        "titulo": "Simulado no sábado", "corpo": "Haverá simulado no sábado às 8h.",
        "turma": "5º Ano A", "precisa_confirmar": "true",
    }, follow_redirects=False)
    assert "Simulado no sábado" in familia.get("/familia").text


def test_familia_nao_ve_comunicado_de_outra_turma(familia):
    # cria um comunicado destinado a outra turma
    with SessionLocal() as db:
        fam = db.scalar(select(models.Usuario).where(models.Usuario.email == "familia@cora.app"))
        outra = models.Comunicado(
            escola_id=fam.escola_id, titulo="Recado do 3º Ano B", autor="Coordenação",
            turma="3º Ano B", categoria="pedagogico", corpo="Conteúdo exclusivo do 3º Ano B.",
        )
        db.add(outra)
        db.commit()
        cid = outra.id
    # não aparece no feed e não pode ser aberto
    assert "Recado do 3º Ano B" not in familia.get("/familia").text
    r = familia.get(f"/familia/comunicado/{cid}", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/familia"


def test_professor_preview_ia(professor):
    r = professor.post("/professor/preview", data={
        "titulo": "URGENTE: cancelamento", "corpo": "A aula de amanhã foi cancelada.", "turma": "Toda a escola",
    })
    assert r.status_code == 200 and "Urgente" in r.text
