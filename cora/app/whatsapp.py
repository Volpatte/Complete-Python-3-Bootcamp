"""Camada de orquestração do WhatsApp (diferencial nº 1 da pesquisa).

Modo SIMULADO por padrão: registra cada envio como uma `EntregaWhatsApp` com
status rastreável (enviado → entregue → lido), sem depender de credenciais.

Modo REAL: se `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` estiverem no ambiente, a
função `_enviar_real` posta na WhatsApp Business API (Graph API da Meta). Os
status reais (entregue/lido) viriam dos webhooks da Meta — o ponto de entrada
está documentado em `registrar_status`.

Tudo é tolerante a falha: qualquer erro vira status "falhou", nunca quebra o app.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime

from sqlalchemy.orm import Session

from . import models


def modo() -> str:
    """'real' se houver credenciais da Meta; senão 'simulado'."""
    if os.getenv("WHATSAPP_TOKEN") and os.getenv("WHATSAPP_PHONE_ID"):
        return "real"
    return "simulado"


def _enviar_real(telefone: str, texto: str) -> bool:
    """Envia de verdade via Graph API. Retorna True se aceito (HTTP 2xx)."""
    token = os.environ["WHATSAPP_TOKEN"]
    phone_id = os.environ["WHATSAPP_PHONE_ID"]
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": texto},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return 200 <= resp.status < 300


def enviar(db: Session, usuario: models.Usuario, texto: str, referencia: str) -> models.EntregaWhatsApp | None:
    """Espelha uma mensagem no WhatsApp da família (se ela optou). Idempotência e
    commit ficam a cargo de quem chama."""
    if not usuario.whatsapp_optin:
        return None

    m = modo()
    status = "enviado"
    if m == "real":
        try:
            status = "enviado" if _enviar_real(usuario.telefone, texto) else "falhou"
        except Exception:
            status = "falhou"

    agora = datetime.utcnow()
    entrega = models.EntregaWhatsApp(
        escola_id=usuario.escola_id, usuario_id=usuario.id, destinatario_nome=usuario.nome,
        referencia=referencia, resumo=texto[:140], status=status, modo=m,
        criado_em=agora, atualizado_em=agora,
    )
    db.add(entrega)
    return entrega


# Avanço de status no modo simulado (no modo real, isto vem dos webhooks da Meta).
_PROXIMO = {"enviado": "entregue", "entregue": "lido"}


def registrar_status(entrega: models.EntregaWhatsApp, novo: str) -> None:
    entrega.status = novo
    entrega.atualizado_em = datetime.utcnow()


def avancar_simulado(entregas: list[models.EntregaWhatsApp]) -> int:
    """Demonstra a transição enviado→entregue→lido. Retorna quantas avançaram."""
    n = 0
    for e in entregas:
        prox = _PROXIMO.get(e.status)
        if prox:
            registrar_status(e, prox)
            n += 1
    return n
