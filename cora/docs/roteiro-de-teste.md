# Roteiro de teste — Cora

Guia passo a passo para validar todas as funcionalidades do MVP. Tempo: ~10 min.

> Dica: para testar **conversa entre duas pessoas** (família ↔ escola) ao mesmo
> tempo, abra **duas janelas**: uma normal e uma **anônima/privada** (cada uma
> tem sua própria sessão de login).

---

## 0. Subir o app

```bash
cd cora
./run.sh                      # cria venv, instala deps e sobe
# ou manual:
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Abra **http://localhost:8000**. O banco (SQLite `cora.db`) é criado e populado
automaticamente no primeiro acesso.

**Logins de demonstração** (senha **`cora123`**) — ou use os botões de acesso
rápido na tela de login:

| Papel | E-mail |
|---|---|
| Coordenação | `coord@cora.app` |
| Professor | `prof@cora.app` |
| Família | `familia@cora.app` |

---

## 1. Família — app mobile (o coração do produto)

1. Login como **Família** (`/login` → "👨‍👩‍👧 Família").
2. **Início**: confira o cabeçalho, as ações rápidas, os *stories* e o **feed**.
   - ✅ Cada comunicado tem o chip **"✨ Resumo Cora IA"** com um resumo.
   - ✅ O feed vem **ordenado por prioridade** (URGENTE no topo).
3. Toque no comunicado **"URGENTE: ... saída ..."**.
   - ✅ Abre o detalhe com resumo, **tradução** e **respostas sugeridas**.
   - ✅ Ao abrir, a **leitura é gravada** (a coordenação verá o contador subir).
4. Aba **Agenda**: eventos com data + **resumo da semana pela IA**.
5. Volte ao Início → seção **Tarefas** e **Autorizações** (botão "Autorizar").

## 2. Assistente Cora (IA conversacional)

1. No Início, toque em **🤖 Cora IA** (ou aba Mensagens → "Assistente Cora").
2. Toque nas sugestões ou digite:
   - "meu filho faltou?" → ✅ responde faltas/presença
   - "cardápio de hoje" → ✅ lista o cardápio
   - "tem prova essa semana?" → ✅ lista próximos eventos
   - "quero pagar o boleto" → ✅ valor + vencimento + Pix
3. ✅ O indicador de **digitação** aparece antes da resposta.

> Sem `ANTHROPIC_API_KEY`, as respostas vêm da heurística (offline). Com a chave,
> são geradas pela Claude API, ancoradas nos mesmos dados.

## 3. Mensageria bidirecional (família ↔ escola)

1. **Família** (janela 1): aba **Mensagens** → abra **"Prof. Marina"**.
   - ✅ Vê as mensagens da professora. Envie: *"Combinado, busco às 11h30!"*
2. **Professor** (janela 2, anônima): login como Professor → menu **Mensagens**.
   - ✅ A conversa aparece com sua mensagem. Abra e **responda**.
3. **Família** (janela 1): reabra a conversa.
   - ✅ A resposta do professor aparece. **Conversa real, nas duas direções.**

## 4. Professor envia comunicado → chega na família

1. **Professor**: aba **Professor** → preencha título e mensagem (use a palavra
   "urgente" para ver a priorização) → **"✨ Pré-processar com IA"**.
   - ✅ Aparece prioridade sugerida, resumo e prévia de tradução.
2. Marque "Pedir confirmação" e clique **"Enviar comunicado"**.
   - ✅ Banner verde: "Comunicado enviado...".
3. **Família**: volte ao **Início** e recarregue.
   - ✅ O novo comunicado está no topo do feed.

## 5. WhatsApp (omnichannel + recibo de leitura)

1. **Família**: no Início, card verde → **"Ativar no WhatsApp"**.
   - ✅ Vira "✅ Ativado!". (Já vem ativo no seed; se quiser ver o botão, a
     coordenação pode resetar — ou apenas observe o estado "Ativado".)
2. **Professor**: envie um comunicado (passo 4). Isso **espelha no WhatsApp** da
   família inscrita.
3. **Coordenação**: login → menu **WhatsApp** (`/whatsapp`).
   - ✅ KPIs: mensagens enviadas, **taxa de entrega**, **taxa de leitura**.
   - ✅ Lista de entregas com status (✓ enviado / ✓✓ entregue / ✓✓ lido).
   - ✅ Badge **"modo simulado"**.
4. Clique **"▶ Simular entrega/leitura"** algumas vezes.
   - ✅ Os status avançam: enviado → entregue → lido, e as taxas sobem.

## 6. Coordenação — analytics

1. **Coordenação**: aba **Coordenação**.
   - ✅ KPIs (taxa média de leitura, comunicados, famílias em risco, integrações).
   - ✅ **Insight da IA** em linguagem natural.
   - ✅ **Engajamento por turma** (barras) e **Radar de famílias em risco**.
   - ✅ Painel de **Integrações** (ERP/LMS/WhatsApp/Pix).

## 7. PWA — instalar como app

1. **Família** em `http://localhost:8000/familia`.
2. ✅ Botão **"⬇️ Instalar o app Cora"** no rodapé (ou ícone "Instalar" na barra
   de endereço do Chrome/Edge). Instale.
3. ✅ Abre em **janela própria, tela cheia**, com o ícone do coração.
4. **Offline**: nas DevTools (aba Network → Offline) recarregue uma página nova.
   - ✅ Aparece a tela "Você está offline" da Cora.

## 8. Autenticação e controle de acesso

1. Sem login, acesse `/familia` → ✅ redireciona para `/login`.
2. Logado como **Família**, tente `/coordenacao` → ✅ volta para `/familia`.
3. **Coordenação** tentando abrir uma conversa de professor → ✅ bloqueado.
4. **Sair** (menu/aba) → ✅ exige login de novo.

---

## Modo real (opcional)

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # IA de verdade (resumos, assistente, insight)
export WHATSAPP_TOKEN=...                   # WhatsApp Business API (Graph/Meta)
export WHATSAPP_PHONE_ID=...
./run.sh
```

- Com `ANTHROPIC_API_KEY`: resumos e respostas do assistente vêm da Claude API.
- Com as credenciais do WhatsApp: a Central mostra **"modo real"** e os envios
  vão de verdade (recibos viriam dos webhooks da Meta).

## Reset do banco

```bash
rm cora/cora.db     # recriado e repopulado no próximo acesso
```
