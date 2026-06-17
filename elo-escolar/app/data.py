"""Dados de exemplo (seed) do protótipo Elo Escolar.

Tudo em memória — é um protótipo navegável, não um banco de dados.
A modelagem aqui já antecipa as tabelas reais do MVP (escola, turma,
usuário, comunicado, tarefa, autorização, evento, recibo de leitura).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

HOJE = date(2026, 6, 17)


# --------------------------------------------------------------------------- #
# Escola / turmas / pessoas
# --------------------------------------------------------------------------- #
ESCOLA = {
    "nome": "Colégio Horizonte",
    "cidade": "Florianópolis/SC",
    "alunos": 842,
    "familias": 712,
    "professores": 58,
}

TURMAS = [
    {"id": "5A", "nome": "5º Ano A", "alunos": 28, "professor": "Prof. Marina"},
    {"id": "5B", "nome": "5º Ano B", "alunos": 26, "professor": "Prof. Carlos"},
    {"id": "3A", "nome": "3º Ano A", "alunos": 24, "professor": "Prof. Beatriz"},
    {"id": "INF2", "nome": "Infantil II", "alunos": 18, "professor": "Prof. Lúcia"},
]

# A "família" logada no protótipo (perfil Família)
RESPONSAVEL = {
    "nome": "Juliana Prado",
    "filho": "Pedro Prado",
    "turma": "5º Ano A",
    "idioma": "pt-BR",
}


# --------------------------------------------------------------------------- #
# Comunicados (o coração da comunicação) + recibos de leitura + IA
# --------------------------------------------------------------------------- #
COMUNICADOS = [
    {
        "id": 1,
        "titulo": "Reunião de Pais e Mestres — 5º Ano A",
        "autor": "Coordenação Pedagógica",
        "turma": "5º Ano A",
        "categoria": "reuniao",
        "enviado_em": datetime(2026, 6, 16, 9, 12),
        "corpo": (
            "Prezados responsáveis, convidamos para a reunião de pais e mestres "
            "do 5º Ano A, que acontecerá no dia 24/06 (terça-feira), às 19h, no "
            "auditório principal. Abordaremos o desempenho do trimestre, o "
            "calendário de provas finais e o projeto de leitura. A presença de "
            "ao menos um responsável é fundamental. Pedimos confirmação até 22/06."
        ),
        "precisa_confirmar": True,
        "total_familias": 28,
        "leram": 19,
        "confirmaram": 11,
    },
    {
        "id": 2,
        "titulo": "URGENTE: Alteração no horário de saída amanhã",
        "autor": "Direção",
        "turma": "Toda a escola",
        "categoria": "urgente",
        "enviado_em": datetime(2026, 6, 17, 7, 5),
        "corpo": (
            "Comunicamos que, devido à manutenção emergencial na rede elétrica do "
            "bairro, a saída de amanhã (18/06) será antecipada para as 11h30 para "
            "todos os turnos. O transporte escolar já foi avisado. Caso não possa "
            "buscar seu filho neste horário, responda este comunicado para "
            "organizarmos a permanência supervisionada."
        ),
        "precisa_confirmar": True,
        "total_familias": 712,
        "leram": 488,
        "confirmaram": 402,
    },
    {
        "id": 3,
        "titulo": "Mensalidade de junho disponível",
        "autor": "Financeiro",
        "turma": "Toda a escola",
        "categoria": "financeiro",
        "enviado_em": datetime(2026, 6, 15, 14, 0),
        "corpo": (
            "O boleto da mensalidade de junho já está disponível no portal "
            "financeiro, com vencimento em 20/06. Pagamentos via Pix têm "
            "confirmação imediata. Em caso de dúvida sobre valores ou descontos, "
            "procure a secretaria."
        ),
        "precisa_confirmar": False,
        "total_familias": 712,
        "leram": 534,
        "confirmaram": 0,
    },
    {
        "id": 4,
        "titulo": "Projeto de Ciências: feira de sustentabilidade",
        "autor": "Prof. Marina",
        "turma": "5º Ano A",
        "categoria": "pedagogico",
        "enviado_em": datetime(2026, 6, 14, 16, 30),
        "corpo": (
            "Turma, na próxima semana iniciamos o projeto da feira de "
            "sustentabilidade. Cada grupo deverá trazer materiais recicláveis "
            "para a montagem dos protótipos. A apresentação será no dia 30/06. "
            "Os critérios de avaliação estão no material anexo."
        ),
        "precisa_confirmar": False,
        "total_familias": 28,
        "leram": 22,
        "confirmaram": 0,
    },
]


def comunicado_por_id(cid: int) -> dict | None:
    return next((c for c in COMUNICADOS if c["id"] == cid), None)


# --------------------------------------------------------------------------- #
# Tarefas / lição de casa
# --------------------------------------------------------------------------- #
TAREFAS = [
    {
        "id": 1,
        "disciplina": "Matemática",
        "titulo": "Lista de frações — exercícios 1 a 12",
        "entrega": HOJE + timedelta(days=2),
        "status": "pendente",
    },
    {
        "id": 2,
        "disciplina": "Português",
        "titulo": "Resenha do livro 'O Pequeno Príncipe'",
        "entrega": HOJE + timedelta(days=5),
        "status": "pendente",
    },
    {
        "id": 3,
        "disciplina": "Ciências",
        "titulo": "Trazer materiais recicláveis (projeto feira)",
        "entrega": HOJE + timedelta(days=8),
        "status": "pendente",
    },
    {
        "id": 4,
        "disciplina": "História",
        "titulo": "Questionário sobre Brasil Colônia",
        "entrega": HOJE - timedelta(days=1),
        "status": "entregue",
    },
]


# --------------------------------------------------------------------------- #
# Agenda / eventos
# --------------------------------------------------------------------------- #
EVENTOS = [
    {"data": HOJE + timedelta(days=1), "titulo": "Saída antecipada (11h30)", "tipo": "urgente"},
    {"data": HOJE + timedelta(days=3), "titulo": "Prova de Matemática — frações", "tipo": "prova"},
    {"data": HOJE + timedelta(days=7), "titulo": "Reunião de Pais e Mestres (19h)", "tipo": "reuniao"},
    {"data": HOJE + timedelta(days=13), "titulo": "Feira de Sustentabilidade", "tipo": "evento"},
]


# --------------------------------------------------------------------------- #
# Autorizações digitais
# --------------------------------------------------------------------------- #
AUTORIZACOES = [
    {
        "id": 1,
        "titulo": "Passeio ao Jardim Botânico",
        "data_evento": HOJE + timedelta(days=10),
        "descricao": "Visita guiada com foco no projeto de sustentabilidade. "
        "Saída 8h, retorno 17h. Custo já incluso na mensalidade.",
        "status": "pendente",
    },
    {
        "id": 2,
        "titulo": "Uso de imagem — material institucional",
        "data_evento": HOJE + timedelta(days=20),
        "descricao": "Autorização para uso de fotos das atividades no site e "
        "redes sociais da escola.",
        "status": "autorizado",
    },
]


# --------------------------------------------------------------------------- #
# Analytics de engajamento (diferencial: dados viram decisão)
# --------------------------------------------------------------------------- #
ENGAJAMENTO_POR_TURMA = [
    {"turma": "5º Ano A", "taxa_leitura": 86, "famílias_ativas": 26, "risco": 2},
    {"turma": "5º Ano B", "taxa_leitura": 71, "famílias_ativas": 19, "risco": 7},
    {"turma": "3º Ano A", "taxa_leitura": 64, "famílias_ativas": 16, "risco": 8},
    {"turma": "Infantil II", "taxa_leitura": 93, "famílias_ativas": 17, "risco": 1},
]

# Famílias com baixo engajamento — IA sinaliza quem pode "sumir" / churn
FAMILIAS_RISCO = [
    {"nome": "Família Souza (3º A)", "ultima_leitura": "há 12 dias", "motivo": "Não lê comunicados financeiros"},
    {"nome": "Família Oliveira (5º B)", "ultima_leitura": "há 9 dias", "motivo": "Abriu app 1x no mês"},
    {"nome": "Família Lima (3º A)", "ultima_leitura": "há 8 dias", "motivo": "Não confirmou últimas 3 reuniões"},
]


# --------------------------------------------------------------------------- #
# Integrações (diferencial: virar o hub, não mais um silo)
# --------------------------------------------------------------------------- #
INTEGRACOES = [
    {"nome": "Sponte (ERP escolar)", "categoria": "ERP / Secretaria", "status": "conectado"},
    {"nome": "TOTVS RM", "categoria": "ERP / Financeiro", "status": "conectado"},
    {"nome": "Google Classroom", "categoria": "LMS", "status": "conectado"},
    {"nome": "WhatsApp Business API", "categoria": "Mensageria", "status": "conectado"},
    {"nome": "Pix / Gateway de pagamento", "categoria": "Financeiro", "status": "conectado"},
    {"nome": "Microsoft Teams for Education", "categoria": "LMS", "status": "disponível"},
]
