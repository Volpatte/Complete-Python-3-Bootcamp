"""Camada de IA do Cora — o principal diferencial.

No protótipo, as funções rodam com heurísticas locais (sem chave de API,
sem rede) para que a navegação funcione em qualquer ambiente. Cada função
está isolada de propósito: no MVP de verdade, troca-se o corpo por uma
chamada à Claude API (Anthropic) mantendo a mesma assinatura.

    Exemplo de como ficaria a versão real (pseudo-código):

        from anthropic import Anthropic
        client = Anthropic()

        def resumir(texto: str) -> str:
            msg = client.messages.create(
                model="claude-sonnet-4-6",   # rápido/barato p/ alto volume
                max_tokens=120,
                messages=[{
                    "role": "user",
                    "content": f"Resuma para um responsável, em 1 frase "
                               f"objetiva e acolhedora:\\n\\n{texto}",
                }],
            )
            return msg.content[0].text

Por enquanto, o que está abaixo é determinístico e offline.
"""

from __future__ import annotations

import re

# Palavras que elevam a prioridade de um comunicado.
_URGENTE = ("urgente", "emergência", "emergencial", "imediat", "antecipad", "cancelad", "acidente")
_ALTA = ("prova", "reunião", "reuniao", "vencimento", "boleto", "mensalidade", "autoriza", "saída", "saida")


def resumir(texto: str, max_frases: int = 1) -> str:
    """Resumo extrativo simples: pega a(s) primeira(s) frase(s) com conteúdo.

    No MVP vira uma chamada à Claude API para resumo abstrativo de verdade.
    """
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    frases = [f for f in frases if len(f) > 20]
    resumo = " ".join(frases[:max_frases])
    return resumo or texto[:140]


def prioridade(titulo: str, corpo: str) -> dict:
    """Classifica a prioridade do comunicado para ordenar/destacar o feed."""
    txt = f"{titulo} {corpo}".lower()
    if any(p in txt for p in _URGENTE):
        return {"nivel": "alta", "rotulo": "Urgente", "cor": "#dc2626"}
    if any(p in txt for p in _ALTA):
        return {"nivel": "media", "rotulo": "Importante", "cor": "#d97706"}
    return {"nivel": "baixa", "rotulo": "Informativo", "cor": "#2563eb"}


def acao_sugerida(categoria: str, precisa_confirmar: bool) -> str | None:
    """O que a IA sugere que a família faça — reduz fricção."""
    if precisa_confirmar:
        return "Confirmar presença"
    if categoria == "financeiro":
        return "Pagar via Pix"
    if categoria == "pedagogico":
        return "Ver detalhes do projeto"
    return None


def sugestoes_resposta(categoria: str, precisa_confirmar: bool) -> list[str]:
    """Respostas rápidas sugeridas (estilo 'smart reply')."""
    if precisa_confirmar:
        return [
            "Confirmo a presença. Obrigada!",
            "Não poderei comparecer, mas envio um representante.",
            "Tenho uma dúvida sobre o horário.",
        ]
    if categoria == "financeiro":
        return ["Já efetuei o pagamento.", "Preciso negociar o vencimento."]
    return ["Recebido, obrigada!", "Tenho uma dúvida."]


def traduzir_rotulo(idioma_destino: str) -> str:
    """Demonstra a tradução automática (multi-idioma para famílias estrangeiras)."""
    nomes = {
        "es": "Traducido al español (automático)",
        "en": "Translated to English (automatic)",
        "ht": "Tradui an kreyòl ayisyen (otomatik)",
        "pt-BR": "Original em português",
    }
    return nomes.get(idioma_destino, "Tradução automática")


def insight_coordenacao(engajamento: list[dict]) -> str:
    """Gera um insight em linguagem natural para a coordenação.

    No MVP, a Claude API recebe os números e devolve a análise + recomendação.
    """
    pior = min(engajamento, key=lambda t: t["taxa_leitura"])
    media = round(sum(t["taxa_leitura"] for t in engajamento) / len(engajamento))
    return (
        f"A taxa média de leitura está em {media}%. A turma {pior['turma']} é o "
        f"ponto de atenção ({pior['taxa_leitura']}%), com {pior['risco']} famílias "
        f"em risco de desengajamento. Recomendo um comunicado direcionado via "
        f"WhatsApp e contato individual com as 3 famílias mais inativas."
    )
