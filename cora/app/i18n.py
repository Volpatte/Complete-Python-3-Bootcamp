"""Internacionalização (i18n) do Cora — PT (padrão) · EN · ES.

Estratégia: a *string em português é a própria chave* (estilo gettext msgid).
Assim, no idioma padrão (pt) nada precisa de dicionário; para EN/ES basta
mapear o texto-fonte para a tradução. Se uma chave ainda não foi traduzida,
o helper devolve o texto em português (fallback seguro — a tela nunca quebra).

Uso no FastAPI:
    lang = i18n.resolve(request)            # cookie > Accept-Language > 'pt'
    ctx = {"t": i18n.translator(lang), "lang": lang, "langs": i18n.LANGS}
E no template:  {{ t("Entrar") }}
"""
from __future__ import annotations

import json
from pathlib import Path

from starlette.requests import Request

DEFAULT = "pt"
# code -> rótulo curto exibido no seletor
LANGS = {"pt": "PT", "en": "EN", "es": "ES"}
COOKIE = "cora_lang"

# Traduções por idioma, indexadas pela string-fonte em português.
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # ---- topo / navegação ----
        "Entrar": "Sign in",
        "Sair": "Log out",
        "Voltar ao início": "Back to home",
        # ---- landing: hero ----
        "Cuidamos de quem": "We care for those who",
        "protege o nosso futuro": "protect our future",
        "Cora aproxima escola e família com o cuidado no centro. Inteligência que "
        "resume o que importa, dados que viram decisão e a conversa fluindo por onde a família já está.":
            "Cora brings school and family closer, with care at the center. "
            "Intelligence that summarizes what matters, data that turns into decisions, "
            "and the conversation flowing where the family already is.",
        "Ver demonstração": "See the demo",
        # ---- landing: features ----
        "A plataforma do cuidado": "The platform of care",
        "Tudo o que aproxima, em um só lugar": "Everything that brings you closer, in one place",
        "Menos ruído, mais presença. O Cora cuida do que é operacional para a escola "
        "estar por inteiro onde importa: perto das famílias.":
            "Less noise, more presence. Cora handles the operational side so the school "
            "can be fully where it matters: close to families.",
        "Inteligência que cuida": "Intelligence that cares",
        "Resume comunicados, prioriza o urgente e sugere respostas. A família vê primeiro o que não pode esperar.":
            "Summarizes announcements, prioritizes the urgent and suggests replies. "
            "Families see first what can't wait.",
        "Decisões com clareza": "Decisions with clarity",
        "Engajamento por turma e um radar das famílias que precisam de atenção — em tempo real.":
            "Engagement by class and a radar of families who need attention — in real time.",
        "Onde a família já está": "Where the family already is",
        "A comunicação chega também no WhatsApp, com entrega e leitura rastreáveis, sem app a mais para baixar.":
            "Communication also reaches WhatsApp, with trackable delivery and read receipts, "
            "no extra app to download.",
        "Conecta a escola inteira": "Connects the whole school",
        "Integra os sistemas que a secretaria já usa — acadêmico, financeiro e pedagógico — sem retrabalho.":
            "Integrates the systems the office already uses — academic, financial and pedagogical — with no rework.",
        # ---- landing: perfis ----
        "Experimente agora": "Try it now",
        "Escolha por onde entrar": "Choose where to start",
        "Uma demonstração navegável, com dados de exemplo. Entre em qualquer perfil e sinta como o Cora funciona.":
            "A clickable demo with sample data. Enter any profile and feel how Cora works.",
        "Coordenação / Direção": "Coordination / Management",
        "Panorama de engajamento, sinais de risco e o pulso da escola — reunidos em um só lugar.":
            "Engagement overview, risk signals and the pulse of the school — all in one place.",
        "Professor": "Teacher",
        "Escreva um comunicado e veja a inteligência resumir, priorizar e traduzir antes de enviar.":
            "Write an announcement and watch the intelligence summarize, prioritize and translate before sending.",
        "Família": "Family",
        "O feed do que importa, agenda, tarefas e um assistente que responde 24h — sem perder nada.":
            "The feed of what matters, calendar, tasks and an assistant that answers 24/7 — without missing a thing.",
        "Abrir painel": "Open dashboard",
        "Abrir app": "Open app",
        "Prefere entrar manualmente?": "Prefer to sign in manually?",
        "Use a tela de login": "Use the login screen",
        "senha de demonstração": "demo password",
        # ---- landing: KPIs / rodapé ----
        "alunos": "students",
        "famílias": "families",
        "professores": "teachers",
        "unidade": "campus",
        "ambiente de demonstração": "demo environment",
        "Cuidamos de quem protege o nosso futuro.": "We care for those who protect our future.",
        "perto de quem você ama": "close to those you love",
        # ---- login ----
        "Bem-vindo de volta": "Welcome back",
        "Entre para acompanhar a escola de quem você ama.": "Sign in to follow the school of those you love.",
        "E-mail": "Email",
        "Senha": "Password",
        "E-mail ou senha incorretos. Tente novamente.": "Incorrect email or password. Please try again.",
        "Acesso rápido para demonstração (senha:": "Quick demo access (password:",
        "Coordenação": "Coordination",
        # ---- navegação / shells (base + app_shell) ----
        "Mensagens": "Messages",
        "Saúde": "Health",
        "Início": "Home",
        "Agenda": "Calendar",
        "Falar com a Cora IA": "Talk to Cora AI",
        "Instalar o app Cora": "Install the Cora app",
    },
    "es": {
        # ---- topo / navegação ----
        "Entrar": "Entrar",
        "Sair": "Salir",
        "Voltar ao início": "Volver al inicio",
        # ---- landing: hero ----
        "Cuidamos de quem": "Cuidamos de quien",
        "protege o nosso futuro": "protege nuestro futuro",
        "Cora aproxima escola e família com o cuidado no centro. Inteligência que "
        "resume o que importa, dados que viram decisão e a conversa fluindo por onde a família já está.":
            "Cora acerca la escuela y la familia, con el cuidado en el centro. "
            "Inteligencia que resume lo que importa, datos que se vuelven decisión "
            "y la conversación fluyendo por donde la familia ya está.",
        "Ver demonstração": "Ver demostración",
        # ---- landing: features ----
        "A plataforma do cuidado": "La plataforma del cuidado",
        "Tudo o que aproxima, em um só lugar": "Todo lo que acerca, en un solo lugar",
        "Menos ruído, mais presença. O Cora cuida do que é operacional para a escola "
        "estar por inteiro onde importa: perto das famílias.":
            "Menos ruido, más presencia. Cora se encarga de lo operativo para que la escuela "
            "esté por completo donde importa: cerca de las familias.",
        "Inteligência que cuida": "Inteligencia que cuida",
        "Resume comunicados, prioriza o urgente e sugere respostas. A família vê primeiro o que não pode esperar.":
            "Resume los comunicados, prioriza lo urgente y sugiere respuestas. "
            "La familia ve primero lo que no puede esperar.",
        "Decisões com clareza": "Decisiones con claridad",
        "Engajamento por turma e um radar das famílias que precisam de atenção — em tempo real.":
            "Participación por grupo y un radar de las familias que necesitan atención — en tiempo real.",
        "Onde a família já está": "Donde la familia ya está",
        "A comunicação chega também no WhatsApp, com entrega e leitura rastreáveis, sem app a mais para baixar.":
            "La comunicación llega también por WhatsApp, con entrega y lectura rastreables, "
            "sin una app más que descargar.",
        "Conecta a escola inteira": "Conecta toda la escuela",
        "Integra os sistemas que a secretaria já usa — acadêmico, financeiro e pedagógico — sem retrabalho.":
            "Integra los sistemas que la secretaría ya usa — académico, financiero y pedagógico — sin retrabajo.",
        # ---- landing: perfis ----
        "Experimente agora": "Pruébalo ahora",
        "Escolha por onde entrar": "Elige por dónde entrar",
        "Uma demonstração navegável, com dados de exemplo. Entre em qualquer perfil e sinta como o Cora funciona.":
            "Una demostración navegable, con datos de ejemplo. Entra en cualquier perfil y siente cómo funciona Cora.",
        "Coordenação / Direção": "Coordinación / Dirección",
        "Panorama de engajamento, sinais de risco e o pulso da escola — reunidos em um só lugar.":
            "Panorama de participación, señales de riesgo y el pulso de la escuela — reunidos en un solo lugar.",
        "Professor": "Profesor",
        "Escreva um comunicado e veja a inteligência resumir, priorizar e traduzir antes de enviar.":
            "Escribe un comunicado y observa cómo la inteligencia resume, prioriza y traduce antes de enviar.",
        "Família": "Familia",
        "O feed do que importa, agenda, tarefas e um assistente que responde 24h — sem perder nada.":
            "El feed de lo que importa, agenda, tareas y un asistente que responde 24h — sin perderte nada.",
        "Abrir painel": "Abrir panel",
        "Abrir app": "Abrir app",
        "Prefere entrar manualmente?": "¿Prefieres entrar manualmente?",
        "Use a tela de login": "Usa la pantalla de acceso",
        "senha de demonstração": "contraseña de demostración",
        # ---- landing: KPIs / rodapé ----
        "alunos": "alumnos",
        "famílias": "familias",
        "professores": "profesores",
        "unidade": "sede",
        "ambiente de demonstração": "entorno de demostración",
        "Cuidamos de quem protege o nosso futuro.": "Cuidamos de quien protege nuestro futuro.",
        "perto de quem você ama": "cerca de quien amas",
        # ---- login ----
        "Bem-vindo de volta": "Bienvenido de vuelta",
        "Entre para acompanhar a escola de quem você ama.": "Entra para seguir la escuela de quien amas.",
        "E-mail": "Correo",
        "Senha": "Contraseña",
        "E-mail ou senha incorretos. Tente novamente.": "Correo o contraseña incorrectos. Inténtalo de nuevo.",
        "Acesso rápido para demonstração (senha:": "Acceso rápido de demostración (contraseña:",
        "Coordenação": "Coordinación",
        # ---- navegação / shells (base + app_shell) ----
        "Mensagens": "Mensajes",
        "Saúde": "Salud",
        "Início": "Inicio",
        "Agenda": "Agenda",
        "Falar com a Cora IA": "Hablar con Cora IA",
        "Instalar o app Cora": "Instalar la app Cora",
    },
}


# Mescla as traduções das telas internas (geradas em app/translations.json).
# Mantém as chaves inline acima como base; o JSON complementa/atualiza.
_JSON_PATH = Path(__file__).resolve().parent / "translations.json"
try:
    _extra = json.loads(_JSON_PATH.read_text(encoding="utf-8"))
    for _lang, _table in _extra.items():
        TRANSLATIONS.setdefault(_lang, {}).update(_table)
except FileNotFoundError:
    pass


def normalize(code: str | None) -> str:
    """Reduz 'pt-BR' -> 'pt' e valida contra os idiomas suportados."""
    if not code:
        return DEFAULT
    code = code.strip().lower().split("-")[0]
    return code if code in LANGS else DEFAULT


def detect(accept_language: str | None) -> str:
    """Escolhe o melhor idioma a partir do header Accept-Language."""
    if not accept_language:
        return DEFAULT
    for part in accept_language.split(","):
        code = normalize(part.split(";")[0])
        if code in LANGS and code != DEFAULT:
            return code
        if code == DEFAULT:
            return DEFAULT
    return DEFAULT


def resolve(request: Request) -> str:
    """Idioma efetivo: cookie salvo > Accept-Language > padrão."""
    cookie = request.cookies.get(COOKIE)
    if cookie:
        return normalize(cookie)
    return detect(request.headers.get("accept-language"))


def translator(lang: str):
    """Retorna a função t(texto) para o idioma dado."""
    table = TRANSLATIONS.get(lang, {})

    def t(text: str) -> str:
        if lang == DEFAULT:
            return text
        return table.get(text, text)

    return t


def tr(text: str, lang: str) -> str:
    """Tradução pontual no lado do servidor (fora de template)."""
    if lang == DEFAULT:
        return text
    return TRANSLATIONS.get(lang, {}).get(text, text)


# Nome do idioma por extenso (para instruir o LLM a responder no idioma certo).
NOME_IDIOMA = {"pt": "português do Brasil", "en": "English", "es": "español"}
