#!/usr/bin/env bash
# Sobe o Cora localmente. Uso: ./run.sh
set -e
cd "$(dirname "$0")"

python3 -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements.txt

# Opcional: IA real e WhatsApp real (descomente e preencha)
# export ANTHROPIC_API_KEY=sk-ant-...
# export WHATSAPP_TOKEN=... WHATSAPP_PHONE_ID=...

echo ""
echo "Cora rodando em  ->  http://localhost:8000"
echo "Login rápido:    coord@cora.app | prof@cora.app | familia@cora.app  (senha: cora123)"
echo ""
exec uvicorn app.main:app --reload --port 8000
