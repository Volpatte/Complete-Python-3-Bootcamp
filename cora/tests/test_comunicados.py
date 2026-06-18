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


def test_professor_preview_ia(professor):
    r = professor.post("/professor/preview", data={
        "titulo": "URGENTE: cancelamento", "corpo": "A aula de amanhã foi cancelada.", "turma": "Toda a escola",
    })
    assert r.status_code == 200 and "Urgente" in r.text
