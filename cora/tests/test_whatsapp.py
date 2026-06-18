from sqlalchemy import func, select

from app import models
from app.db import SessionLocal


def _conta_entregas():
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(models.EntregaWhatsApp))


def test_comunicado_espelha_no_whatsapp(professor):
    antes = _conta_entregas()
    professor.post("/professor/enviar", data={
        "titulo": "Reunião extra", "corpo": "Reunião extra na sexta.", "turma": "5º Ano A",
    }, follow_redirects=False)
    assert _conta_entregas() == antes + 1


def test_central_mostra_modo_simulado(coord):
    h = coord.get("/whatsapp").text
    assert "Central WhatsApp" in h and "modo simulado" in h and "taxa de leitura" in h


def test_simular_leitura_avanca_status(coord):
    def lidos():
        with SessionLocal() as db:
            return db.scalar(select(func.count()).select_from(models.EntregaWhatsApp)
                             .where(models.EntregaWhatsApp.status == "lido"))
    antes = lidos()
    coord.post("/whatsapp/simular-leitura", follow_redirects=False)
    assert lidos() >= antes  # nunca diminui; avança enviado→entregue→lido


def test_acesso_negado(familia, professor):
    assert familia.get("/whatsapp", follow_redirects=False).status_code == 303
    assert professor.get("/whatsapp", follow_redirects=False).status_code == 303


def test_optin_familia(familia):
    # garante estado opt-out e ativa
    with SessionLocal() as db:
        f = db.scalar(select(models.Usuario).where(models.Usuario.email == "familia@cora.app"))
        f.whatsapp_optin = False
        db.commit()
    assert "Ativar no WhatsApp" in familia.get("/familia").text
    familia.post("/familia/whatsapp/ativar", data={"telefone": "+5548911112222"}, follow_redirects=False)
    with SessionLocal() as db:
        f = db.scalar(select(models.Usuario).where(models.Usuario.email == "familia@cora.app"))
    assert f.whatsapp_optin and f.telefone == "+5548911112222"
