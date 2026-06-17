# Pesquisa de mercado — comunicação escola-família no Brasil

> Insumo para priorização de roadmap do **Cora**.
> Pesquisa multi-fonte (jun/2026). Confiança indicada por afirmação.
> Premissas iniciais corrigidas estão sinalizadas com ⚠️.

---

## TL;DR — as 4 brechas reais

1. **WhatsApp como canal de primeira classe.** Todos os incumbentes tratam o WhatsApp como *rival a ser substituído* — não como canal nativo de entrega. É a maior dor estrutural (pai ignora o app, abre o WhatsApp).
2. **IA voltada à FAMÍLIA, não só ao professor.** A IA da Agenda Edu já existe, mas serve o educador (escrever/revisar comunicado). Ninguém oferece assistente que responda os pais 24/7 ("meu filho faltou?", cardápio, financeiro).
3. **Analytics preditivo de engajamento/churn.** Os incumbentes param na "taxa de leitura". Previsão de família desengajada / risco de evasão só existe na academia — não embarcada em produto.
4. **Hub de integração bidirecional acionável.** As integrações atuais são "espelho" de cadastro (unidirecional). Falta orquestração com fluxos acionáveis (ex.: inadimplência → comunicação automática).

⚠️ **Risco-chave:** a Agenda Edu já se vende como "SuperApp" com IA + 20 integrações + WhatsApp. **Nenhuma peça isolada é diferencial** — a defensabilidade está na *combinação* (WhatsApp-first + IA para a família + analytics de churn) e na execução/UX.

---

## 1. Os incumbentes

### Agenda Edu
- **Dono:** ⚠️ **Bemobi (BMOB3)** desde dez/2023 (caminho: fundada em Fortaleza/2014 → Eleva/Grupo Salta → Bemobi). **Não é da Arco.** (alta) — [Brazil Journal](https://braziljournal.com/bemobi-compra-empresa-de-ex-eleva-e-estreia-em-educacao/), [SpaceMoney](https://www.spacemoney.com.br/geral/bemobi-bmob3-compra-agenda-edu-empresa-de-ex-eleva/200359/)
- **Escala:** +2.500 instituições / ~2–2,5 mi usuários (números variam por fonte). (média)
- **Módulos:** Atividades, Comunicados (c/ assinatura digital de leitura), Mensagens, Eventos, Cardápio, Mural, Diário, Saúde e **Pagamentos (EduPay** — Pix/boleto/cartão, cobrança recorrente, alega "−85% inadimplência"*). (alta; *número promocional, não auditado) — [agendaedu.com/pagamentos-digitais](https://www.agendaedu.com/pagamentos-digitais)
- **IA:** ✅ **"Agenda Edu IA"** — gera/revisa comunicados, atividades e eventos; aprende o tom da escola. Foco em **produtividade do educador**, não chatbot para família nem analytics preditivo. (alta) — [agendaedu.com/ia](https://www.agendaedu.com/ia)
- **WhatsApp:** integração de atendimento multicanal (captação/atendimento), com histórico. (média/alta)
- **Integrações:** alega **20+** com ERPs — TOTVS, SophiA, Sponte, Qi Solution (cadastros, catracas, notas). Padrão "espelho" via API. (média/alta)

### ClassApp
- **Dono:** ⚠️ incorporada à **isaac** (+ Activesoft), hoje dentro do **ecossistema Arco Educação**; produtos unificados com **Escola em Movimento**. Sede no interior de SP (Limeira/Campinas), não Ribeirão Preto. (alta) — [classapp.com.br/quem-somos](https://www.classapp.com.br/quem-somos), [Startupi: Arco adquire isaac](https://startupi.com.br/arco-educacao-adquire-isaac/)
- **Escala:** ~2 mi usuários / +2.400 escolas (recente). (média-alta)
- **Módulos:** Mensagens c/ controle de leitura, Comunicados, Momentos (mídia), Agenda, Autorizações, Enquetes, **Financeiro/ClassPay** (módulo pago à parte). (alta)
- **IA:** moderação/melhoria de texto em comunicados (~2025). Sem chatbot para família. (média-alta)
- **WhatsApp:** posiciona-se como **substituto** do WhatsApp; ⚠️ integração nativa *com* o WhatsApp como canal de envio **não confirmada**. (média)
- **Integrações:** "+10" com ERPs (Sponte, Activesoft, Superlógica, Eskolare, isaac). **Sem LMS** (Google Classroom/Moodle) encontrado. (alta)

### Modelo comercial (ambos)
- **B2B**, pago pela escola, **gratuito para a família**. Preço por aluno/mês. ⚠️ **Preço não é público** em nenhum dos dois — só por contato comercial. Faixas em matérias antigas: Agenda Edu ~R$1,25–5/aluno/mês; ClassApp citado "R$900 adesão + R$1/aluno/mês" (provavelmente desatualizado). (baixa)

---

## 2. Reclamações reais (onde dói)

> Volume formal no Reclame Aqui é **baixo** (B2B — quem contrata é a escola). O sinal mais rico está nas **avaliações das lojas** e em conteúdo de setor. Notas agregadas são altas (Agenda Edu ~4,2 Play / ~4,8 App Store; ClassApp ~4,8), mas os comentários revelam padrões.

**Agenda Edu:**
- 💰 **Boletos/pagamento** — boleto não aparece, pago aparece "em atraso", cobrança duplicada. *Tema nº 1.* (frequente)
- 🆘 **Suporte lento/inexistente** — só chat, esperas longas. (frequente)
- 🐛 **App trava/não abre** — congela com múltiplas fotos, precisa limpar cache. Como é canal único, falha = comunicação cortada. (frequente)
- 📅 Atualizações em hora ruim deixando pais sem acesso. (ocasional)

**ClassApp:**
- 💬 **Chat de uma via** — não dá para mandar nova mensagem antes da resposta. *Limitação de UX muito citada.* (frequente)
- 🔔 **Notificações não chegam** — recorrente o bastante para ter vários artigos de ajuda. (ocasional)
- 🐛 Bug de cadastro/primeiro acesso e tela branca no iOS. (ocasional)

**Transversal (todo o segmento):**
- 📲 **"Mais um app obrigatório"** — ambos forçam o pai a instalar/monitorar um app em vez do canal que ele já usa (WhatsApp). Vendido como benefício à escola, é **dor para a família**.

Fontes: [RA Agenda Edu](https://www.reclameaqui.com.br/empresa/agenda-edu/lista-reclamacoes/), [App Store ClassApp](https://apps.apple.com/br/app/classapp/id918086112), [Ajuda ClassApp – notificações](https://ajuda.classapp.com.br/hc/pt-br/articles/360006093374).

---

## 3. Mercado e contexto

- **Brasil:** 47,1 mi de matrículas em 179,3 mil escolas (Censo 2024); **rede privada com 9,5 mi de alunos (~20%), crescendo** enquanto a pública encolhe — é o segmento pagante e o alvo natural. (alta) — [FENEP](https://www.fenep.org.br/rede-privada-consolida-recuperacao-apos-crise-sanitaria-e-ja-supera-95-milhoes-de-alunos/), [INEP](https://download.inep.gov.br/censo_escolar/resultados/2024/apresentacao_coletiva.pdf)
- **WhatsApp:** ~99% dos smartphones; 81% já falaram com empresas pelo app; **89% já interagiram com bot de marca, mas 37% ficaram insatisfeitos** → demanda por automação *boa*. (alta) — [Mobile Time/Opinion Box](https://www.mobiletime.com.br/pesquisas/mensageria-no-brasil-marco-de-2024/)
- **Consenso de setor:** "os pais já escolheram o WhatsApp; lutar contra isso é lutar contra o comportamento humano". Recomenda-se **dual: app = registro oficial + WhatsApp = entrega rápida**. (alta)
- **Mercado fragmentado por função** + **consolidação em curso** (Arco+isaac+ClassApp; Cogna/Vasta+Eleva) rumo a "super-app"/"banco das escolas". (média-alta)
- **Evasão** é dor real (Ensino Médio 5,9%, Censo 2023); previsão preditiva existe só na academia. (alta)

---

## 4. Tradução em roadmap (priorização)

Notação: **Impacto** (dor que resolve) × **Diferenciação** (vs. incumbente) × **Esforço**.

### 🟢 NOW — fundação + cunha (0–4 meses)
| Item | Por quê | Dif. |
|---|---|---|
| **Núcleo de comunicação sólido** (comunicados, mensagens *bidirecionais de verdade*, leitura, agenda, autorizações) | Paridade obrigatória + corrige o "chat de uma via" do ClassApp | média |
| **WhatsApp-first como canal nativo** (entrega via WhatsApp Business API + confirmação de leitura + LGPD resolvida; app como sistema de registro) | **Brecha nº 1.** Ataca a dor "mais um app" de frente | **alta** |
| **Confiabilidade brutal** (notificações que chegam, app que não trava) | As duas maiores reclamações operacionais dos incumbentes | média |

### 🟡 NEXT — diferenciais de IA e dados (4–9 meses)
| Item | Por quê | Dif. |
|---|---|---|
| **Assistente de IA para a família no WhatsApp** (responde faltas, cardápio, agenda, financeiro 24/7) | **Brecha nº 2.** Ninguém faz; 37% odeiam os bots atuais | **alta** |
| **IA para o educador** (resumo/priorização/tradução — já no protótipo) | Paridade com Agenda Edu IA; multi-idioma é plus | baixa-média |
| **Analytics de engajamento + radar de churn** (prevê família desengajada/risco de evasão) | **Brecha nº 3.** Só existe na academia | **alta** |

### 🔵 LATER — hub e monetização (9+ meses)
| Item | Por quê | Dif. |
|---|---|---|
| **Hub de integração bidirecional acionável** (ERP Sponte/TOTVS + Google Classroom + financeiro, com fluxos: inadimplência→comunicação) | **Brecha nº 4.** Integração atual é só "espelho" | média |
| **Financeiro/pagamentos (Pix recorrente)** | Maior fonte de reclamação *e* de receita; mas território onde incumbentes já investem | baixa-média |

### Princípios estratégicos
1. **Não competir peça-a-peça** — a Agenda Edu já tem IA, WhatsApp e integrações isoladas. Vencer é a **combinação WhatsApp-first + IA-para-a-família + churn analytics**.
2. **Confiabilidade é feature** — boa parte da insatisfação é operacional (app trava, notificação some). Isso é barato de superar e gera boca-a-boca.
3. **Alvo inicial:** rede privada (segmento pagante, crescendo). Considerar nicho desatendido (educação infantil ou redes/franquias) para entrar.
4. **Cuidado com a consolidação:** Arco e Bemobi têm capital. A janela é UX + WhatsApp-first antes de eles fecharem essa lacuna.

---

### Nota metodológica
Vários domínios (sites oficiais, Reclame Aqui, App Store, Crunchbase) retornaram HTTP 403 ao fetch direto; as citações vieram de trechos indexados das mesmas fontes. Afirmações "alta" estão corroboradas por +1 fonte ou são dados oficiais (INEP, Mobile Time). Números de escolas/usuários são autodeclarados pelos fornecedores (marketing). Preços não são públicos.
