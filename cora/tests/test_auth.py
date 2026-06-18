def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["produto"] == "Cora"


def test_rota_protegida_sem_login(client):
    r = client.get("/familia", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_demo(client):
    r = client.get("/login/demo/familia", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/familia"


def test_login_senha_correta(client):
    r = client.post("/login", data={"email": "prof@cora.app", "senha": "cora123"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/professor"


def test_login_senha_errada(client):
    r = client.post("/login", data={"email": "prof@cora.app", "senha": "errada"}, follow_redirects=False)
    assert r.status_code == 303 and "erro" in r.headers["location"]


def test_papel_errado_redireciona(familia):
    r = familia.get("/coordenacao", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/familia"


def test_logout(familia):
    assert familia.get("/logout", follow_redirects=False).status_code == 303
    r = familia.get("/familia", follow_redirects=False)
    assert r.headers["location"] == "/login"
