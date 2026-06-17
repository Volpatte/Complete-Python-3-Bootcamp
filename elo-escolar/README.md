# Elo Escolar — protótipo navegável

Plataforma de comunicação escola–família, posicionada como concorrente do
**Agenda Edu** e do **ClassApp**, com a camada que falta neles:

| Diferencial | O que demonstramos no protótipo |
|---|---|
| 🧠 **IA nativa** | Resumo automático de comunicados, priorização inteligente do feed, sugestão de respostas e tradução multi-idioma |
| 📊 **Analytics pedagógico** | Dashboard de engajamento por turma e *radar de famílias em risco* (churn) com insight gerado em linguagem natural |
| 💬 **Omnichannel / WhatsApp** | Comunicação que chega também no WhatsApp — a família responde de onde preferir |
| 🔌 **Integrações (hub)** | Conectores para ERP escolar, financeiro e LMS (Sponte, TOTVS, Google Classroom, Pix…) |

> Tudo com **dados de exemplo**, em memória. É um protótipo para validar fluxo e
> proposta de valor com escolas — não um produto em produção.

## Como rodar

```bash
cd elo-escolar
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# abra http://127.0.0.1:8000
```

## Telas (perfis navegáveis)

- `/` — landing + seletor de perfil
- `/coordenacao` — analytics, insight de IA, radar de risco, integrações
- `/professor` — compor comunicado e ver a IA resumir/priorizar/traduzir
- `/familia` — feed inteligente, agenda, tarefas, autorizações, respostas sugeridas

## Arquitetura

```
app/
  main.py        # rotas FastAPI (3 perfis) + render Jinja2
  data.py        # dados de exemplo (modelagem antecipa o MVP real)
  ai.py          # camada de IA — heurística offline; ponto de plugar a Claude API
  templates/     # base, home, coordenacao, professor, familia, comunicado
  static/style.css
```

### Onde plugar a IA de verdade

O módulo `app/ai.py` isola cada função de IA (resumo, prioridade, sugestão de
resposta, insight). No MVP, troca-se o corpo de cada função por uma chamada à
**Claude API** mantendo a mesma assinatura — `claude-sonnet-4-6` para o alto
volume (resumo/tradução) e um modelo maior para os insights analíticos da
coordenação. O `README` e os comentários em `ai.py` mostram o exemplo.

## Próximos passos sugeridos (rumo ao MVP)

1. Persistência real (Postgres) + autenticação multi-perfil e multi-escola.
2. Camada de IA real (Claude API) por trás das mesmas funções de `ai.py`.
3. Conector WhatsApp Business API + webhooks de entrega/leitura.
4. App mobile (React Native / Flutter) consumindo a mesma API.
5. Integrações reais (Google Classroom, ERPs) e portal financeiro.
