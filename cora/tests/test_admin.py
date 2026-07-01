"""Testes da Gestão da escola (administração de usuários)."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app import models
from app.db import SessionLocal
from app.main import app


def _uid(email: str) -> int | None:
    with SessionLocal() as db:
        u = db.scalar(select(models.Usuario).where(models.Usuario.email == email))
        return u.id if u else None


def test_admin_lista_equipe_semeada(coord):
    r = coord.get("/admin")
    assert r.status_code == 200
    assert "Roberto Diretor" in r.text and "Carla Secretaria" in r.text and "Marcos Financeiro" in r.text


def test_criar_funcionario(coord):
    coord.post("/admin/usuario", data={
        "nome": "Teste Prof", "email": "tprof@x.com", "papel": "professor", "senha": "segredo123"})
    assert "tprof@x.com" in coord.get("/admin").text


def test_criar_familia_com_aluno(coord):
    coord.post("/admin/usuario", data={
        "nome": "Fam X", "email": "famx@x.com", "papel": "familia",
        "senha": "segredo123", "filho_nome": "Kid X", "turma": "5º Ano A"})
    html = coord.get("/admin").text
    assert "famx@x.com" in html and "Kid X" in html


def test_email_duplicado_bloqueado(coord):
    coord.post("/admin/usuario", data={"nome": "A", "email": "dup@x.com", "papel": "professor", "senha": "x1234567"})
    r = coord.post("/admin/usuario", data={"nome": "B", "email": "dup@x.com", "papel": "professor"},
                   follow_redirects=False)
    assert r.status_code == 303 and "erro=email" in r.headers["location"]


def test_senha_gerada_quando_em_branco(coord):
    r = coord.post("/admin/usuario", data={"nome": "Sem Senha", "email": "ss@x.com", "papel": "secretaria"},
                   follow_redirects=False)
    assert r.status_code == 303 and "nova_senha=" in r.headers["location"]


def test_redefinir_senha_mostra_nova(coord):
    # usa um usuário descartável (não semeado) para não poluir os testes de auth
    coord.post("/admin/usuario", data={"nome": "Reset Me", "email": "resetme@x.com", "papel": "professor", "senha": "inicial123"})
    r = coord.post(f"/admin/usuario/{_uid('resetme@x.com')}/senha", follow_redirects=False)
    assert r.status_code == 303 and "nova_senha=" in r.headers["location"]


def test_usuario_desativado_nao_loga(coord):
    coord.post("/admin/usuario", data={"nome": "Off", "email": "off@x.com", "papel": "professor", "senha": "segredo123"})
    coord.post(f"/admin/usuario/{_uid('off@x.com')}/status")  # desativa
    c = TestClient(app)
    r = c.post("/login", data={"email": "off@x.com", "senha": "segredo123"}, follow_redirects=False)
    assert "erro=1" in r.headers["location"]


def test_professor_nao_acessa_admin(professor):
    r = professor.get("/admin", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/professor")


def test_familia_nao_acessa_admin(familia):
    r = familia.get("/admin", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].endswith("/familia")


def test_nao_desativa_a_propria_conta(coord):
    r = coord.post(f"/admin/usuario/{_uid('coord@cora.app')}/status", follow_redirects=False)
    assert "erro=self" in r.headers["location"]


def test_direcao_acessa_admin():
    c = TestClient(app)
    c.get("/login/demo/direcao")
    assert c.get("/admin").status_code == 200
