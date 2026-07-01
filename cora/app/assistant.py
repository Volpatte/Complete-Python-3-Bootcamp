"""Assistente Cora — chatbot conversacional para a família (diferencial nº 2).

A pesquisa de mercado mostrou que ninguém oferece um assistente que responda
os pais 24/7 ("meu filho faltou?", cardápio, agenda, financeiro). Este módulo
implementa um roteador de intenções *offline* (sem rede/chave) para o protótipo.

Agora o assistente é **trilíngue** (PT/EN/ES): a intenção é detectada por
palavras-chave nos três idiomas e cada resposta é montada no idioma pedido.
Os valores vindos dos dados de exemplo (cardápio, disciplinas, títulos de
tarefa/evento, mês/status financeiro) passam por ``i18n.tr`` para sair
traduzidos; nomes próprios (o nome do filho) nunca são traduzidos.

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
        system="Você é a Cora, assistente acolhedora da escola. Responda no "
               "idioma da família, com no máximo 3 frases, tom caloroso.",
        tools=TOOLS,
        messages=historico,
    )

Por enquanto, intenção é detectada por palavras-chave e a resposta usa os
dados de exemplo de data.py.
"""

from __future__ import annotations

from . import data, i18n, llm

# Nomes de mês completos por idioma (índice 0 = janeiro).
_MESES_NOME = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
           "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio",
           "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
}


def _data(d, lang: str = "pt") -> str:
    """Formata uma data como '17 de junho' / 'June 17' / '17 de junio'."""
    nome = _MESES_NOME.get(lang, _MESES_NOME["pt"])[d.month - 1]
    if lang == "en":
        return f"{nome} {d.day:02d}"
    return f"{d.day:02d} de {nome}"


def _tem(texto: str, *palavras: str) -> bool:
    return any(p in texto for p in palavras)


def _tem_palavra(texto: str, *palavras: str) -> bool:
    """Match por palavra inteira (evita 'hi' casar dentro de 'this')."""
    tokens = set(texto.replace("?", " ").replace("!", " ").replace(",", " ")
                 .replace(".", " ").split())
    return any(p in tokens for p in palavras)


def _contexto_familia(lang: str = "pt") -> str:
    """Monta o contexto factual que ancora as respostas da IA (vem do ERP no MVP)."""
    filho = data.RESPONSAVEL["filho"]  # nome próprio — não traduzir
    f = data.FREQUENCIA
    c = data.CARDAPIO_HOJE
    fin = data.FINANCEIRO
    pend = [x for x in data.TAREFAS if x["status"] == "pendente"]
    tarefas = "; ".join(
        f"{i18n.tr(x['disciplina'], lang)}: {i18n.tr(x['titulo'], lang)} "
        f"(até {x['entrega'].strftime('%d/%m')})"
        for x in pend
    )
    eventos = "; ".join(
        f"{e['data'].strftime('%d/%m')} {i18n.tr(e['titulo'], lang)}"
        for e in data.EVENTOS[:3]
    )
    return (
        f"Aluno: {filho} ({data.RESPONSAVEL['turma']}).\n"
        f"Frequência: {f['faltas']} faltas, presença {f['presenca_pct']}% em "
        f"{f['dias_letivos']} dias; última falta em {_data(f['ultima_falta'], lang)}.\n"
        f"Cardápio de hoje: almoço {i18n.tr(c['principal'], lang)}; "
        f"salada {i18n.tr(c['salada'], lang)}; "
        f"lanche {i18n.tr(c['lanche'], lang)}; "
        f"sobremesa {i18n.tr(c['sobremesa'], lang)}.\n"
        f"Financeiro: mensalidade de {i18n.tr(fin['mes'], lang)} {fin['valor']}, vence "
        f"{_data(fin['vencimento'], lang)}, status {i18n.tr(fin['status'], lang)}, "
        f"aceita Pix: {fin['aceita_pix']}.\n"
        f"Tarefas pendentes: {tarefas or 'nenhuma'}.\n"
        f"Próximos eventos: {eventos or 'nenhum'}."
    )


def responder(mensagem: str, lang: str = "pt") -> dict:
    """Resposta da Cora para o responsável: {"texto": str, "sugestoes": list[str]}.

    Quando a Claude API está disponível, o texto é gerado por ela (ancorado nos
    dados reais do aluno) no idioma ``lang``; as sugestões de continuação vêm
    sempre do roteador heurístico. Sem a API, tudo cai no roteador heurístico.
    """
    base = _responder_heuristico(mensagem, lang)
    if (mensagem or "").strip() and llm.disponivel():
        idioma = i18n.NOME_IDIOMA.get(lang, "português do Brasil")
        resposta = llm.completar(
            system=(
                "Você é a Cora, assistente acolhedora de uma escola, conversando com "
                f"um responsável (mãe/pai) no chat. Responda em {idioma}, em "
                "no máximo 3 frases, com tom caloroso e prático. Use SOMENTE os dados "
                "abaixo; se a resposta não estiver neles, diga gentilmente que vai "
                "encaminhar à secretaria. Nunca invente notas, faltas ou valores.\n\n"
                + _contexto_familia(lang)
            ),
            user=mensagem,
            max_tokens=300,
        )
        if resposta:
            base = {"texto": resposta, "sugestoes": base["sugestoes"]}
    return base


def _responder_heuristico(mensagem: str, lang: str = "pt") -> dict:
    """Roteador de intenções offline (sem rede). Base de sugestões e fallback.

    Detecta a intenção por palavras-chave em PT + EN + ES e monta a resposta no
    idioma ``lang`` a partir de dicionários por idioma.
    """
    t = (mensagem or "").lower().strip()
    filho = data.RESPONSAVEL["filho"].split(" ")[0]  # primeiro nome — não traduzir
    L = lang if lang in ("pt", "en", "es") else "pt"

    # --- saudação / vazio ---
    # Frases longas casam por substring; tokens curtos (oi/hi/hola…) por palavra
    # inteira, para não casar dentro de outras palavras (ex.: 'hi' em 'this').
    if not t or _tem(
        t, "bom dia", "boa tarde", "boa noite", "buenos días", "buenas tardes", "buenas noches",
    ) or _tem_palavra(
        t, "oi", "olá", "ola", "ei", "hi", "hello", "hey", "hola", "buenas", "hola,",
    ):
        textos = {
            "pt": (
                f"Oi! 💜 Eu sou a Cora, assistente da escola do {filho}. "
                "Posso te ajudar com faltas, cardápio, agenda, tarefas e financeiro, "
                "a qualquer hora. O que você precisa hoje?"
            ),
            "en": (
                f"Hi! 💜 I'm Cora, the school assistant for {filho}. "
                "I can help you with absences, the menu, the calendar, homework and "
                "billing, anytime. What do you need today?"
            ),
            "es": (
                f"¡Hola! 💜 Soy Cora, la asistente de la escuela de {filho}. "
                "Puedo ayudarte con faltas, menú, agenda, tareas y pagos, a cualquier "
                "hora. ¿Qué necesitas hoy?"
            ),
        }
        sugestoes = {
            "pt": [f"O {filho} faltou?", "Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
            "en": [f"Did {filho} miss school?", "Today's menu", "Any test this week?", "June invoice"],
            "es": [f"¿{filho} faltó?", "Menú de hoy", "¿Hay examen esta semana?", "Factura de junio"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- frequência / faltas ---
    if _tem(
        t, "falt", "frequ", "presen", "atras",
        "absan", "absence", "absent", "attend", "miss",
        "asisten", "inasisten", "ausen",
    ):
        f = data.FREQUENCIA
        ult = _data(f["ultima_falta"], L)
        textos = {
            "pt": (
                f"O {filho} tem {f['faltas']} faltas no período (presença de "
                f"{f['presenca_pct']}% em {f['dias_letivos']} dias letivos). A última "
                f"foi em {ult}. Quer que eu te avise no WhatsApp "
                "sempre que houver uma nova falta?"
            ),
            "en": (
                f"{filho} has {f['faltas']} absences in the period ("
                f"{f['presenca_pct']}% attendance across {f['dias_letivos']} school days). "
                f"The last one was on {ult}. Would you like me to notify you on WhatsApp "
                "whenever there's a new absence?"
            ),
            "es": (
                f"{filho} tiene {f['faltas']} faltas en el período (asistencia del "
                f"{f['presenca_pct']}% en {f['dias_letivos']} días lectivos). La última "
                f"fue el {ult}. ¿Quieres que te avise por WhatsApp "
                "cada vez que haya una nueva falta?"
            ),
        }
        sugestoes = {
            "pt": ["Sim, me avise das faltas", "Tem prova essa semana?", "Cardápio de hoje"],
            "en": ["Yes, notify me about absences", "Any test this week?", "Today's menu"],
            "es": ["Sí, avísame de las faltas", "¿Hay examen esta semana?", "Menú de hoy"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- cardápio ---
    if _tem(
        t, "cardáp", "cardap", "almoç", "almoc", "comida", "merenda", "lanche", "comer",
        "menu", "menú", "lunch", "meal", "food", "snack", "eat",
        "almuerzo", "comida", "merienda",
    ):
        c = data.CARDAPIO_HOJE
        principal = i18n.tr(c["principal"], L)
        salada = i18n.tr(c["salada"], L)
        lanche = i18n.tr(c["lanche"], L)
        sobremesa = i18n.tr(c["sobremesa"], L)
        textos = {
            "pt": (
                f"O cardápio de hoje 🍽️\n• Almoço: {principal}\n"
                f"• Salada: {salada}\n• Lanche: {lanche}\n"
                f"• Sobremesa: {sobremesa}"
            ),
            "en": (
                f"Today's menu 🍽️\n• Lunch: {principal}\n"
                f"• Salad: {salada}\n• Snack: {lanche}\n"
                f"• Dessert: {sobremesa}"
            ),
            "es": (
                f"El menú de hoy 🍽️\n• Almuerzo: {principal}\n"
                f"• Ensalada: {salada}\n• Merienda: {lanche}\n"
                f"• Postre: {sobremesa}"
            ),
        }
        sugestoes = {
            "pt": ["Cardápio da semana", f"O {filho} faltou?", "Tem prova essa semana?"],
            "en": ["Weekly menu", f"Did {filho} miss school?", "Any test this week?"],
            "es": ["Menú de la semana", f"¿{filho} faltó?", "¿Hay examen esta semana?"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- financeiro / boleto ---
    if _tem(
        t, "boleto", "mensalid", "pagar", "pagamento", "financ", "pix", "fatura", "valor",
        "tuition", "payment", "invoice", "fee", "bill",
        "pago", "cuota", "factura", "pagar",
    ):
        fin = data.FINANCEIRO
        mes = i18n.tr(fin["mes"], L)
        status = i18n.tr(fin["status"], L)
        venc = _data(fin["vencimento"], L)
        extra_pt = " Posso gerar um Pix com confirmação na hora, se preferir." if fin["aceita_pix"] else ""
        extra_en = " I can generate a Pix with instant confirmation, if you prefer." if fin["aceita_pix"] else ""
        extra_es = " Puedo generar un Pix con confirmación al instante, si prefieres." if fin["aceita_pix"] else ""
        textos = {
            "pt": (
                f"A mensalidade de {mes} é de {fin['valor']}, com vencimento em "
                f"{venc} (status: {status}).{extra_pt}"
            ),
            "en": (
                f"The {mes} tuition is {fin['valor']}, due on "
                f"{venc} (status: {status}).{extra_en}"
            ),
            "es": (
                f"La mensualidad de {mes} es de {fin['valor']}, con vencimiento el "
                f"{venc} (estado: {status}).{extra_es}"
            ),
        }
        sugestoes = {
            "pt": ["Gerar Pix agora", "Ver boleto", "Negociar vencimento"],
            "en": ["Generate Pix now", "View invoice", "Renegotiate due date"],
            "es": ["Generar Pix ahora", "Ver factura", "Renegociar vencimiento"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- tarefas / lição ---
    if _tem(
        t, "tarefa", "lição", "licao", "dever", "atividade",
        "homework", "assignment", "task",
        "tarea", "deber",
    ):
        pend = [x for x in data.TAREFAS if x["status"] == "pendente"]
        linhas = "\n".join(
            f"• {i18n.tr(x['disciplina'], L)}: {i18n.tr(x['titulo'], L)} "
            f"(até {x['entrega'].strftime('%d/%m')})"
            if L == "pt" else
            (f"• {i18n.tr(x['disciplina'], L)}: {i18n.tr(x['titulo'], L)} "
             f"(due {x['entrega'].strftime('%d/%m')})" if L == "en" else
             f"• {i18n.tr(x['disciplina'], L)}: {i18n.tr(x['titulo'], L)} "
             f"(entrega {x['entrega'].strftime('%d/%m')})")
            for x in pend
        )
        textos = {
            "pt": f"O {filho} tem {len(pend)} tarefas pendentes 📚\n{linhas}",
            "en": f"{filho} has {len(pend)} pending tasks 📚\n{linhas}",
            "es": f"{filho} tiene {len(pend)} tareas pendientes 📚\n{linhas}",
        }
        sugestoes = {
            "pt": ["Tem prova essa semana?", "Cardápio de hoje", f"O {filho} faltou?"],
            "en": ["Any test this week?", "Today's menu", f"Did {filho} miss school?"],
            "es": ["¿Hay examen esta semana?", "Menú de hoy", f"¿{filho} faltó?"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- agenda / provas / reunião / eventos ---
    if _tem(
        t, "prova", "agenda", "evento", "reuni", "amanhã", "amanha", "semana",
        "calend", "saída", "saida", "horário", "horario",
        "exam", "test", "event", "meeting", "week", "schedule", "tomorrow",
        "examen", "reunión", "reunion", "semana", "mañana", "manana", "salida",
    ):
        prox = data.EVENTOS[:3]
        linhas = "\n".join(
            f"• {e['data'].strftime('%d/%m')} — {i18n.tr(e['titulo'], L)}" for e in prox
        )
        textos = {
            "pt": (
                f"Os próximos compromissos do {filho} 📅\n{linhas}\n\n"
                "Quer que eu ative lembretes no WhatsApp?"
            ),
            "en": (
                f"{filho}'s upcoming events 📅\n{linhas}\n\n"
                "Would you like me to turn on WhatsApp reminders?"
            ),
            "es": (
                f"Los próximos compromisos de {filho} 📅\n{linhas}\n\n"
                "¿Quieres que active recordatorios en WhatsApp?"
            ),
        }
        sugestoes = {
            "pt": ["Sim, ativar lembretes", "Tem tarefa pendente?", "Cardápio de hoje"],
            "en": ["Yes, turn on reminders", "Any pending tasks?", "Today's menu"],
            "es": ["Sí, activar recordatorios", "¿Hay tareas pendientes?", "Menú de hoy"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- agradecimento ---
    if _tem(
        t, "obrigad", "valeu", "brigad", "tks", "thanks", "thank you", "gracias",
    ):
        textos = {
            "pt": (
                "Imagina! 💜 Estou por aqui 24h sempre que precisar. Cuida bem do "
                f"{filho} por mim 😊"
            ),
            "en": (
                "You're welcome! 💜 I'm here 24/7 whenever you need. Take good care of "
                f"{filho} for me 😊"
            ),
            "es": (
                "¡De nada! 💜 Estoy aquí 24h siempre que lo necesites. Cuida bien de "
                f"{filho} por mí 😊"
            ),
        }
        sugestoes = {
            "pt": ["Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
            "en": ["Today's menu", "Any test this week?", "June invoice"],
            "es": ["Menú de hoy", "¿Hay examen esta semana?", "Factura de junio"],
        }
        return {"texto": textos[L], "sugestoes": sugestoes[L]}

    # --- fallback ---
    textos = {
        "pt": (
            "Ainda estou aprendendo 🙂 mas já consigo te ajudar com **faltas**, "
            "**cardápio**, **agenda**, **tarefas** e **financeiro**. No app final, o "
            "que eu não souber eu encaminho direto para a secretaria. Sobre o que "
            "você quer saber?"
        ),
        "en": (
            "I'm still learning 🙂 but I can already help you with **absences**, "
            "**menu**, **calendar**, **homework** and **billing**. In the final app, "
            "whatever I don't know I forward straight to the front office. What would "
            "you like to know?"
        ),
        "es": (
            "Todavía estoy aprendiendo 🙂 pero ya puedo ayudarte con **faltas**, "
            "**menú**, **agenda**, **tareas** y **pagos**. En la app final, lo que no "
            "sepa lo derivo directo a la secretaría. ¿Sobre qué quieres saber?"
        ),
    }
    sugestoes = {
        "pt": [f"O {filho} faltou?", "Cardápio de hoje", "Tem prova essa semana?", "Boleto de junho"],
        "en": [f"Did {filho} miss school?", "Today's menu", "Any test this week?", "June invoice"],
        "es": [f"¿{filho} faltó?", "Menú de hoy", "¿Hay examen esta semana?", "Factura de junio"],
    }
    return {"texto": textos[L], "sugestoes": sugestoes[L]}
