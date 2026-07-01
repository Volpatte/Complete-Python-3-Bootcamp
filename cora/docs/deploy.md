# Deploy no Render (HTTPS) — instalar no celular

O `render.yaml` (na raiz do repositório) já configura tudo. Você ganha uma URL
HTTPS gratuita — e com HTTPS o celular oferece **"Adicionar à tela inicial"**,
instalando o Cora como app.

## Opção A — Blueprint (1 clique, recomendado)

1. Faça login em https://render.com (pode entrar com o GitHub).
2. **New → Blueprint**.
3. Conecte o repositório `Volpatte/Complete-Python-3-Bootcamp` e escolha a
   branch `claude/agenda-edu-app-cfgzxq`.
4. O Render lê o `render.yaml` e propõe o serviço **cora**. Clique **Apply**.
5. Aguarde o build (~2–4 min). No fim, abre uma URL tipo
   `https://cora-xxxx.onrender.com`.

## Opção B — Web Service manual

**New → Web Service** → conecte o repo/branch e preencha:
- **Root Directory:** `cora`
- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`
- **Plan:** Free

## Variáveis de ambiente (opcionais)

No painel do serviço → **Environment**:
- `ANTHROPIC_API_KEY` — liga a IA real (resumos/assistente/insight).
- `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_ID` — liga o WhatsApp real.

Sem elas, roda em modo simulado/heurístico (ideal para demonstração).
`CORA_SECRET_KEY` é gerada automaticamente pelo Blueprint.

## Instalar no celular

1. Abra a URL HTTPS no Chrome (Android) ou Safari (iOS).
2. Faça login (`familia@cora.app` / `cora123`, ou os botões de acesso rápido).
3. **Android/Chrome:** menu ⋮ → **Adicionar à tela inicial** (ou o botão
   "⬇️ Instalar o app Cora"). **iOS/Safari:** Compartilhar → **Adicionar à
   Tela de Início**.
4. O Cora abre em tela cheia, com o ícone do coração. 💜

## Observações

- **Plano free hiberna após inatividade** — a primeira visita depois de um
  tempo ocioso leva ~30s pra "acordar". Normal.
- **Banco SQLite é efêmero** no free: a cada deploy/restart o banco é recriado
  e **repopulado com os dados de demonstração** (ótimo para demos). Para
  persistir dados entre deploys, crie um Postgres no Render e defina
  `DATABASE_URL=postgresql+psycopg://...` (o código já suporta — veja
  `app/db.py`). Nesse caso, acrescente `psycopg[binary]` ao `requirements.txt`.
