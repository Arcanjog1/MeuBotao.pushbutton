# -*- coding: utf-8 -*-
"""Presentation of existing backend results. No Revit, geometry or solver imports."""
from collections import Counter

STEPS = ("Configuração", "Paredes", "Modulação", "Revisão", "Criação", "Resultado")
TOKENS = {
    "Primary": (55, 108, 166), "Success": (115, 198, 157),
    "Warning": (232, 187, 107), "Danger": (240, 139, 139),
    "Surface": (39, 45, 53), "Background": (30, 35, 42),
    "SurfaceAlt": (47, 54, 63), "Border": (66, 75, 86),
    "TextPrimary": (234, 238, 243), "TextSecondary": (173, 185, 198),
    "Hover": (66, 123, 184), "Pressed": (42, 87, 136),
}
SPACING = (4, 8, 12, 16, 20, 24, 32)
RADIUS = {"Control": 4, "Panel": 6, "Preview": 8}
CONTROL_HEIGHT = {"Compact": 28, "Default": 32, "Action": 36}
TYPE = {"Title": 14, "SectionTitle": 10, "FieldLabel": 9,
        "Body": 9, "HelperText": 8.25, "Caption": 8.25, "StepLabel": 9, "Status": 9}
TOKENS.update({"Surface0": TOKENS["Background"], "Surface1": TOKENS["Surface"],
               "Surface2": TOKENS["SurfaceAlt"], "PrimaryHover": TOKENS["Hover"],
               "Stone": (99, 110, 119), "StoneTop": (125, 137, 145),
               "StoneSide": (68, 80, 91), "Reinforcement": (83, 139, 188)})


def friendly_problem(detail):
    """Translate presentation only; raw diagnostics remain in technical details."""
    text = str(detail or "")
    lower = text.lower()
    for words, message in (
        (("modificada", "deslocado", "rotacionado"), "Parede modificada. Selecione novamente e reanalise antes de criar."),
        (("prism", "collision", "colisão", "sobrepos"), "Possível sobreposição de blocos. Revise no modelo."),
        (("junction", "cross_band", "binding", "amarra"), "Problema de amarração. Revise o encontro das paredes."),
        (("abertura", "opening", "vao", "vão"), "Abertura requer revisão. Confira posição e dimensões."),
        (("famil", "famíl", "catalog"), "Família necessária não encontrada. Confira a lista de famílias."),
        (("pilarete", "boneca", "curto"), "Trecho curto de parede requer revisão."),
    ):
        if any(word in lower for word in words):
            return message
    return "Parede requer revisão. Visualize no modelo e consulte os detalhes."


def activity_text(detail):
    text = str(detail or "")
    lower = text.lower()
    if "graph" in lower or "grafo" in lower:
        return "Organizando os encontros entre paredes…"
    if "catalog" in lower or "catálogo" in lower:
        return "Verificando as famílias disponíveis…"
    if any(x in lower for x in ("physical", "candidate", "prism", "cross_band", "junction", "solver 18", "etapa 3b")):
        return "Calculando modulação…"
    return text.replace("solver", "cálculo").replace("Solver", "Cálculo")


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
    preflight = result.get("beta_preflight") or {}
    # FATAL (plano inconsistente) impede a RUN inteira.
    if preflight.get("errors"):
        return False, "Criação bloqueada: o plano tem erro fatal. Corrija e analise novamente."
    impossiveis = localized_blockers(result)
    puladas, nao_resolvidas = materialization_split(result)
    explicado = bool(impossiveis) or bool(puladas) or bool(nao_resolvidas)
    # FALHA FECHADA: laudo reprovado SEM dizer QUAIS peças estão envolvidas não
    # prova que o problema é localizado — a apresentação não pode liberar um
    # portão físico que ela não consegue explicar.
    if preflight and not preflight.get("ok", True) and not explicado:
        return False, "Criação bloqueada pela validação. Revise os problemas críticos."
    if not result.get("candidates"):
        return False, "Nenhum bloco planejado. Revise as paredes e analise novamente."
    if explicado:
        partes = []
        if puladas:
            partes.append("{} peça(s) não serão criadas (invadem abertura ou colidem)".format(puladas))
        if nao_resolvidas:
            partes.append("{} amarração(ões) ficarão NÃO RESOLVIDAS — revisão humana obrigatória".format(
                nao_resolvidas))
        if not partes:
            partes.append("{} ocorrência(s) localizada(s) registradas".format(impossiveis))
        return True, "Confira as quantidades e clique em Criar blocos no Revit. " + "; ".join(partes) + "."
    return True, "Confira as quantidades e clique em Criar blocos no Revit."


def localized_blockers(result):
    """Ocorrências localizadas do preflight (invasão de vão ou colisão).

    Não bloqueiam a RUN: a peça afetada não é criada (regra 48 — nenhuma peça
    ocupa o volume real de uma abertura, sem exceção). Se ela era amarração, o
    nó/fiada fica como amarração NÃO resolvida, com revisão humana."""
    preflight = (result or {}).get("beta_preflight") or {}
    return len(preflight.get("opening_violations") or []) + len(preflight.get("collisions") or [])


def materialization_split(result):
    """(peças que NÃO serão criadas, amarrações NÃO resolvidas) — contrato do motor.

    Sem o contrato (resultado antigo), devolve (None, None) — desconhecido nunca
    vira zero."""
    plano = (result or {}).get("materialization")
    if not isinstance(plano, dict):
        return None, None
    return len(plano.get("skipped") or []), len(plano.get("unresolved_bonds") or [])


def unresolved_bonds(result, creation=None):
    """Amarrações rejeitadas (a peça invadia abertura/colidia): NÃO resolvidas."""
    if creation is not None and creation.get("unresolved_bonds") is not None:
        return list(creation.get("unresolved_bonds") or [])
    return list(((result or {}).get("materialization") or {}).get("unresolved_bonds") or [])


def materialization_rows(result, creation=None):
    """Cada ocorrência com identificação completa, para a tela de revisão."""
    plano = (result or {}).get("materialization") or {}
    linhas = []
    for rec in list(plano.get("skipped") or []):
        papel = rec.get("structural_role")
        linhas.append(u"Parede {} · fiada {} · {} · {} — {}{} · não será criada{}".format(
            rec.get("wall_idx"), rec.get("course_index"), rec.get("logical_code") or "?",
            rec.get("rule_id"), rec.get("message"),
            u" · sobreposição {:.2f} cm".format(rec["overlap_cm"]) if isinstance(rec.get("overlap_cm"), (int, float)) else "",
            u" · AMARRAÇÃO ({}) — revisão humana".format(papel) if papel else ""))
    return linhas


def fatal_errors(result):
    """Erros que invalidam o plano inteiro (fiadas incompletas, geometria não
    finita, altura de fiada indisponível)."""
    return list(((result or {}).get("beta_preflight") or {}).get("errors") or [])


def materialization_counts(result, creation=None):
    """Contabilidade explícita: planejadas = criadas + puladas + falhas."""
    planejadas = (creation or {}).get("planned_total")
    if planejadas is None:
        contagem = planned_counts(result)
        planejadas = sum(contagem.values()) if contagem else None
    criadas = (creation or {}).get("created_count")
    puladas = (creation or {}).get("skipped_count")
    if creation is None:
        falhas = None
    elif creation.get("failed_count") is not None:
        falhas = creation.get("failed_count")           # por PEÇA
    else:
        falhas = len(creation.get("failures") or [])
    return {"planejadas": planejadas, "criadas": criadas, "puladas": puladas, "falhas": falhas,
            "fecha": (None if None in (planejadas, criadas, puladas, falhas)
                      else planejadas == criadas + puladas + falhas)}


def skipped_rows(creation):
    """Cada peça pulada com motivo rastreável (parede, fiada, regra)."""
    linhas = []
    for row in (creation or {}).get("skipped") or []:
        linhas.append(u"Parede {} · fiada {} · {} — {} ({})".format(
            row.get("wall_idx"), row.get("course_index"), row.get("logical_code") or "?",
            row.get("message") or "não materializável", row.get("rule_id") or "UNBUILDABLE"))
    return linhas


def wall_label(row):
    ids = row.get("wall_ids") or []
    if ids:
        return "Parede {}".format(str(ids[0]))
    index = row.get("wall_idx")
    return "Eixo {} (temporário)".format(index + 1) if isinstance(index, int) else "Projeto"


def family_rows(catalog, missing):
    rows = [("OK", code.replace("CHANNEL_U_", "Canaleta ").replace("CHANNEL_", "Canaleta "), "Disponível") for code in sorted(catalog or {})]
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
        self.step, self.status, self.can_create = step, {2: "analyzing", 3: "solving", 5: "creating"}.get(step, "loading"), False

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

    def completed(self, result, solve_result=None):
        """`solve_result` (pos-#42) traz os itens de REVISAO HUMANA da regra 76.1:
        com eles o desfecho e' "concluida com revisao necessaria", nunca "sucesso"."""
        self.step = 6
        self.status = ("error" if not result.get("created_count") or result.get("course_height_error")
                       else "warning" if result.get("failures") or result.get("skipped_wall_count")
                       or result.get("reproved_wall_count") or result.get("colliding_instance_count")
                       else "success")
        pendentes, portoes = review_summary(solve_result if solve_result is not None else self.result)
        if self.status == "success" and (pendentes or portoes):
            self.status = "warning"


    def report_text(self, handler, creation=None):
        result = self.result or {}
        counts = self.counts
        strategy = "Canaletas (CHANNEL)" if self.strategy == "CHANNEL" else "Sem reforço"
        prov = getattr(handler, "runtime_provenance", None) or {}
        versao = ("Versão: canal={} branch={} commit={} cache={}".format(
            prov.get("CHANNEL", "?"), prov.get("SOURCE_BRANCH", "-"), prov.get("RESOLVED_COMMIT", "?"),
            prov.get("CACHE_STATUS", "?")) if prov else "Versão: não informada pelo loader.")
        lines = ["RESULTADOS", versao, "Reforço: " + strategy,
                 "Paredes selecionadas: {}".format(len(handler.walls_to_create or [])),
                 "Aberturas detectadas: {}".format(len(handler.all_openings or []))]
        if counts is None:
            lines.append("Quantidade de todas as fiadas: indisponível neste resultado. Reanalise para atualizar.")
        else:
            lines.append("{} blocos planejados (todas as fiadas)".format(sum(counts.values())))
            lines.extend("  {}: {}".format(k.replace("CHANNEL_U_", "Canaleta ").replace("CHANNEL_", "Canaleta "), counts[k]) for k in sorted(counts))
        if creation is not None:
            lines.extend(["{} bloco(s) criado(s)".format(creation.get("created_count", 0)),
                          "Falhas de criação: {}".format(len(creation.get("failures") or []))])
        lines.extend(["", "VALIDAÇÃO", self.reason if creation is None else
                      "Confira os blocos no Revit antes de concluir a revisão humana."])
        preflight = result.get("beta_preflight") or {}
        if preflight and not preflight.get("ok"):
            for key in ("errors", "opening_violations", "collisions"):
                lines.extend("Crítico: " + friendly_problem(item) for item in preflight.get(key) or [])
        pendentes = review_items(result, creation)
        lines.extend(["", "REVISÃO NECESSÁRIA (não é falha de criação)"])
        if pendentes:
            lines.extend("  " + row["text"] for row in pendentes)
        else:
            lines.append("  Nenhum encontro marcado para revisão humana.")
        for label, count in hard_gate_counts(result):
            if count:
                lines.append("  Crítico: {} — {}".format(label, count))
        sem_encontro = no_functional_junction_count(result)
        if sem_encontro:
            lines.append("  (Técnico: {} fiada(s) sem encontro funcional por projeto — "
                         "aberturas consomem a parede principal; não é erro.)".format(sem_encontro))
        contas = materialization_counts(result, creation)
        if creation is not None:
            resolvida = creation.get("structurally_resolved")

            def _n(valor):
                return "—" if valor is None else valor
            # a RUN foi executada quando a criacao terminou (mesmo com 0 pecas criadas)
            lines.extend(["", "ESTADO ESTRUTURAL",
                          "  RUN executada: sim — {} de {} peça(s) criada(s)".format(
                              _n(contas["criadas"]), _n(contas["planejadas"])),
                          "  Modulação estruturalmente resolvida: {}".format(
                              "sim" if resolvida is True else ("NÃO — {} pendência(s) listada(s) em "
                                                             "REVISÃO NECESSÁRIA".format(len(pendentes))
                                                             if resolvida is False else "—"))])
            lines.extend(["", "MATERIALIZAÇÃO",
                          "  Planejados: {}".format(_n(contas["planejadas"])),
                          "  Criados: {}".format(_n(contas["criadas"])),
                          "  Ignorados: {}".format(_n(contas["puladas"])),
                          "  Falhas de criação: {}".format(_n(contas["falhas"])),
                          "  Contabilidade fecha: {}".format(
                              "sim" if contas["fecha"] is True else (
                                  "NÃO — investigar" if contas["fecha"] is False
                                  else "— (valor desconhecido)"))])
            lines.extend("  " + linha for linha in skipped_rows(creation)[:40])
        elif localized_blockers(result):
            puladas, nao_resolvidas = materialization_split(result)
            lines.extend(["", "MATERIALIZAÇÃO",
                          "  Peças que NÃO serão criadas: {}".format(puladas if puladas is not None else "—"),
                          "  Amarrações NÃO resolvidas (revisão humana obrigatória): {}".format(
                              nao_resolvidas if nao_resolvidas is not None else "—")])
            lines.extend("  " + linha for linha in materialization_rows(result)[:40])
        for erro in fatal_errors(result):
            lines.append("  FATAL: {}".format(erro))
        lines.extend(["", "AVISOS / REVISÃO",
                      "Colisões relatadas: {}".format(len(result.get("collisions") or [])),
                      "Violações de aberturas relatadas: {}".format(len(result.get("door_void_violations") or [])),
                      "Paredes com amarração reprovada: {}".format(sum(
                          1 for a in (result.get("wall_bond_audits") or {}).values() if not a.get("ok")))])
        lines.extend(["", "PAREDES NÃO MODULADAS"])
        retained = ((creation or {}).get("retained_walls") if (creation or {}).get("retained_walls") is not None
                    else result.get("unmodulated_walls")) or []
        for i, w in enumerate(retained, 1):
            if w.get("reason") == "INCOMPLETE_CREATION":
                lines.append("Parede retida {}: criação incompleta — {} de {} peça(s) não criada(s); "
                             "referência preservada.".format(i, w.get("missing_count"), w.get("planned_count")))
            else:
                lines.append("Parede retida {}: {}".format(i, friendly_problem(w.get("reason"))))
        if not retained:
            lines.append("Nenhuma retenção informada pelo motor.")
        if creation:
            lines.extend(friendly_problem(f) for f in creation.get("failures") or [])
        for number, row in enumerate(handler.error_rows or [], 1):
            lines.append("{} — {}: {}".format("Corrigido" if row.get("resolved") else "Requer revisão",
                                              "Parede {}".format(number), friendly_problem(row.get("problem_text", ""))))
        lines.extend(["", "FAMÍLIAS"])
        families = dict(handler.catalog or {})
        families.update(handler.channel_catalog or {})
        missing = list(handler.catalog_missing or []) + list(handler.channel_catalog_missing or [])
        lines.extend("{} — {}: {}".format(*row) for row in family_rows(families, missing))
        if self.strategy == "CHANNEL" and not handler.channel_catalog and not handler.channel_catalog_missing:
            lines.append("Canaletas: verificação pendente; será realizada pelo backend ao analisar.")
        lines.extend(["", "DESEMPENHO", "Tempo e operações detalhadas em Detalhes da execução."])
        return "\n".join(lines)

# --------------------------------------------------------------- pos-PR #42
# O motor final classifica tres desfechos diferentes no encontro entre paredes,
# e a interface NAO pode achatar os tres num "tudo certo":
#   - portao duro (colisao, fora do modulo, sem apoio, invasao de vao, canaleta
#     ou compensador exercendo amarracao): o esperado e' ZERO - se aparecer, e'
#     critico;
#   - `missing_required_junction_bond` (regra 76.1): a peca de amarracao NAO
#     cabe; o motor marca `review: HUMAN_REVIEW`. A criacao acontece, mas o caso
#     precisa de REVISAO HUMANA - nunca e' "falha" nem "tudo perfeito";
#   - `NO_FUNCTIONAL_JUNCTION` (secao 77): naquela fiada NAO EXISTE encontro
#     funcional (as aberturas consumiram a principal dos dois lados). E' projeto,
#     nao defeito: aparece so' nos detalhes tecnicos, nunca como erro.
HARD_GATES = (
    ("Colisões", "collisions"),
    ("Trechos fora do módulo", "non_modular"),
    ("Invasão de abertura", "door_void_violations"),
    ("Canaleta exercendo amarração", "channel_as_junction_bond"),
    ("Compensador exercendo amarração", "compensator_as_junction_bond"),
)


def hard_gate_counts(result):
    """Portoes duros do motor final, com o nome que o usuario entende."""
    result = result or {}
    counts = [(label, len(result.get(key) or [])) for label, key in HARD_GATES]
    support = (result.get("physical_support") or {}).get("counts") or {}
    counts.append(("Peças sem apoio",
                   sum(v for k, v in support.items() if str(k).startswith("UNSUPPORTED"))))
    return counts


def hard_gate_total(result):
    return sum(count for _label, count in hard_gate_counts(result))


def review_items(result, creation=None):
    """Encontros que o motor entrega marcados para REVISAO HUMANA (regra 76.1).

    Nao inclui `NO_FUNCTIONAL_JUNCTION`: aquilo nao e' pendencia, e' a topologia
    real da fiada (secao 77)."""
    rows = []
    for item in (result or {}).get("missing_required_junction_bond") or []:
        node = item.get("node_index")
        course = item.get("course_index")
        kind = {"L_CORNER": "canto L", "T_INTERSECTION": "encontro em T",
                "X_INTERSECTION": "cruzamento"}.get(item.get("node_kind"), "encontro")
        rows.append({
            "node": node, "course": course,
            "text": u"Encontro {} (nó {}), fiada {}: a peça de amarração não cabe — revise no modelo."
                    .format(kind, node, course),
        })
    # Opção A: amarração REJEITADA na materialização (invadia abertura/colidia)
    # não é amarração resolvida — entra aqui, nunca some.
    for item in unresolved_bonds(result, creation):
        rows.append({
            "node": item.get("node_index"), "course": item.get("course_index"),
            "text": u"Amarração NÃO resolvida (nó {}), fiada {}: {} {} rejeitado — {}.".format(
                item.get("node_index"), item.get("course_index"), item.get("logical_code") or "?",
                item.get("structural_role") or "", item.get("rejected_rule") or "invade abertura"),
        })
    return rows


def no_functional_junction_count(result):
    """Fiadas em que, por projeto, nao existe encontro funcional (secao 77)."""
    role = (result or {}).get("junction_role_by_course") or {}
    return len(role.get("no_functional_junction") or [])


def review_summary(result):
    """(itens de revisao, portoes duros) - o que a tela final tem de dizer."""
    return len(review_items(result)), hard_gate_total(result)

