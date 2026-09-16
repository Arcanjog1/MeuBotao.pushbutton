# -*- coding: utf-8 -*-
"""Presentation of existing backend results. No Revit, geometry or solver imports."""
from collections import Counter

STEPS = ("Configuração", "Paredes", "Revisão", "Modulação", "Criação", "Resultado")
TOKENS = {
    "Primary": (32, 91, 157), "Success": (25, 112, 75),
    "Warning": (146, 83, 12), "Danger": (175, 42, 42),
    "Surface": (255, 255, 255), "Background": (244, 246, 248),
    "Border": (214, 221, 229), "TextPrimary": (32, 44, 58),
    "TextSecondary": (83, 99, 117), "Hover": (24, 72, 126),
    "Pressed": (18, 54, 95),
}


def elapsed_text(seconds):
    seconds = max(0, int(seconds))
    return "{:02d}:{:02d}".format(seconds // 60, seconds % 60)


def friendly_error(detail):
    text = str(detail or "")
    lower = text.lower()
    if any(word in lower for word in ("deslocado", "rotacionado", "assinatura", "geometria/catalogo")):
        return "As paredes ou a configuração mudaram. Feche esta janela, selecione as paredes novamente e reanalise."
    if any(word in lower for word in ("family", "familia", "catálogo", "catalogo")):
        return "Faltam famílias necessárias. Consulte a lista de famílias, carregue-as no Revit e reabra a modulação."
    if "bloqueado" in lower:
        return "A validação impediu a criação. Revise os problemas indicados e analise novamente."
    return "Não foi possível concluir esta etapa. Consulte os detalhes da execução e tente novamente após corrigir a causa."


def planned_counts(result):
    """Count the already materialized plan, not the representative A/B pair.

    A missing all-course plan is UNKNOWN: legacy representative candidates
    are not sufficient evidence for the number of Revit instances.
    """
    sources = (result or {}).get("course_candidates")
    if sources is None:
        return None
    return dict(Counter(c.get("logical_code", "Sem código")
                        for source in sources.values() for c in source))


def creation_gate(result, catalog_missing=(), channel_missing=()):
    """Mirror existing backend gates; diagnostic warnings remain warnings."""
    if catalog_missing or channel_missing:
        return False, "Carregue as famílias ausentes e reabra a modulação."
    if not result:
        return False, "Analise a modulação antes de criar os blocos."
    if result.get("error"):
        return False, friendly_error(result["error"])
    preflight = result.get("beta_preflight")
    if preflight is not None and not preflight.get("ok"):
        return False, "Criação bloqueada pela validação. Revise os problemas críticos."
    if not result.get("candidates"):
        return False, "Nenhum bloco planejado. Revise as paredes e analise novamente."
    return True, "Confira as quantidades e clique em Criar blocos no Revit."


def wall_label(row):
    ids = row.get("wall_ids") or []
    if ids:
        return "Parede {}".format(str(ids[0]))
    index = row.get("wall_idx")
    return "Eixo {} (temporário)".format(index + 1) if isinstance(index, int) else "Projeto"


def family_rows(catalog, missing):
    rows = [("OK", code, "Disponível") for code in sorted(catalog or {})]
    rows.extend(("Ausente", m.get("logical_code", ""),
                 "{} / {} — {}".format(m.get("family_name", ""), m.get("type_name", ""),
                                       m.get("reason", "Carregue a família no projeto"))) for m in missing or [])
    return rows


class ModulationUiState(object):
    def __init__(self, step=1, strategy=None):
        self.step = step
        self.strategy = "CHANNEL" if strategy == "CHANNEL" else "NONE"
        self.status = "idle"
        self.can_create = False
        self.reason = "Analise a modulação antes de criar os blocos."
        self.counts = None
        self.result = None

    def start(self, step):
        self.step, self.status, self.can_create = step, "loading", False

    def solved(self, result, missing=(), channel_missing=()):
        self.result = result
        self.step = 4
        self.counts = planned_counts(result)
        self.can_create, self.reason = creation_gate(result, missing, channel_missing)
        self.status = "ready" if self.can_create else "error"

    def failed(self, detail):
        self.status, self.can_create = "error", False
        self.reason = friendly_error(detail)

    def cancelled(self):
        self.status, self.can_create = "cancelled", False
        self.reason = "Execução interrompida. Confira o estado das paredes antes de continuar."

    def completed(self, result):
        self.step = 6
        self.status = ("error" if not result.get("created_count") or result.get("course_height_error")
                       else "warning" if result.get("failures") or result.get("skipped_wall_count")
                       or result.get("reproved_wall_count") or result.get("colliding_instance_count")
                       else "success")

    def report_text(self, handler, creation=None):
        result = self.result or {}
        counts = self.counts
        strategy = "Canaletas (CHANNEL)" if self.strategy == "CHANNEL" else "Sem reforço"
        lines = ["RESULTADOS", "Reforço: " + strategy,
                 "Paredes selecionadas: {}".format(len(handler.walls_to_create or [])),
                 "Aberturas detectadas: {}".format(len(handler.all_openings or []))]
        if counts is None:
            lines.append("Quantidade de todas as fiadas: indisponível neste resultado. Reanalise para atualizar.")
        else:
            lines.append("{} blocos planejados (todas as fiadas)".format(sum(counts.values())))
            lines.extend("  {}: {}".format(k, counts[k]) for k in sorted(counts))
        if creation is not None:
            lines.extend(["{} bloco(s) criado(s)".format(creation.get("created_count", 0)),
                          "Falhas de criação: {}".format(len(creation.get("failures") or []))])
        lines.extend(["", "VALIDAÇÃO", self.reason if creation is None else
                      "Confira os blocos no Revit antes de concluir a revisão humana."])
        preflight = result.get("beta_preflight") or {}
        if preflight and not preflight.get("ok"):
            for key in ("errors", "opening_violations", "collisions"):
                lines.extend("Crítico: {}".format(item) for item in preflight.get(key) or [])
        lines.extend(["", "AVISOS / REVISÃO",
                      "Colisões relatadas: {}".format(len(result.get("collisions") or [])),
                      "Violações de aberturas relatadas: {}".format(len(result.get("door_void_violations") or [])),
                      "Paredes com amarração reprovada: {}".format(sum(
                          1 for a in (result.get("wall_bond_audits") or {}).values() if not a.get("ok")))])
        lines.extend(["", "PAREDES NÃO MODULADAS"])
        retained = result.get("unmodulated_walls") or []
        lines.extend("Eixo {} (temporário): {}".format(w.get("wall_idx"), w.get("reason", "Revisar")) for w in retained)
        if not retained:
            lines.append("Nenhuma retenção informada pelo motor.")
        if creation:
            lines.extend(str(f) for f in creation.get("failures") or [])
        for row in handler.error_rows or []:
            lines.append("{} — {}: {}".format("Corrigido" if row.get("resolved") else "Requer revisão",
                                              wall_label(row), row.get("problem_text", "")))
        lines.extend(["", "FAMÍLIAS"])
        families = dict(handler.catalog or {})
        families.update(handler.channel_catalog or {})
        missing = list(handler.catalog_missing or []) + list(handler.channel_catalog_missing or [])
        lines.extend("{} — {}: {}".format(*row) for row in family_rows(families, missing))
        if self.strategy == "CHANNEL" and not handler.channel_catalog and not handler.channel_catalog_missing:
            lines.append("Canaletas: verificação pendente; será realizada pelo backend ao analisar.")
        lines.extend(["", "DESEMPENHO", "Tempo e operações detalhadas em Detalhes da execução."])
        return "\n".join(lines)
