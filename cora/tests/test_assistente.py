"""Assistente Cora trilíngue — a resposta sai no idioma do usuário."""


def _perguntar(client, mensagem: str) -> str:
    return client.post("/api/assistente", json={"mensagem": mensagem}).json()["texto"]


def test_assistente_pt_padrao(familia):
    # cardápio em português (valor de dados traduzido por i18n)
    assert "frango grelhado" in _perguntar(familia, "cardápio de hoje")


def test_assistente_en(familia):
    familia.get("/lang/en")
    texto = _perguntar(familia, "today's menu")
    assert "grilled chicken" in texto


def test_assistente_es(familia):
    familia.get("/lang/es")
    texto = _perguntar(familia, "menú de hoy")
    assert "pollo a la parrilla" in texto


def test_assistente_saudacao_vazio(familia):
    familia.get("/lang/en")
    r = familia.post("/api/assistente", json={"mensagem": ""}).json()
    assert r["texto"] and isinstance(r["sugestoes"], list) and r["sugestoes"]
