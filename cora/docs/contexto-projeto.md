# Cora — Contexto Completo do Projeto

> **Documento de transferência.** Reúne tudo que outra IA (ou pessoa) precisa para
> continuar o desenvolvimento do Cora sem depender do histórico da conversa original.
> Atualizado em: 2026-08-20.

---

## 1. O que é o Cora

**Cora** é uma plataforma **escola ↔ família** — um app onde a escola se comunica com
os pais, cobra mensalidades, pede autorizações e gerencia o dia a dia; e onde a família
acompanha os filhos, paga, autoriza e conversa. Tudo com **IA nativa** e **trilíngue
(PT/EN/ES)**.

- **Tagline:** *"Cuidamos de quem protege o nosso futuro."*
- **Identidade visual:** gradiente coral → rosa → violeta (`#ff6a86 → #e21e79 → #8b5cf6`),
  cantos arredondados, emoji como ícones, tom acolhedor e humano.
- **Estado:** protótipo navegável funcional com dados de exemplo (seed), 96 testes passando.
- **Repositório:** `Volpatte/Complete-Python-3-Bootcamp`, o app vive na pasta `cora/`.
  (O repo era um fork do curso de Python; o Cora foi construído dentro dele.)

---

## 2. Stack e arquitetura

| Camada | Escolha |
|---|---|
| Backend | **FastAPI** (Python 3.12) |
| Templates | **Jinja2** (server-side rendering, sem SPA) |
| ORM / DB | **SQLAlchemy 2.x** + SQLite (arquivo `cora.db`, recriado pelo seed) |
| Sessão | Cookie assinado via `itsdangerous` (`CORA_SECRET_KEY`) |
| IA | SDK `anthropic` — **degrada graciosamente** para respostas mock se não houver `ANTHROPIC_API_KEY` |
| Frontend | CSS artesanal (`style.css` para desktop/staff, `app.css` para o app mobile da família), zero framework JS |
| PWA | `manifest.webmanifest` + `sw.js` + `offline.html` (instalável) |
| Testes | **pytest** + `fastapi.testclient` |
| Deploy | **Render** via `render.yaml` (blueprint na raiz do repo) |

**Princípio central:** simplicidade. Sem build step, sem node_modules, sem migrations
(o schema nasce do `models.py` e o `seed.py` popula tudo). Rodar é `uvicorn app.main:app`.

### Arquivos principais

```
cora/
├── app/
│   ├── main.py          # TODAS as rotas + helpers (~1.380 linhas) — o coração
│   ├── models.py        # 17 modelos SQLAlchemy
│   ├── seed.py          # cria o banco e popula dados de demonstração
│   ├── data.py          # constantes/dados-fonte do seed (comunicados, tarefas…)
│   ├── db.py            # engine, SessionLocal, get_db
│   ├── security.py      # hash de senha, sessão
│   ├── i18n.py          # tradução PT/EN/ES
│   ├── translations.json# 362 chaves EN/ES
│   ├── ai.py, llm.py, assistant.py, analytics.py, whatsapp.py
│   ├── static/          # style.css, app.css, sw.js, manifest, ícones
│   └── templates/       # 25 templates Jinja
├── tests/               # 13 arquivos, 96 testes
├── docs/                # deploy.md, roteiro-de-teste.md, pesquisa-mercado.md, este arquivo
├── requirements.txt
└── run.sh
```

---

## 3. Papéis e permissões

```python
COORDENACAO = "coordenacao";  DIRECAO = "direcao";  SECRETARIA = "secretaria"
FINANCEIRO  = "financeiro";   PROFESSOR = "professor";  FAMILIA = "familia"

PAPEIS_ADMIN = (COORDENACAO, DIRECAO, SECRETARIA, FINANCEIRO)   # acessam /admin
PAPEIS_STAFF = (COORDENACAO, DIRECAO, SECRETARIA, FINANCEIRO, PROFESSOR)
```

Controle de acesso via dependência `exigir(*papeis)` — redireciona para a home do papel
se não autorizado (staff → `/coordenacao`, família → `/familia`).

**Regra de ouro de segurança (aplicada em todas as queries):** escopo por `escola_id`
+ verificação de propriedade (`registro.usuario_id == user.id`) antes de qualquer mutação.

### Logins de demonstração (senha: `cora123`)

| E-mail | Papel |
|---|---|
| `familia@cora.app` | Família (Juliana, mãe de Pedro e Laura) |
| `prof@cora.app` | Professor (Prof. Marina) |
| `coord@cora.app` | Coordenação (Ana Coordenação) |
| `dir@cora.app` | Direção (Roberto Diretor) |
| `sec@cora.app` | Secretaria (Carla Secretaria) |
| `fin@cora.app` | Financeiro (Marcos Financeiro) |
| +8 famílias extras | `souza@`, `lima@`, `rocha@`, `dias@`, `castro@`, `mendes@`, `oliveira@`, `pires@` |

Atalho de demo sem digitar senha: `GET /login/demo/{papel}`.

---

## 4. Modelo de dados (17 tabelas)

| Modelo | Papel no sistema |
|---|---|
| `Escola` | multi-tenant: tudo tem `escola_id` |
| `Usuario` | papel, nome, email, senha_hash, turma, ativo, escola_id |
| `Turma`, `Aluno` | alunos têm `responsavel_id` → Usuario(familia) |
| `Comunicado`, `Leitura` | comunicados por turma/escola + rastreio de leitura |
| `Tarefa`, `Evento` | lição de casa e agenda |
| `Autorizacao` | pedidos de autorização (status: pendente/autorizado/recusado) |
| `Conversa`, `Mensagem` | chat **família ↔ staff** |
| `MensagemStaff` | DM **staff ↔ staff** (de_id, para_id, lido) |
| `Cobranca` | financeiro — **valores em centavos** (`valor_centavos`) |
| `EntregaWhatsApp` | simulação de entrega/leitura via WhatsApp |
| `FichaSaude`, `Medicacao`, `AdministracaoMed` | módulo de saúde |

**Convenção importante:** dinheiro sempre em **centavos** (`int`), nunca float.
Exibição via filtro Jinja `|reais`. Parsing de entrada via `_centavos()` que entende
`R$ 1.480,00`, `1.480`, `1480.00`, `50`.

---

## 5. Rotas (55)

### Autenticação e comuns
`/` (landing) · `/login` (GET/POST) · `/login/demo/{papel}` · `/logout` ·
`/lang/{code}` · `/health` · `/sw.js`

### Família (app mobile)
| Rota | O quê |
|---|---|
| `GET /familia` | feed/home do app |
| `GET /familia/comunicado/{cid}` | comunicado + marca leitura |
| `GET /familia/agenda`, `/familia/loja` | agenda e loja |
| `GET/POST /familia/saude*` | ficha de saúde e medicação |
| `GET /familia/mensagens`, `/{cid}`, `POST /{cid}/enviar` | chat com a escola |
| `GET /familia/financeiro` · `POST /familia/financeiro/{cid}/pagar` | faturas + Pix |
| `POST /familia/autorizacao/{aid}/responder` | autorizar/recusar |
| `GET /familia/notificacoes` | central de notificações |
| `GET /familia/assistente` · `POST /api/assistente` | assistente IA 24/7 |
| `POST /familia/whatsapp/ativar` | ativa canal WhatsApp |

### Staff
| Rota | Papéis | O quê |
|---|---|---|
| `GET /coordenacao` | staff | painel com analytics, engajamento, radar de risco |
| `GET /professor` + `POST /professor/{tarefa,evento,preview,enviar}` | professor | comunicados com IA, tarefas, eventos |
| `GET /admin` + `POST /admin/*` | PAPEIS_ADMIN | CRUD funcionários/alunos/turmas + importação CSV |
| `GET/POST /financeiro`, `/financeiro/cobranca` | financeiro, coord, direção | KPIs + lançar cobrança |
| `GET/POST /autorizacoes` | professor, coordenação | solicitar + acompanhar respostas |
| `GET /equipe`, `/equipe/{cid}`, `POST /equipe/{cid}/enviar` | PAPEIS_STAFF | mensagens internas |
| `GET /notificacoes` | PAPEIS_STAFF | central de notificações |
| `GET /mensagens`, `/{cid}`, `POST /{cid}/enviar` | professor, coord | chat com famílias |
| `GET /whatsapp` + `POST /whatsapp/simular-leitura` | coordenação | painel WhatsApp |
| `GET /saude` + `POST /saude/administrar/{id}` | coordenação | enfermaria |

---

## 6. Funcionalidades implementadas

### Comunicação
- **Comunicados com IA**: professor escreve → IA gera resumo, sugere tom, classifica urgência.
- **Rastreio de leitura** por família, com taxa por turma.
- **WhatsApp**: canal simulado com entrega/leitura rastreável.
- **Chat família ↔ staff** e **chat staff ↔ staff** (`/equipe`).

### Financeiro (`Cobranca`)
- Painel da escola: KPIs **a receber / recebido / vencido**; lançar cobrança para uma
  **família** ou **turma inteira** (broadcast, 1 por responsável, deduplicado).
- Família: saldo em aberto + **"Pagar via Pix"** (idempotente — não repaga).
- Status `vencido` é **derivado** da data de vencimento, não armazenado.

### Autorizações (`Autorizacao`)
- Família: **Autorizar / Recusar** persistidos, com `respondido_em`; pode trocar a escolha.
- Staff: solicitar por **turma** ou **toda a escola**; acompanhar por evento com barra de
  progresso e contagem autorizado/recusado/pendente.

### Central de notificações
- **Sino com contador** global (injetado no contexto via `notif_count`), no topo do staff
  e no header do app da família.
- Agrega **ao vivo, sem estado próprio** (`_notificacoes(db, user)`):
  - Família → comunicados não lidos + faturas em aberto + autorizações pendentes.
  - Staff → mensagens da equipe não lidas (agrupadas por remetente).
- Cada item linka para a tela de origem e **desaparece ao agir**.

### Outros módulos
- **Analytics** (`/coordenacao`): engajamento por turma, radar de famílias em risco, insight de IA.
- **Gestão** (`/admin`): funcionários, alunos, turmas, reset de senha, ativar/desativar,
  **importação CSV**.
- **Saúde**: ficha, medicações autorizadas, registro de administração pela enfermaria.
- **Assistente IA**: responde sobre faltas, cardápio, agenda, financeiro.
- **PWA**: instalável, com página offline.

---

## 7. Convenções de código (siga-as)

1. **Idioma**: todo código, comentários, commits e UI em **português**. Nomes de
   variáveis/rotas em português (`cobranca`, `autorizacoes`, `_colegas`).
2. **i18n**: a string em **PT é a própria chave** (estilo gettext). Nos templates:
   `{{ t("Autorizar") }}`. Traduções EN/ES em `app/translations.json`. Se faltar
   tradução, cai no PT (nunca quebra). **Toda string nova na UI precisa passar por `t()`
   e ganhar entrada em EN e ES.**
3. **Contexto de template**: use sempre o helper `_ctx(request, user, active=..., **extra)`
   — ele injeta `t`, `lang`, `langs`, `is_admin`, `is_staff`, `pode_financeiro`, `notif_count`.
4. **Segurança**: escopo por `escola_id` em toda query; cheque propriedade antes de mutar;
   use `exigir(*papeis)` na assinatura da rota.
5. **Dinheiro**: centavos (int). Nunca float.
6. **POST → RedirectResponse(303)** (padrão POST-Redirect-GET), com `?msg=...` para feedback.
7. **Estilo visual**: sem framework CSS; classes existentes (`card`, `pill`, `btn`,
   `section-title`, `muted small`, `grid cols-2`, `it`, `post`) — reutilize-as.
   O app da família estende `app_shell.html`; telas de staff estendem `base.html`.
8. **Testes**: um arquivo por feature em `tests/`, usando as fixtures de `conftest.py`
   (`familia`, `professor`, `coord`, `admin`…). Cada feature nova deve incluir teste de
   **controle de acesso** e de **IDOR**.

---

## 8. Testes

```bash
cd cora && python3 -m pytest        # 96 passed
```

Arquivos: `test_auth`, `test_admin`, `test_analytics`, `test_assistente`,
`test_autorizacoes`, `test_comunicados`, `test_equipe`, `test_financeiro`,
`test_mensagens`, `test_misc`, `test_notificacoes`, `test_saude`, `test_whatsapp`.

---

## 9. Como rodar

```bash
cd cora
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000
# ou: ./run.sh
```

O banco `cora.db` é criado e populado automaticamente no primeiro boot.
Para resetar os dados: `rm cora.db` e suba de novo.

Variáveis de ambiente (todas opcionais):
- `ANTHROPIC_API_KEY` — liga a IA real (sem ela, respostas mock coerentes).
- `CORA_SECRET_KEY` — chave de sessão (gerada no Render).
- `WHATSAPP_TOKEN` — WhatsApp real.

---

## 10. Estado do Git / PR / Deploy

- **Branch de trabalho:** `claude/agenda-edu-app-cfgzxq` (todo desenvolvimento vai nela).
- **Base:** `master`.
- **PR aberto:** [#2 — "Novas features: Financeiro, Autorizações, Mensagens da equipe e
  Central de notificações"](https://github.com/Volpatte/Complete-Python-3-Bootcamp/pull/2),
  com 4 commits:
  1. `eb67362` Portal Financeiro
  2. `3090f34` Autorizações reais
  3. `0f1e0d4` Mensagens da equipe
  4. `65eb087` Central de notificações
- **PR anterior (#1) já foi mergeado** — trazia o app base (comunicados, IA, analytics,
  WhatsApp, saúde, gestão, PWA, i18n).
- **Deploy:** Render, blueprint `render.yaml` na raiz. Hoje o deploy segue a **branch de
  feature** (features entram no ar antes do merge). URL: `https://cora-7hdj.onrender.com`
  (plano free — o primeiro acesso demora ~30s pra "acordar").

---

## 11. Histórico de decisões relevantes

- **Sem migrations**: o schema vem do `models.py`; ao adicionar coluna, basta apagar o
  `cora.db` local. Em produção o Render recria o banco a cada deploy (é protótipo).
- **`Autorizacao` ganhou `escola_id` e `respondido_em`** para permitir o painel do staff.
- **`MensagemStaff` é um modelo separado** de `Conversa`/`Mensagem` (que servem
  família↔staff) — decisão consciente para não entrelaçar os dois fluxos.
- **Notificações não têm tabela**: são agregadas ao vivo. Isso evita sincronização de
  estado e faz o item sumir naturalmente quando a ação é feita.
- **Broadcast sempre deduplica por responsável** (uma família com 2 filhos na turma
  recebe 1 cobrança/autorização, não 2).
- **Parser de moeda**: `"1.480"` é 1480 reais (separador de milhar BR), mas `"10.50"`
  é 10,50 — heurística: ponto seguido de exatamente 3 dígitos = milhar.

---

## 12. Backlog sugerido (próximos passos)

1. **Recibos / 2ª via** e histórico de pagamentos no financeiro.
2. **Evento + autorização juntos** — criar evento na agenda já disparando o pedido.
3. **Notificações push/e-mail reais** (hoje a central é in-app).
4. **Mesclar o PR #2** e apontar o deploy para o `master`.
5. Relatórios exportáveis (PDF/CSV) de inadimplência e engajamento.
6. Multi-escola de verdade (hoje o seed cria uma escola só, mas o schema já suporta).

---

## 13. Materiais de apresentação

- **Mockup/showcase compartilhável** (página com as telas reais do app):
  publicado como Artifact — *"Cora"* — com hero, features, galeria de telas mobile,
  painéis em molduras de navegador e CTA para o app ao vivo.
- Outros docs: `cora/docs/deploy.md` (como publicar), `cora/docs/roteiro-de-teste.md`
  (passo a passo de demonstração), `cora/docs/pesquisa-mercado.md` (concorrentes e
  posicionamento).

---

## 14. Prompt sugerido para outra IA

> Você vai continuar o desenvolvimento do **Cora**, uma plataforma escola↔família em
> FastAPI + Jinja2 + SQLAlchemy (SQLite), trilíngue PT/EN/ES, descrita no documento
> anexo (`cora/docs/contexto-projeto.md`). O código está em `cora/`. Leia o documento
> inteiro antes de agir, siga as **convenções da seção 7** (código e UI em português,
> toda string via `t()` com tradução EN/ES, escopo por `escola_id`, dinheiro em centavos,
> POST→303), e mantenha a suíte de testes verde (`python3 -m pytest`, hoje 96 passando).
> Desenvolva na branch `claude/agenda-edu-app-cfgzxq`. Minha próxima tarefa é: **[descreva]**.
