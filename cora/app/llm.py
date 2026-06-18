"""Integração opcional com a Claude API (Anthropic).

Se `ANTHROPIC_API_KEY` estiver no ambiente e o pacote `anthropic` instalado, as
funções de IA usam o modelo de verdade (`claude-opus-4-8` por padrão). Caso
contrário — sem chave, sem pacote, ou erro de rede — caem automaticamente nas
heurísticas offline. A demonstração nunca quebra.

Configurável por env:
    ANTHROPIC_API_KEY   ativa a IA real
    CORA_MODELO         troca o modelo (padrão: claude-opus-4-8)
"""

from __future__ import annotations

import os

MODELO = os.getenv("CORA_MODELO", "claude-opus-4-8")

_cache: dict = {}  # cacheia só o client bem-sucedido (não o None)


def _client():
    """Retorna o client da Anthropic, ou None se a IA real não estiver disponível.

    Só memoiza o client criado com sucesso — assim, se a chave for definida depois
    do primeiro acesso, a IA real passa a funcionar sem reiniciar o app.
    """
    if "c" in _cache:
        return _cache["c"]
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
    except Exception:
        return None
    _cache["c"] = client
    return client


def disponivel() -> bool:
    return _client() is not None


def completar(system: str, user: str, max_tokens: int = 400, effort: str = "low") -> str | None:
    """Uma chamada simples à Claude API. Retorna o texto, ou None se indisponível/erro.

    `effort` controla profundidade/custo (low|medium|high). Resumo e tradução
    usam `low`; análises da coordenação usam `medium`.
    """
    client = _client()
    if client is None:
        return None

    def _chamar(com_effort: bool) -> str:
        kwargs = dict(
            model=MODELO,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if com_effort:
            kwargs["output_config"] = {"effort": effort}
        msg = client.messages.create(**kwargs)
        return "".join(b.text for b in msg.content if b.type == "text").strip()

    try:
        return _chamar(com_effort=True) or None
    except TypeError:
        # SDK antigo sem `output_config` — tenta sem.
        try:
            return _chamar(com_effort=False) or None
        except Exception:
            return None
    except Exception:
        return None
