from sqlalchemy import func, select

from app import models
from app.db import SessionLocal


def test_familia_ve_ficha_e_medicacao(familia):
    h = familia.get("/familia/saude").text
    assert "Ficha médica" in h
    assert "Amendoim" in h                 # alergia seedada
    assert "Salbutamol" in h               # medicação seedada
    assert "Histórico de administração" in h


def test_familia_edita_ficha(familia):
    familia.post("/familia/saude/ficha", data={
        "tipo_sanguineo": "A+", "alergias": "Amendoim", "condicoes": "Asma",
        "restricoes": "", "contato_emergencia": "Juliana", "convenio": "Unimed",
        "observacoes": "usa óculos",
    }, follow_redirects=False)
    with SessionLocal() as db:
        f = db.scalar(select(models.FichaSaude).where(models.FichaSaude.aluno_nome == "Pedro Prado"))
    assert f.tipo_sanguineo == "A+" and "óculos" in f.observacoes


def test_familia_autoriza_medicacao(familia):
    antes = _conta_med()
    familia.post("/familia/saude/medicacao", data={
        "nome": "Dipirona", "dosagem": "10 gotas", "horario": "se febre", "instrucoes": "acima de 38C",
    }, follow_redirects=False)
    assert _conta_med() == antes + 1


def test_coordenacao_registra_administracao_e_notifica(coord, familia):
    with SessionLocal() as db:
        med = db.scalar(select(models.Medicacao).where(models.Medicacao.nome.contains("Salbutamol")))
        adm_antes = db.scalar(select(func.count()).select_from(models.AdministracaoMed))
        wpp_antes = db.scalar(select(func.count()).select_from(models.EntregaWhatsApp))

    coord.post(f"/saude/administrar/{med.id}",
               data={"dose": "2 jatos", "observacao": "crise leve, ok"}, follow_redirects=False)

    with SessionLocal() as db:
        adm = db.scalar(select(func.count()).select_from(models.AdministracaoMed))
        wpp = db.scalar(select(func.count()).select_from(models.EntregaWhatsApp))
    assert adm == adm_antes + 1
    assert wpp == wpp_antes + 1                       # avisou no WhatsApp
    assert "crise leve, ok" in familia.get("/familia/saude").text   # família vê


def test_acesso_negado_saude(familia):
    assert familia.get("/saude", follow_redirects=False).status_code == 303


def _conta_med() -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(models.Medicacao))
