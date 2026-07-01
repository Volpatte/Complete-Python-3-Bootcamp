"""Analytics ao vivo da coordenação — calculados do banco (não mock).

Engajamento por turma e radar de famílias em risco derivam das leituras reais
(tabela Leitura) e dos comunicados de cada turma.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from . import data, models

# Textos do radar de risco (parametrizados com números → formatados por idioma).
_NUNCA_MOTIVO = {"pt": "Nunca leu um comunicado", "en": "Never read an announcement", "es": "Nunca leyó un comunicado"}
_NUNCA_ROTULO = {"pt": "nunca leu", "en": "never read", "es": "nunca leyó"}


def _fmt_sem_leitura(dias: int, lang: str) -> str:
    return {"pt": f"Sem leitura há {dias} dias", "en": f"No reads in {dias} days",
            "es": f"Sin lectura hace {dias} días"}.get(lang, f"Sem leitura há {dias} dias")


def _fmt_baixa_taxa(pct: int, lang: str) -> str:
    return {"pt": f"Lê só {pct}% dos comunicados", "en": f"Reads only {pct}% of announcements",
            "es": f"Lee solo {pct}% de los comunicados"}.get(lang, f"Lê só {pct}% dos comunicados")


def _fmt_dias(dias: int, lang: str) -> str:
    return {"pt": f"há {dias} dias", "en": f"{dias} days ago",
            "es": f"hace {dias} días"}.get(lang, f"há {dias} dias")


def _coletar(db, escola_id: int):
    fams = list(db.scalars(select(models.Usuario).where(
        models.Usuario.escola_id == escola_id, models.Usuario.papel == models.FAMILIA)))
    coms = list(db.scalars(select(models.Comunicado).where(models.Comunicado.escola_id == escola_id)))
    rows = db.execute(
        select(models.Leitura.usuario_id, models.Leitura.comunicado_id, models.Leitura.lido_em)
        .where(models.Leitura.lido.is_(True))
    ).all()
    lido_set = {(u, c) for (u, c, _) in rows}
    ultimo: dict[int, object] = {}
    for u, _c, t in rows:
        if t and (u not in ultimo or t > ultimo[u]):
            ultimo[u] = t
    return fams, coms, lido_set, ultimo


def _coms_da_turma(coms, turma: str):
    return [c for c in coms if c.turma == turma or c.turma == "Toda a escola"]


def _perfil(f, coms, lido_set, ultimo, hoje, lang="pt"):
    coms_f = _coms_da_turma(coms, f.turma)
    n = len(coms_f)
    lidos = sum(1 for c in coms_f if (f.id, c.id) in lido_set)
    taxa = lidos / n if n else 0.0
    ult = ultimo.get(f.id)
    dias = (hoje - ult.date()).days if ult else None
    if ult is None:
        risco, motivo, rotulo = True, _NUNCA_MOTIVO.get(lang, _NUNCA_MOTIVO["pt"]), _NUNCA_ROTULO.get(lang, _NUNCA_ROTULO["pt"])
    elif dias > 7:
        risco, motivo, rotulo = True, _fmt_sem_leitura(dias, lang), _fmt_dias(dias, lang)
    elif taxa < 0.5:
        risco, motivo, rotulo = True, _fmt_baixa_taxa(round(taxa * 100), lang), _fmt_dias(dias, lang)
    else:
        risco, motivo, rotulo = False, "", _fmt_dias(dias, lang)
    return {"nome": f.nome, "turma": f.turma, "taxa": taxa, "risco": risco, "motivo": motivo, "rotulo": rotulo}


def engajamento_por_turma(db, escola_id: int, hoje: date | None = None, lang: str = "pt") -> list[dict]:
    hoje = hoje or date.today()
    fams, coms, lido_set, ultimo = _coletar(db, escola_id)
    perfis = [_perfil(f, coms, lido_set, ultimo, hoje, lang) for f in fams]
    turmas = db.scalars(
        select(models.Turma).where(
            models.Turma.escola_id == escola_id, models.Turma.ativo.is_(True)
        ).order_by(models.Turma.nome)
    )
    out = []
    for t in turmas:
        membros = [p for p in perfis if p["turma"] == t.nome]
        if not membros:
            continue
        taxa = round(sum(p["taxa"] for p in membros) / len(membros) * 100)
        risco = sum(1 for p in membros if p["risco"])
        out.append({
            "turma": t.nome, "taxa_leitura": taxa,
            "famílias_ativas": len(membros) - risco, "risco": risco,
        })
    return out


def familias_em_risco(db, escola_id: int, hoje: date | None = None, limite: int = 6, lang: str = "pt") -> list[dict]:
    hoje = hoje or date.today()
    fams, coms, lido_set, ultimo = _coletar(db, escola_id)
    perfis = [_perfil(f, coms, lido_set, ultimo, hoje, lang) for f in fams]
    risco = sorted((p for p in perfis if p["risco"]), key=lambda p: p["taxa"])
    return [
        {"nome": f'{p["nome"]} ({p["turma"]})', "ultima_leitura": p["rotulo"], "motivo": p["motivo"]}
        for p in risco[:limite]
    ]
