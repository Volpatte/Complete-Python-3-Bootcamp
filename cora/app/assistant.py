"""Assistente Cora — chatbot conversacional para a família (diferencial nº 2).

A pesquisa de mercado mostrou que ninguém oferece um assistente que responda
os pais 24/7 ("meu filho faltou?", cardápio, agenda, financeiro). Este módulo
implementa um roteador de intenções *offline* (sem rede/chave) para o protótipo.

No MVP, isto vira a Claude API com **tool use**: o modelo entende a pergunta em
linguagem natural e chama ferramentas que leem o ERP/financeiro/agenda. Ex.:

    from anthropic import Anthropic
    client = Anthropic()
    TOOLS = [
        {"name": "consultar_frequencia", "description": "...", "input_schema": {...}},
        {"name": "consultar_cardapio",   "description": "...", "input_schema": {...}},
        {"name": "consultar_financeiro", "description": "...", "input_schema": {...}},
    ]
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system="Você é a Cora, assistente acolhedora da escola. Responda em "
               "português, com no máximo 3 frases, tom caloroso.",
        tools=TOOLS,
        messages=historico,
    )

Por enquanto, intenção é detectada por palavras-chave e a resposta usa os
dados de exemplo de data.py.
"""

from __future__ import annotations

from . import data, llm

_MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _data(d) -> str:
    return f"{d.day:02d} de {['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][d.month-1]}"


def _tem(texto: str, *palavras: str) -> bool:
    return any(p in texto for p in palavras)


def _contexto_familia() -> str:
    """Monta o contexto factual que ancora as respostas da IA (vem do ERP no MVP)."""
    filho = data.RESPONSAVEL["filho"]
    f = data.FREQUENCIA
    c = data.CARDAPIO_HOJE
    fin = data.FINANCEIRO
    pend = [x for x in data.TAREFAS if x["status"] == "pendente"]
    tarefas = "; ".join(f"{x['disciplina']}: {x['titulo']} (até {x['entrega'].strftime('%d/%m')})" for x in pend)
    eventos = "; ".join(f"{e['data'].strftime('%d/%m')} {e['titulo']}" for e in data.EVENTOS[:3])
    return (
        f"Aluno: {filho} ({data.RESPONSAVEL['turma']}).\n"
        f"Frequência: {f['faltas']} faltas, presença {f['presenca_pct']}% em "
        f"{f['dias_letivos']} dias; última falta em {_data(f['ultima_falta'])}.\n"
        f"Cardápio de hoje: almoço {c['principal']}; salada {c['salada']}; "
        f"lanche {c['lanche']}; sobremesa {c['sobremesa']}.\n"
        f"Financeiro: mensalidade de {fin['mes']} {fin['valor']}, vence "
        f"{_data(fin['vencimento'])}, status {fin['status']}, aceita Pix: {fin['aceita_pix']}.\n"
        f"Tarefas pendentes: {tarefas or 'nenhuma'}.\n"
        f"Próximos eventos: {eventos or 'nenhum'}."
    )


def responder(mensagem: str) -> dict:
    """Resposta da Cora para o responsável: {"texto": str, "sugestoes": list[str]}.

    Quando a Claude API está disponível, o texto é gerado por ela (ancorado nos
    dados reais do aluno); as sugestões de continuação vêm sempre do roteador
    heurístico. Sem a API, tudo cai no roteador heurístico.
    """
    base = _responder_heuristico(mensagem)
    if (mensagem or "").strip() and llm.disponivel():
        resposta = llm.completar(
            system=(
                "Você é a Cora, assistente acolhedora de uma escola, conversando com "
                "um responsável (mãe/pai) no chat. Responda em português do Brasil, em "
                "no máximo 3 frases, com tom caloroso e prático. Use SOMENTE os dados "
                "abaixo; se a resposta não estiver neles, diga gentilmente que vai "
                "encaminhar à secretaria. Nunca invente notas, faltas ou valores.\n\n"
                + _contexto_familia()
            ),
            user=mensagem,
            max_tokens=300,
        )
        if resposta:
            base = {"texto": resposta, "sugestoes": base["sugestoes"]}
    return base


def _responder_heuristico(mensagem: str) -> dict:
    """Roteador de intenções offline (sem rede). Base de sugestões e fallback."""
    t = (mensagem or "").lower().strip()
    filho = data.RESPONSAVEL["filho"].split(" ")[0]

    # --- saudação / vazio ---
    if not t or _tem(t, "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "ei "):
        return {
            "texto": (
                f"Oi! 💜 Eu sou a Cora, assistente da escola do {filho}. "
                "Posso te ajudar com faltas, cardápio, agenda, tarefas e financeiro, "
                "a qualquer hora. O que você precisa hoje?"
            ),
            "sugestoes": ["O Pedro faltou?", "Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
        }

    # --- frequência / faltas ---
    if _tem(t, "falt", "frequ", "presen", "atras"):
        f = data.FREQUENCIA
        return {
            "texto": (
                f"O {filho} tem {f['faltas']} faltas no período (presença de "
                f"{f['presenca_pct']}% em {f['dias_letivos']} dias letivos). A última "
                f"foi em {_data(f['ultima_falta'])}. Quer que eu te avise no WhatsApp "
                "sempre que houver uma nova falta?"
            ),
            "sugestoes": ["Sim, me avise das faltas", "Tem prova essa semana?", "Cardápio de hoje"],
        }

    # --- cardápio ---
    if _tem(t, "cardáp", "cardap", "almoç", "almoc", "comida", "merenda", "lanche", "comer"):
        c = data.CARDAPIO_HOJE
        return {
            "texto": (
                f"O cardápio de hoje 🍽️\n• Almoço: {c['principal']}\n"
                f"• Salada: {c['salada']}\n• Lanche: {c['lanche']}\n"
                f"• Sobremesa: {c['sobremesa']}"
            ),
            "sugestoes": ["Cardápio da semana", "O Pedro faltou?", "Tem prova essa semana?"],
        }

    # --- financeiro / boleto ---
    if _tem(t, "boleto", "mensalid", "pagar", "pagamento", "financ", "pix", "fatura", "valor"):
        fin = data.FINANCEIRO
        extra = " Posso gerar um Pix com confirmação na hora, se preferir." if fin["aceita_pix"] else ""
        return {
            "texto": (
                f"A mensalidade de {fin['mes']} é de {fin['valor']}, com vencimento em "
                f"{_data(fin['vencimento'])} (status: {fin['status']}).{extra}"
            ),
            "sugestoes": ["Gerar Pix agora", "Ver boleto", "Negociar vencimento"],
        }

    # --- tarefas / lição ---
    if _tem(t, "tarefa", "lição", "licao", "dever", "lição de casa", "atividade"):
        pend = [x for x in data.TAREFAS if x["status"] == "pendente"]
        linhas = "\n".join(f"• {x['disciplina']}: {x['titulo']} (até {x['entrega'].strftime('%d/%m')})" for x in pend)
        return {
            "texto": f"O {filho} tem {len(pend)} tarefas pendentes 📚\n{linhas}",
            "sugestoes": ["Tem prova essa semana?", "Cardápio de hoje", "O Pedro faltou?"],
        }

    # --- agenda / provas / reunião / eventos ---
    if _tem(t, "prova", "agenda", "evento", "reuni", "amanhã", "amanha", "semana", "calend", "saída", "saida", "horário", "horario"):
        prox = data.EVENTOS[:3]
        linhas = "\n".join(f"• {e['data'].strftime('%d/%m')} — {e['titulo']}" for e in prox)
        return {
            "texto": f"Os próximos compromissos do {filho} 📅\n{linhas}\n\nQuer que eu ative lembretes no WhatsApp?",
            "sugestoes": ["Sim, ativar lembretes", "Tem tarefa pendente?", "Cardápio de hoje"],
        }

    # --- agradecimento ---
    if _tem(t, "obrigad", "valeu", "brigad", "tks", "thanks"):
        return {
            "texto": "Imagina! 💜 Estou por aqui 24h sempre que precisar. Cuida bem do "
            f"{filho} por mim 😊",
            "sugestoes": ["Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
        }

    # --- fallback ---
    return {
        "texto": (
            "Ainda estou aprendendo 🙂 mas já consigo te ajudar com **faltas**, "
            "**cardápio**, **agenda**, **tarefas** e **financeiro**. No app final, o "
            "que eu não souber eu encaminho direto para a secretaria. Sobre o que "
            "você quer saber?"
        ),
        "sugestoes": ["O Pedro faltou?", "Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
    }
