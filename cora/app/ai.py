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

from . import i18n, llm

# Palavras que elevam a prioridade de um comunicado.
_URGENTE = ("urgente", "emergência", "emergencial", "imediat", "antecipad", "cancelad", "acidente")
_ALTA = ("prova", "reunião", "reuniao", "vencimento", "boleto", "mensalidade", "autoriza", "saída", "saida")


def resumir(texto: str, max_frases: int = 1, lang: str = "pt") -> str:
    """Resumo de 1 frase do comunicado para o feed da família.

    Usa a Claude API quando disponível (resumo abstrativo); senão, cai num
    resumo extrativo simples (primeiras frases com conteúdo). O resumo sai no
    idioma pedido (`lang`) quando a API está ativa; offline, ele espelha o
    idioma do próprio texto recebido.
    """
    if texto and llm.disponivel():
        idioma = i18n.NOME_IDIOMA.get(lang, "português do Brasil")
        r = llm.completar(
            system=(
                "Você é a Cora, assistente de uma escola. Resuma o comunicado a seguir "
                f"para um responsável, em UMA frase curta, clara e acolhedora, em {idioma}. "
                "Responda apenas com o resumo, sem aspas nem rótulos."
            ),
            user=texto,
            max_tokens=120,
        )
        if r:
            return r

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


def insight_coordenacao(engajamento: list[dict], lang: str = "pt") -> str:
    """Gera um insight em linguagem natural para a coordenação.

    Com a Claude API, envia os números e recebe análise + recomendação no
    idioma pedido; sem ela, monta um insight localizado a partir do pior caso.
    """
    pior = min(engajamento, key=lambda t: t["taxa_leitura"])
    media = round(sum(t["taxa_leitura"] for t in engajamento) / len(engajamento))

    if llm.disponivel():
        idioma = i18n.NOME_IDIOMA.get(lang, "português do Brasil")
        linhas = "\n".join(
            f"- {t['turma']}: leitura {t['taxa_leitura']}%, {t['risco']} famílias em risco"
            for t in engajamento
        )
        r = llm.completar(
            system=(
                "Você é a Cora, analista de engajamento de uma escola. A partir dos "
                "dados de leitura por turma, escreva um insight de 2 a 3 frases para a "
                "coordenação: aponte o ponto de atenção e dê UMA recomendação prática "
                f"(ex.: comunicado por WhatsApp, contato individual). Escreva em {idioma}, "
                "tom direto e profissional."
            ),
            user=f"Taxa média: {media}%.\nPor turma:\n{linhas}",
            max_tokens=220,
            effort="medium",
        )
        if r:
            return r

    plantilhas = {
        "pt": (
            f"A taxa média de leitura está em {media}%. A turma {pior['turma']} é o "
            f"ponto de atenção ({pior['taxa_leitura']}%), com {pior['risco']} famílias "
            f"em risco de desengajamento. Recomendo um comunicado direcionado via "
            f"WhatsApp e contato individual com as 3 famílias mais inativas."
        ),
        "en": (
            f"The average read rate is {media}%. Class {pior['turma']} is the attention "
            f"point ({pior['taxa_leitura']}%), with {pior['risco']} families at risk of "
            f"disengaging. I recommend a targeted announcement via WhatsApp and "
            f"individual contact with the 3 most inactive families."
        ),
        "es": (
            f"La tasa media de lectura es del {media}%. El grupo {pior['turma']} es el "
            f"punto de atención ({pior['taxa_leitura']}%), con {pior['risco']} familias en "
            f"riesgo de desenganche. Recomiendo un comunicado dirigido por WhatsApp y "
            f"contacto individual con las 3 familias más inactivas."
        ),
    }
    return plantilhas.get(lang, plantilhas["pt"])
