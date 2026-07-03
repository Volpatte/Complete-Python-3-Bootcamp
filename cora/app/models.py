"""Modelos ORM (SQLAlchemy 2.0) — os dados transacionais do Cora.

Dados de referência/analytics de demonstração (engajamento, integrações,
cardápio, frequência, financeiro) seguem em data.py por enquanto; no MVP
completo eles vêm de integrações com o ERP.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Papéis de usuário
COORDENACAO = "coordenacao"
DIRECAO = "direcao"
SECRETARIA = "secretaria"
FINANCEIRO = "financeiro"
PROFESSOR = "professor"
FAMILIA = "familia"

# Papéis administrativos (back-office) — acessam a Gestão da escola.
PAPEIS_ADMIN = (COORDENACAO, DIRECAO, SECRETARIA, FINANCEIRO)
# Todos os papéis de funcionário (não-família).
PAPEIS_STAFF = (COORDENACAO, DIRECAO, SECRETARIA, FINANCEIRO, PROFESSOR)
# Papéis que a Gestão pode criar (ordem de exibição no formulário).
PAPEIS_CRIAVEIS = (PROFESSOR, COORDENACAO, DIRECAO, SECRETARIA, FINANCEIRO, FAMILIA)


class Escola(Base):
    __tablename__ = "escolas"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160))
    cidade: Mapped[str] = mapped_column(String(120), default="")

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="escola")


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[str] = mapped_column(String(20))  # coordenacao | direcao | secretaria | financeiro | professor | familia
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)  # contas desativadas não fazem login

    # Específico do perfil Família
    filho_nome: Mapped[str] = mapped_column(String(120), default="")
    turma: Mapped[str] = mapped_column(String(60), default="")
    idioma: Mapped[str] = mapped_column(String(10), default="pt-BR")
    telefone: Mapped[str] = mapped_column(String(20), default="")
    whatsapp_optin: Mapped[bool] = mapped_column(Boolean, default=False)

    escola: Mapped["Escola"] = relationship(back_populates="usuarios")


class Turma(Base):
    """Turma da escola — gerenciável (nome + professor responsável)."""

    __tablename__ = "turmas"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True)
    nome: Mapped[str] = mapped_column(String(60))
    professor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    professor_nome: Mapped[str] = mapped_column(String(120), default="")  # rótulo exibido
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Aluno(Base):
    """Aluno matriculado — o roster da escola.

    Vincula aluno ↔ turma ↔ responsável (família). Uma família pode ter vários
    alunos (múltiplos filhos); um aluno pode existir sem responsável vinculado
    (ex.: importado antes de a família criar conta).
    """

    __tablename__ = "alunos"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    matricula: Mapped[str] = mapped_column(String(30), default="", index=True)
    turma: Mapped[str] = mapped_column(String(60), default="")
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Comunicado(Base):
    __tablename__ = "comunicados"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    titulo: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str] = mapped_column(String(120))
    turma: Mapped[str] = mapped_column(String(60))
    categoria: Mapped[str] = mapped_column(String(40))
    corpo: Mapped[str] = mapped_column(Text)
    resumo: Mapped[str] = mapped_column(Text, default="")   # resumo de 1 frase (pré-computado pela IA no envio)
    precisa_confirmar: Mapped[bool] = mapped_column(Boolean, default=False)
    enviado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Contadores denormalizados (no produto completo, derivados da tabela Leitura)
    total_familias: Mapped[int] = mapped_column(Integer, default=0)
    leram: Mapped[int] = mapped_column(Integer, default=0)
    confirmaram: Mapped[int] = mapped_column(Integer, default=0)


class Leitura(Base):
    """Estado de leitura/confirmação por usuário — persistência real de verdade."""

    __tablename__ = "leituras"
    id: Mapped[int] = mapped_column(primary_key=True)
    comunicado_id: Mapped[int] = mapped_column(ForeignKey("comunicados.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    lido: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmado: Mapped[bool] = mapped_column(Boolean, default=False)
    lido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Tarefa(Base):
    __tablename__ = "tarefas"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    turma: Mapped[str] = mapped_column(String(60), default="")
    disciplina: Mapped[str] = mapped_column(String(60))
    titulo: Mapped[str] = mapped_column(String(200))
    entrega: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pendente")


class Evento(Base):
    __tablename__ = "eventos"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    data: Mapped[date] = mapped_column(Date)
    titulo: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(40), default="evento")


class Autorizacao(Base):
    """Pedido de autorização (passeio, uso de imagem…). Uma linha por família.

    status: pendente | autorizado | recusado.
    """

    __tablename__ = "autorizacoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True, default=0)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    data_evento: Mapped[date] = mapped_column(Date)
    descricao: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    respondido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Conversa(Base):
    """Fio de conversa entre uma família e um canal da escola (prof/coord/financeiro)."""

    __tablename__ = "conversas"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    familia_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    canal: Mapped[str] = mapped_column(String(80))          # rótulo exibido (ex.: "Prof. Marina")
    staff_papel: Mapped[str] = mapped_column(String(20))    # qual papel atende (professor|coordenacao)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mensagens: Mapped[list["Mensagem"]] = relationship(
        order_by="Mensagem.enviado_em", cascade="all, delete-orphan", back_populates="conversa"
    )


class Mensagem(Base):
    __tablename__ = "mensagens"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversa_id: Mapped[int] = mapped_column(ForeignKey("conversas.id"), index=True)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    autor_nome: Mapped[str] = mapped_column(String(120))
    autor_papel: Mapped[str] = mapped_column(String(20))    # familia | professor | coordenacao
    corpo: Mapped[str] = mapped_column(Text)
    enviado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversa: Mapped["Conversa"] = relationship(back_populates="mensagens")


class EntregaWhatsApp(Base):
    """Registro de uma mensagem espelhada no WhatsApp + seu status de entrega/leitura.

    É o coração do diferencial omnichannel: cada comunicado/mensagem enviado a uma
    família que optou pelo WhatsApp gera uma entrega, com status rastreável
    (enviado → entregue → lido). No modo simulado, o status é controlado na
    Central WhatsApp; no modo real, viria dos webhooks da WhatsApp Business API.
    """

    __tablename__ = "entregas_whatsapp"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    destinatario_nome: Mapped[str] = mapped_column(String(120))
    referencia: Mapped[str] = mapped_column(String(60))   # ex.: "comunicado:3", "mensagem:1"
    resumo: Mapped[str] = mapped_column(String(140))
    status: Mapped[str] = mapped_column(String(20), default="enviado")  # enviado|entregue|lido|falhou
    modo: Mapped[str] = mapped_column(String(12), default="simulado")   # simulado|real
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FichaSaude(Base):
    """Ficha médica do aluno (uma por família)."""

    __tablename__ = "fichas_saude"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True, index=True)
    aluno_nome: Mapped[str] = mapped_column(String(120))
    tipo_sanguineo: Mapped[str] = mapped_column(String(8), default="")
    alergias: Mapped[str] = mapped_column(Text, default="")
    condicoes: Mapped[str] = mapped_column(Text, default="")          # condições crônicas / cuidados especiais
    restricoes: Mapped[str] = mapped_column(Text, default="")         # restrições alimentares
    contato_emergencia: Mapped[str] = mapped_column(String(160), default="")
    convenio: Mapped[str] = mapped_column(String(120), default="")
    observacoes: Mapped[str] = mapped_column(Text, default="")


class Medicacao(Base):
    """Medicação que a escola pode administrar, autorizada pela família."""

    __tablename__ = "medicacoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    aluno_nome: Mapped[str] = mapped_column(String(120))
    nome: Mapped[str] = mapped_column(String(120))
    dosagem: Mapped[str] = mapped_column(String(80), default="")
    horario: Mapped[str] = mapped_column(String(80), default="")       # ex.: "se necessário", "12h"
    instrucoes: Mapped[str] = mapped_column(Text, default="")
    autorizado: Mapped[bool] = mapped_column(Boolean, default=True)    # família autoriza a escola
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    administracoes: Mapped[list["AdministracaoMed"]] = relationship(
        order_by="AdministracaoMed.administrado_em.desc()", cascade="all, delete-orphan",
        back_populates="medicacao",
    )


class AdministracaoMed(Base):
    """Registro de uma administração de medicação feita pela escola."""

    __tablename__ = "administracoes_med"
    id: Mapped[int] = mapped_column(primary_key=True)
    medicacao_id: Mapped[int] = mapped_column(ForeignKey("medicacoes.id"), index=True)
    administrado_por: Mapped[str] = mapped_column(String(120))
    administrado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dose: Mapped[str] = mapped_column(String(80), default="")
    observacao: Mapped[str] = mapped_column(Text, default="")

    medicacao: Mapped["Medicacao"] = relationship(back_populates="administracoes")


class Cobranca(Base):
    """Cobrança financeira (mensalidade, material, evento…) de uma família.

    Valores em centavos (int) para evitar imprecisão de ponto flutuante.
    Status: 'aberto' | 'pago'. 'vencido' é derivado (aberto + vencimento passado).
    """

    __tablename__ = "cobrancas"
    id: Mapped[int] = mapped_column(primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey("escolas.id"), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)  # a família cobrada
    aluno_nome: Mapped[str] = mapped_column(String(120), default="")
    descricao: Mapped[str] = mapped_column(String(160))
    valor_centavos: Mapped[int] = mapped_column(Integer)
    vencimento: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="aberto")  # aberto | pago
    metodo: Mapped[str] = mapped_column(String(20), default="")        # ex.: Pix
    pago_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
