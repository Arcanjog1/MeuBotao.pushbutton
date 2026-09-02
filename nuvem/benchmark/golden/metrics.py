# -*- coding: utf-8 -*-
"""Metricas OBRIGATORIAS do golden benchmark, por categoria (itens 2 e 10
do pedido), cada uma com a DIRECAO que decide se um numero maior e'
melhor, pior, ou nenhum dos dois (item 12).

Este modulo NAO recalcula o que `benchmark/scoring.py` e
`benchmark/validators/*` ja calculam - ele LE aquele resultado
(`score_project(...)`, opcionalmente a lista de `findings` e o
`project` bruto) e reorganiza em categorias de dominio (PAREDES, FIADAS,
BLOCOS, PRISMA, ENCONTROS, ABERTURAS, QUALIDADE, PERFORMANCE) porque e'
assim que o pedido quer poder ler o resultado - nao porque o numero em si
seja novo.

DADOS INCOMPLETOS (item 26): uma metrica que nao pode ser calculada com o
que foi passado volta como `{"value": None, "status": "NOT_AVAILABLE",
...}` - NUNCA um zero inventado. Zero e' um valor medido (zero
colisoes); `None`/`NOT_AVAILABLE` e' "nao sei".
"""

from ..validators import base as validators_base
from .. import model

# ------------------------------------------------------------- direcao
HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
LOWER_IS_BETTER = "LOWER_IS_BETTER"
INFORMATIONAL = "INFORMATIONAL"
CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"

ALL_DIRECTIONS = (HIGHER_IS_BETTER, LOWER_IS_BETTER, INFORMATIONAL,
                  CONTEXT_DEPENDENT)

STATUS_OK = "OK"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"


def _metric(value, direction, unit=None, note=None):
    return {
        "value": value,
        "status": STATUS_NOT_AVAILABLE if value is None else STATUS_OK,
        "direction": direction,
        "unit": unit,
        "note": note,
    }


def _na(direction, note=None):
    return _metric(None, direction, note=note)


def _findings_by_code(findings):
    counts = {}
    for item in findings or []:
        counts[item.get("code")] = counts.get(item.get("code"), 0) + 1
    return counts


def _code_count(by_code, code):
    return by_code.get(code, 0)


# ----------------------------------------------------------- PAREDES
def wall_metrics(project=None, score=None):
    if score is not None:
        total = score.get("walls")
        not_modulated = _code_count(score.get("findings_by_code") or {},
                                    "COVERAGE_WALL_NOT_MODULATED")
        modulated = None if total is None else max(0, total - not_modulated)
        coverage_pct = (round(100.0 * modulated / total, 2)
                        if total else None)
        return {
            "total_walls": _metric(total, INFORMATIONAL, unit="paredes"),
            "walls_modulated": _metric(modulated, HIGHER_IS_BETTER, unit="paredes"),
            "walls_not_modulated": _metric(not_modulated, LOWER_IS_BETTER, unit="paredes"),
            "coverage_pct": _metric(coverage_pct, HIGHER_IS_BETTER, unit="%"),
        }
    if project is not None:
        total = len(project.get("walls") or [])
        modulated = sum(1 for w in project.get("walls") or [] if model.count_blocks(
            {"walls": [w]}) > 0)
        not_modulated = total - modulated
        coverage_pct = round(100.0 * modulated / total, 2) if total else None
        return {
            "total_walls": _metric(total, INFORMATIONAL, unit="paredes"),
            "walls_modulated": _metric(modulated, HIGHER_IS_BETTER, unit="paredes"),
            "walls_not_modulated": _metric(not_modulated, LOWER_IS_BETTER, unit="paredes"),
            "coverage_pct": _metric(coverage_pct, HIGHER_IS_BETTER, unit="%"),
        }
    return {
        "total_walls": _na(INFORMATIONAL),
        "walls_modulated": _na(HIGHER_IS_BETTER),
        "walls_not_modulated": _na(LOWER_IS_BETTER),
        "coverage_pct": _na(HIGHER_IS_BETTER),
    }


# ------------------------------------------------------------ FIADAS
def course_metrics(project=None, score=None):
    by_code = _findings_by_code_from(score)
    missing_rows = _code_count(by_code, "COVERAGE_MISSING_ROW") if by_code is not None else None
    mostly_empty = _code_count(by_code, "COVERAGE_ROW_MOSTLY_EMPTY") if by_code is not None else None
    gaps = _code_count(by_code, "COVERAGE_GAP_IN_ROW") if by_code is not None else None
    partial_walls = _code_count(by_code, "COVERAGE_PARTIAL_WALL") if by_code is not None else None

    total_rows = None
    if project is not None:
        total_rows = sum(len(w.get("rows") or []) for w in project.get("walls") or [])

    return {
        "total_rows": _metric(total_rows, INFORMATIONAL, unit="fiadas"),
        "missing_rows": _metric(missing_rows, LOWER_IS_BETTER, unit="fiadas"),
        "mostly_empty_rows": _metric(mostly_empty, LOWER_IS_BETTER, unit="fiadas"),
        "gaps_in_row": _metric(gaps, LOWER_IS_BETTER, unit="ocorrencias"),
        "partial_walls": _metric(partial_walls, LOWER_IS_BETTER, unit="paredes"),
    }


def _findings_by_code_from(score):
    if score is None:
        return None
    return score.get("findings_by_code") or {}


# ------------------------------------------------------------ BLOCOS
# Codigos conhecidos do catalogo (item 10). "outros" pega qualquer coisa
# fora desta lista - nunca descartado em silencio.
KNOWN_BLOCK_CODES = ("B39", "B34", "B54", "B19", "C09", "C04")


def block_metrics(project=None):
    """So' calculavel com o PROJETO bruto (score.json nao guarda a
    contagem por codigo) - por isso, sem `project`, tudo sai
    NOT_AVAILABLE (item 26), nunca zero inventado."""
    if project is None:
        out = {"total_blocks": _na(INFORMATIONAL)}
        for code in KNOWN_BLOCK_CODES:
            out[code] = _na(CONTEXT_DEPENDENT)
        out["outros"] = _na(CONTEXT_DEPENDENT)
        return out

    counts = {}
    total = 0
    for _wall, _row, block in model.iter_blocks(project):
        code = block.get("code") or "?"
        counts[code] = counts.get(code, 0) + 1
        total += 1

    out = {"total_blocks": _metric(total, CONTEXT_DEPENDENT, unit="pecas",
                                   note="quantidade total nao e' automaticamente "
                                        "melhor nem pior (item 12)")}
    for code in KNOWN_BLOCK_CODES:
        out[code] = _metric(counts.get(code, 0), CONTEXT_DEPENDENT, unit="pecas")
    known_total = sum(counts.get(code, 0) for code in KNOWN_BLOCK_CODES)
    out["outros"] = _metric(max(0, total - known_total), CONTEXT_DEPENDENT, unit="pecas")
    return out


# ------------------------------------------------------------- PRISMA
def prism_metrics(score=None, findings=None):
    by_code = _findings_by_code_from(score)
    if by_code is None and findings is not None:
        by_code = _findings_by_code(findings)
    if by_code is None:
        return {
            "alignment_conflicts": _na(LOWER_IS_BETTER),
            "continuous_vertical_joints": _na(LOWER_IS_BETTER),
            "stagger_below_target": _na(INFORMATIONAL),
        }
    return {
        # PRISM_CONTINUOUS_JOINT = a regra #1 (junta corrida entre fiadas
        # consecutivas) - e' o "forbidden joint alignment" do pedido.
        "alignment_conflicts": _metric(
            _code_count(by_code, "PRISM_CONTINUOUS_JOINT"), LOWER_IS_BETTER,
            unit="juntas"),
        "continuous_vertical_joints": _metric(
            _code_count(by_code, "PRISM_JOINT_STACK"), LOWER_IS_BETTER,
            unit="pilhas de juntas"),
        # Nivel 2 (preferencia) - divergir nao e' erro, so' informativo.
        "stagger_below_target": _metric(
            _code_count(by_code, "PRISM_STAGGER_BELOW_TARGET"), INFORMATIONAL,
            unit="juntas"),
    }


# ---------------------------------------------------------- ENCONTROS
def _junction_type_counts(findings, code):
    counts = {"L": 0, "T": 0, "X": 0, "unknown": 0}
    for item in findings or []:
        if item.get("code") != code:
            continue
        jtype = item.get("junction_type")
        if jtype in counts:
            counts[jtype] += 1
        else:
            counts["unknown"] += 1
    return counts


def junction_metrics(score=None, findings=None):
    by_code = _findings_by_code_from(score)
    if by_code is None and findings is not None:
        by_code = _findings_by_code(findings)

    missing_binding = _code_count(by_code, "JUNCTION_MISSING_BINDING") if by_code is not None else None
    not_alternating = _code_count(by_code, "JUNCTION_NOT_ALTERNATING") if by_code is not None else None
    half_block_adjacent = _code_count(by_code, "JUNCTION_HALF_BLOCK_ADJACENT") if by_code is not None else None

    out = {
        "missing_binding": _metric(missing_binding, LOWER_IS_BETTER, unit="encontros"),
        "degraded_intersections": _metric(not_alternating, LOWER_IS_BETTER, unit="encontros"),
        "half_block_adjacent_to_binding": _metric(half_block_adjacent, LOWER_IS_BETTER, unit="ocorrencias"),
    }

    # Quebra por tipo (L/T/X) so' e' possivel com a lista de FINDINGS (o
    # score.json agregado nao guarda `junction_type`) - degrada com
    # honestidade quando so' o score esta' disponivel (item 26).
    if findings is not None:
        for target_code, label in (
            ("JUNCTION_MISSING_BINDING", "missing_binding_by_type"),
            ("JUNCTION_NOT_ALTERNATING", "degraded_by_type"),
        ):
            by_type = _junction_type_counts(findings, target_code)
            for jtype in ("L", "T", "X"):
                out["{0}_{1}".format(label, jtype)] = _metric(
                    by_type[jtype], LOWER_IS_BETTER, unit="encontros")
    else:
        for label in ("missing_binding_by_type", "degraded_by_type"):
            for jtype in ("L", "T", "X"):
                out["{0}_{1}".format(label, jtype)] = _na(
                    LOWER_IS_BETTER,
                    note="precisa da lista de findings (nao so' do score) para quebrar por tipo")
    return out


# ----------------------------------------------------------- ABERTURAS
def opening_metrics(score=None, findings=None):
    by_code = _findings_by_code_from(score)
    if by_code is None and findings is not None:
        by_code = _findings_by_code(findings)
    if by_code is None:
        by_code = {}
        available = False
    else:
        available = True

    def m(code, direction, unit="ocorrencias"):
        if not available:
            return _na(direction)
        return _metric(_code_count(by_code, code), direction, unit=unit)

    return {
        "blocks_inside_door": m("OPENING_BLOCK_INSIDE_DOOR", LOWER_IS_BETTER, unit="blocos"),
        "blocks_inside_window": m("OPENING_BLOCK_INSIDE_WINDOW", LOWER_IS_BETTER, unit="blocos"),
        "blocks_crossing_jamb": m("OPENING_BLOCK_CROSSES_JAMB", LOWER_IS_BETTER, unit="blocos"),
        "missing_lintel": m("OPENING_MISSING_LINTEL", LOWER_IS_BETTER, unit="vaos"),
        "missing_counter_lintel": m("OPENING_MISSING_COUNTER_LINTEL", LOWER_IS_BETTER, unit="vaos"),
        "solid_below_sill_missing": m("OPENING_SOLID_BELOW_SILL_MISSING", LOWER_IS_BETTER, unit="fiadas"),
    }


# ------------------------------------------------------------ QUALIDADE
def quality_metrics(score=None, findings=None):
    by_code = _findings_by_code_from(score)
    if by_code is None and findings is not None:
        by_code = _findings_by_code(findings)
    if by_code is None:
        by_code = {}
        available = False
    else:
        available = True

    def m(code, direction, unit="ocorrencias"):
        if not available:
            return _na(direction)
        return _metric(_code_count(by_code, code), direction, unit=unit)

    return {
        "collisions": m("POSITION_OVERLAP", LOWER_IS_BETTER, unit="colisoes"),
        "non_modular_walls": m("COVERAGE_WALL_NOT_MODULATED", LOWER_IS_BETTER, unit="paredes"),
        "consecutive_compensators": m("COMPENSATOR_CONSECUTIVE", LOWER_IS_BETTER, unit="ocorrencias"),
        "compensator_excess_in_run": m("COMPENSATOR_EXCESS_IN_RUN", LOWER_IS_BETTER, unit="trechos"),
        "avoidable_compensators": m("COMPENSATOR_AVOIDABLE", INFORMATIONAL, unit="ocorrencias"),
        "orphan_blocks": m("COVERAGE_ORPHAN_BLOCKS", LOWER_IS_BETTER, unit="blocos"),
        "critical_errors_total": _metric(
            score.get("critical_errors") if score is not None else None,
            LOWER_IS_BETTER, unit="ocorrencias"),
    }


# ---------------------------------------------------------- PERFORMANCE
def performance_metrics(timing_seconds=None, by_stage_seconds=None):
    """So' preenchido quando quem chama MEDIU o tempo (item 10:
    'performance... quando os dados existirem'). Este modulo nunca cronometra
    nada sozinho."""
    out = {
        "runtime_seconds": (
            _metric(round(float(timing_seconds), 3), LOWER_IS_BETTER, unit="s")
            if timing_seconds is not None else _na(LOWER_IS_BETTER)
        ),
    }
    if by_stage_seconds:
        for stage, seconds in sorted(by_stage_seconds.items()):
            out["stage_{0}_seconds".format(stage)] = _metric(
                round(float(seconds), 3), LOWER_IS_BETTER, unit="s")
    return out


# ---------------------------------------------------------------- tudo
CATEGORY_BUILDERS = (
    "walls", "courses", "blocks", "prism", "junctions", "openings",
    "quality", "performance",
)


def compute_metrics(project=None, score=None, findings=None,
                    timing_seconds=None, by_stage_seconds=None):
    """Monta o bundle inteiro de metricas (item 10). Todo argumento e'
    OPCIONAL - o que faltar sai NOT_AVAILABLE, nunca inventado (item 26).

    `project`: dict formato `benchmark/model.py` (result.json/reference.json).
    `score`: saida de `benchmark.scoring.score_project` (ou um
        `score.json`/`baseline.json` lido do disco - o mesmo formato).
    `findings`: lista de achados (`findings.json`) - habilita a quebra por
        tipo de encontro (L/T/X) que o score sozinho nao carrega.
    """
    return {
        "walls": wall_metrics(project=project, score=score),
        "courses": course_metrics(project=project, score=score),
        "blocks": block_metrics(project=project),
        "prism": prism_metrics(score=score, findings=findings),
        "junctions": junction_metrics(score=score, findings=findings),
        "openings": opening_metrics(score=score, findings=findings),
        "quality": quality_metrics(score=score, findings=findings),
        "performance": performance_metrics(timing_seconds=timing_seconds,
                                           by_stage_seconds=by_stage_seconds),
    }


def critical_invariant_codes():
    """CRITICAL_INVARIANT (item 14) - NAO inventado aqui: e' exatamente a
    lista de classes de erro que `validators/base.py` ja marca
    `SEVERITY_CRITICAL`, que por sua vez cita a secao do
    REGRAS_MODULACAO_BLOCOS.md de onde cada uma vem."""
    return sorted(
        code for code, klass in validators_base.ERROR_CLASS_BY_CODE.items()
        if klass.severity == validators_base.SEVERITY_CRITICAL
    )
