import json


def test_assistente_api(familia):
    for q, termo in [
        ("meu filho faltou?", "faltas"),
        ("cardápio de hoje", "cardápio"),
        ("quero pagar o boleto", "mensalidade"),
    ]:
        r = familia.post("/api/assistente", json={"mensagem": q})
        d = r.json()
        assert r.status_code == 200 and d["texto"] and len(d["sugestoes"]) >= 1
        assert termo.lower() in d["texto"].lower()


def test_assistente_exige_login(client):
    r = client.post("/api/assistente", json={"mensagem": "oi"}, follow_redirects=False)
    assert r.status_code == 303


def test_loja(familia):
    h = familia.get("/familia/loja").text
    assert "Loja da escola" in h and "Comprar via Pix" in h and "uniforme" in h.lower()


def test_fab_cora_em_todas_as_telas(familia):
    for p in ["/familia", "/familia/mensagens", "/familia/agenda", "/familia/loja", "/familia/saude"]:
        assert "fab-cora" in familia.get(p).text


def test_pwa_manifest(client):
    r = client.get("/static/manifest.webmanifest")
    m = json.loads(r.text)
    assert r.status_code == 200
    assert m["start_url"] == "/familia" and m["display"] == "standalone" and len(m["icons"]) == 2


def test_pwa_service_worker(client):
    r = client.get("/sw.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert r.headers.get("service-worker-allowed") == "/"


def test_pwa_assets(client):
    assert client.get("/static/icon-192.png").status_code == 200
    assert client.get("/static/icon-512.png").status_code == 200
    assert client.get("/static/offline.html").status_code == 200
