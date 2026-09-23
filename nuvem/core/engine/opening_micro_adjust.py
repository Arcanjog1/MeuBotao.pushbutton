# -*- coding: utf-8 -*-
"""MICROAJUSTE DA POSICAO DA ABERTURA (secao 66, 2026-09-15) - ETAPA 3B.

A posicao longitudinal de uma abertura na propria parede NAO e' absoluta: quando
ela deixa entre a amarracao (peca de no') e a jamba um trecho que nenhuma peca
inteira fecha, a fiada e' obrigada a usar peca de acerto (compensador, pastilha
ou meio bloco) e o padrao vertical da banda quebra ali.

Caso REAL medido na BUTANTA (parede 8284543, porta 8079002, jamba em t=469 cm):

    fiada par   B54(no')@385 | C09@440 B19@450 | VAO          <- 30 cm de sobra
    fiada impar B39@420      | C09@460         | VAO

    com a abertura 5 cm adiante (jamba em 474):
    fiada par   B54(no')@385 | B34@440         | VAO          <- 35 cm: cabe B34
    fiada impar B34@420      | B19@455         | VAO

Este modulo SO' PLANEJA: enumera os deslocamentos possiveis (ate'
`MICRO_ADJUST_MAX_CM`, passo `MICRO_ADJUST_STEP_CM`), pede ao chamador que
avalie cada um com um solve REAL da regiao afetada e escolhe. Nada aqui move
abertura, toca no Revit ou altera largura/altura/peitoril/nivel.

Regras do usuario (2026-09-15) que estao codificadas aqui:
  - teto de 10 cm para cada lado, menor deslocamento primeiro, e o offset 0
    vence qualquer empate (`nao mover sem ganho real`);
  - portoes duros primeiro (nada dentro do vao, sem colisao, apoio, amarracao,
    prisma, no'|fill, fill|tie, CHANNEL); so' depois qualidade;
  - qualidade na ordem: vazado menor -> padrao vertical -> meio bloco
    desnecessario -> compensador/pastilha -> aglomerado de especiais ->
    nao modular;
  - o cluster manda: a parede da abertura E as paredes ligadas a ela;
  - nunca recentralizar: simetria nao e' criterio.
"""
import collections

from core.engine import small_void_alignment as _sva
from core.engine.modulation_math import (BLOCK_OPENING_JOINT_CM,
                                         pier_closes_with_blocks_cm)
from core.engine.wall_stepper import (_candidate_extent_on_wall_axis, _ft_to_cm,
                                      _wall_axis_and_length)

OPENING_MICRO_ADJUST_ENABLED = True
# Teto pedido pelo usuario (2026-09-15). O teto ANTIGO da Etapa 3B para
# fechar parede nao modular continua em AXIS_OPENING_SHIFT_MAX_CM = 5 cm: sao
# capacidades diferentes (aquela resolve INVIABILIDADE, esta resolve
# QUALIDADE) e cada uma tem o seu limite.
MICRO_ADJUST_MAX_CM = 10.0
MICRO_ADJUST_STEP_CM = 1.0
# Seguranca (secao 10 do pedido): a abertura nunca sai da parede, nunca encosta
# noutra abertura e nunca chega perto demais de um no'.
MICRO_ADJUST_WALL_EDGE_MIN_CM = 5.0
MICRO_ADJUST_OPENING_GAP_MIN_CM = 10.0
MICRO_ADJUST_NODE_CLEARANCE_CM = 5.0
# Teto de aberturas examinadas por execucao (a busca custa um solve do cluster
# por offset candidato).
MICRO_ADJUST_MAX_OPENINGS = 24

FILLER_MAX_LENGTH_CM = 20.0   # compensador, pastilha e meio bloco
STRIP_MAX_CM = 120.0          # trecho no' -> jamba que ainda e' "a faixa da amarracao"


def _extent(cand, p0, direction):
    return _candidate_extent_on_wall_axis(cand, p0, direction)


def _is_filler(cand, catalog):
    """Peca de ACERTO: compensador/pastilha (catalogo) ou meio bloco - a peca
    que existe para fechar a conta, nao para construir a parede."""
    code = cand.get("logical_code")
    entry = (catalog or {}).get(code) or {}
    if entry.get("is_compensator"):
        return True
    length = entry.get("length_cm") or cand.get("length_cm") or 0.0
    return bool(length) and length <= FILLER_MAX_LENGTH_CM


def strip_filler_pieces(course_candidates, wall_idx, walls_to_create, openings_cm, catalog,
                        max_course=None):
    """PADRAO VERTICAL (prioridade 10): pecas de acerto dentro das faixas entre
    uma peca de NO' e a jamba mais proxima, somadas em todas as fiadas.

    E' geometria, nao nome de peca: a faixa entre a amarracao e o vao deveria
    fechar com alvenaria inteira; cada compensador/pastilha/meio bloco ali e' o
    padrao da banda interrompido. Deslocar a abertura muda o comprimento da
    faixa e, com ele, o que cabe nela."""
    p0, _p1, direction, _len_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
    total = 0
    for course in sorted(course_candidates or {}):
        if max_course is not None and course > max_course:
            continue
        row = []
        for cand in course_candidates[course] or ():
            if cand.get("wall_idx") != wall_idx:
                continue
            lo, hi = _extent(cand, p0, direction)
            row.append((lo, hi, cand))
        row.sort()
        anchors = [(lo, hi) for lo, hi, cand in row if cand.get("node_index") is not None]
        if not anchors:
            continue
        for t_lo, t_hi in openings_cm:
            for anchor_lo, anchor_hi in anchors:
                if anchor_hi <= t_lo:
                    a, b = anchor_hi, t_lo         # faixa a' esquerda do vao
                elif anchor_lo >= t_hi:
                    a, b = t_hi, anchor_lo         # faixa a' direita do vao
                else:
                    continue
                if not (0.0 < b - a <= STRIP_MAX_CM):
                    continue
                for lo, hi, cand in row:
                    if lo >= a - 0.5 and hi <= b + 0.5 and _is_filler(cand, catalog):
                        total += 1
    return total


def detect_candidates(course_candidates, walls_to_create, openings_per_wall, catalog,
                      max_course=None):
    """OPENING_MICRO_ADJUSTMENT_REQUIRED: aberturas cuja vizinhanca mostra o
    defeito que um deslocamento pode resolver. Diagnostico, nunca erro."""
    violations = _sva.b34_small_void_violations(course_candidates, catalog)
    near = collections.Counter()
    for item in violations:
        wall_idx = item.get("wall_idx")
        if wall_idx is None:
            continue
        near[wall_idx] += 1
    out = []
    for wall_idx, openings in enumerate(openings_per_wall or ()):
        if not openings:
            continue
        _p0, _p1, _d, length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
        for opening_index, opening in enumerate(openings):
            span = (_cm(opening[0]), _cm(opening[1]))
            fillers = strip_filler_pieces(course_candidates, wall_idx, walls_to_create,
                                          [span], catalog, max_course=max_course)
            reasons = []
            if fillers:
                reasons.append("pecas de acerto na faixa amarracao->jamba: %d" % fillers)
            if near.get(wall_idx):
                reasons.append("vazado menor desalinhado na parede: %d" % near[wall_idx])
            if reasons:
                out.append({"wall_idx": wall_idx, "opening_index": opening_index,
                            "span_cm": [round(span[0], 1), round(span[1], 1)],
                            "strip_fillers": fillers, "reasons": reasons})
    out.sort(key=lambda item: (-item["strip_fillers"], item["wall_idx"], item["opening_index"]))
    return out[:MICRO_ADJUST_MAX_OPENINGS]


def _cm(value_ft):
    return _ft_to_cm(value_ft)


def feasible_offsets(opening_span_cm, other_openings_cm, wall_length_cm, node_positions_cm,
                     max_cm=None, step_cm=None, already_moved_cm=0.0):
    """Deslocamentos permitidos, do MENOR para o maior (empate: para a frente).
    Recusa o que sai da parede, encosta noutra abertura ou chega perto de no'.

    `already_moved_cm` e' o quanto esta abertura JA' saiu da posicao original do
    projeto: o teto de MICRO_ADJUST_MAX_CM vale para o deslocamento TOTAL, nunca
    por execucao - sem isso a abertura passearia 10 cm a cada rodada."""
    max_cm = MICRO_ADJUST_MAX_CM if max_cm is None else max_cm
    step_cm = MICRO_ADJUST_STEP_CM if step_cm is None else step_cm
    t_lo, t_hi = opening_span_cm
    out = [0.0]
    steps = int(round(max_cm / step_cm))
    for k in range(1, steps + 1):
        for sign in (1.0, -1.0):
            delta = sign * k * step_cm
            if abs(already_moved_cm + delta) > max_cm + 1e-9:
                continue
            lo, hi = t_lo + delta, t_hi + delta
            if lo < MICRO_ADJUST_WALL_EDGE_MIN_CM or hi > wall_length_cm - MICRO_ADJUST_WALL_EDGE_MIN_CM:
                continue
            if any(hi > o_lo - MICRO_ADJUST_OPENING_GAP_MIN_CM and lo < o_hi + MICRO_ADJUST_OPENING_GAP_MIN_CM
                   for o_lo, o_hi in other_openings_cm):
                continue
            if any(abs(lo - t) < MICRO_ADJUST_NODE_CLEARANCE_CM or abs(hi - t) < MICRO_ADJUST_NODE_CLEARANCE_CM
                   for t in (node_positions_cm or ())):
                continue
            out.append(round(delta, 3))
    return out


def piers_close(opening_span_cm, other_openings_cm, wall_length_cm):
    """PRE-TRIAGEM ARITMETICA (a mesma da Etapa 3B): os dois pilaretes deste vao
    fecham com blocos nesta posicao? E' condicao NECESSARIA - sem ela o solver
    real deixa a parede NAO MODULAR, e nao adianta gastar um solve para
    descobrir. As duas bordas do pilarete que interessam aqui sao faces (jamba
    do vao, face de no' ou ponta), com junta de contorno
    BLOCK_OPENING_JOINT_CM. Medido na BUTANTA: sobrevivem os deslocamentos
    multiplos do modulo (PIER_MODULE_CM = 5 cm, o mdc de bloco+junta)."""
    t_lo, t_hi = opening_span_cm
    bounds = [0.0, wall_length_cm]
    for o_lo, o_hi in other_openings_cm or ():
        bounds.extend([o_lo, o_hi])
    left_edge = max([b for b in bounds if b <= t_lo + 1e-6] or [0.0])
    right_edge = min([b for b in bounds if b >= t_hi - 1e-6] or [wall_length_cm])
    joint = BLOCK_OPENING_JOINT_CM
    return (pier_closes_with_blocks_cm(t_lo - left_edge, joint, joint)
            and pier_closes_with_blocks_cm(right_edge - t_hi, joint, joint))


QUALITY_ORDER = ("small_void", "strip_fillers", "mid_wall_half_blocks", "specials",
                 "special_clusters", "non_modular")


def _worse_gates(after, before):
    for key, value in (after or {}).items():
        if value > (before or {}).get(key, 0):
            return True
    return False


def _quality_tuple(quality):
    return tuple((quality or {}).get(key, 0) for key in QUALITY_ORDER)


def choose_offset(candidate, evaluate, offsets, verify=None):
    """Avalia cada offset com `evaluate(offset) -> {"gates": {...},
    "quality": {...}}` e devolve o vencedor. O offset 0 e' a referencia: um
    deslocamento so' vence se NENHUM portao piorar e a qualidade for
    ESTRITAMENTE melhor; empate fica com o menor deslocamento (logo, com 0).

    `verify(offset)`, quando dado, e' a avaliacao CARA (o fluxo completo): o
    ranking usa a barata e o VENCEDOR e' confirmado com ela antes de virar
    plano. Sem a confirmacao, um deslocamento que so' parece melhor no modelo
    barato entraria no modelo real - medido: 2 de 3 propostas caem aqui."""
    base = evaluate(0.0)
    if base is None:
        return None
    best = {"offset_cm": 0.0, "gates": base["gates"], "quality": base["quality"]}
    best_key = _quality_tuple(base["quality"])
    tried = [{"offset_cm": 0.0, "gates": base["gates"], "quality": base["quality"]}]
    for offset in offsets:
        if offset == 0.0:
            continue
        result = evaluate(offset)
        if result is None:
            continue
        tried.append({"offset_cm": offset, "gates": result["gates"], "quality": result["quality"]})
        if _worse_gates(result["gates"], base["gates"]):
            continue
        key = _quality_tuple(result["quality"])
        if key < best_key:
            best, best_key = {"offset_cm": offset, "gates": result["gates"],
                              "quality": result["quality"]}, key
    confirmed = None
    if verify is not None and best["offset_cm"] != 0.0:
        exact_base = verify(0.0)
        exact_best = verify(best["offset_cm"])
        confirmed = {"offset_cm": best["offset_cm"], "before": exact_base, "after": exact_best}
        if (exact_base is None or exact_best is None
                or _worse_gates(exact_best["gates"], exact_base["gates"])
                or not _quality_tuple(exact_best["quality"]) < _quality_tuple(exact_base["quality"])):
            confirmed["rejected"] = True
            best = {"offset_cm": 0.0, "gates": exact_base["gates"] if exact_base else base["gates"],
                    "quality": exact_base["quality"] if exact_base else base["quality"]}
        else:
            tried[0] = {"offset_cm": 0.0, "gates": exact_base["gates"], "quality": exact_base["quality"]}
            best = {"offset_cm": best["offset_cm"], "gates": exact_best["gates"],
                    "quality": exact_best["quality"]}
    return {"wall_idx": candidate["wall_idx"], "opening_index": candidate["opening_index"],
            "span_cm": candidate["span_cm"], "reasons": candidate["reasons"],
            "chosen_offset_cm": best["offset_cm"], "before": tried[0], "after": best,
            "tried": tried, "confirmed": confirmed, "applied": best["offset_cm"] != 0.0}


def plan_micro_adjustments(course_candidates, walls_to_create, openings_per_wall, catalog,
                           evaluate, node_positions_by_wall=None, max_course=None,
                           max_openings=None, moved_so_far_cm=None, offset_allowed=None):
    """ETAPA 3B - microajuste de posicao por QUALIDADE.

    1. detecta as aberturas com o defeito (OPENING_MICRO_ADJUSTMENT_REQUIRED);
    2. enumera os deslocamentos seguros, passa a pre-triagem aritmetica e, quando
       o chamador da' `offset_allowed(wall_idx, opening_index, offset_cm)`, a
       GUARDA DE INTERFERENCIA do modelo (varredura da abertura ate' a posicao
       final contra os elementos reais - so' o chamador enxerga o Revit);
    3. manda o chamador avaliar cada um com um solve REAL da regiao afetada
       (`evaluate(wall_idx, opening_index, offset_cm)` -> {"gates", "quality"});
    4. escolhe o melhor - empate fica com o menor deslocamento, e o 0 vence
       qualquer empate (`nao mover sem ganho real`).

    Nao move nada: devolve o plano para o chamador aplicar (no planejamento e,
    depois, no Revit)."""
    if not OPENING_MICRO_ADJUST_ENABLED:
        return {"enabled": False, "required": [], "records": [], "applied": [],
                "counts": {"OPENING_MICRO_ADJUSTMENT_REQUIRED": 0, "OPENING_MICRO_ADJUSTMENT_APPLIED": 0}}
    required = detect_candidates(course_candidates, walls_to_create, openings_per_wall, catalog,
                                 max_course=max_course)
    limit = MICRO_ADJUST_MAX_OPENINGS if max_openings is None else max_openings
    records = []
    for candidate in required[:limit]:
        wall_idx = candidate["wall_idx"]
        _p0, _p1, _d, length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
        wall_length_cm = _ft_to_cm(length_ft)
        spans = [(_cm(o[0]), _cm(o[1])) for o in openings_per_wall[wall_idx]]
        span = spans[candidate["opening_index"]]
        others = [s for i, s in enumerate(spans) if i != candidate["opening_index"]]
        moved = (moved_so_far_cm or {}).get((wall_idx, candidate["opening_index"]), 0.0)
        offsets = feasible_offsets(span, others, wall_length_cm,
                                   (node_positions_by_wall or {}).get(wall_idx),
                                   already_moved_cm=moved)
        offsets = [d for d in offsets if piers_close((span[0] + d, span[1] + d), others, wall_length_cm)]
        if offset_allowed is not None:
            blocked = [d for d in offsets if d and not offset_allowed(wall_idx, candidate["opening_index"], d)]
            if blocked:
                candidate["blocked_offsets_cm"] = sorted(blocked)
            offsets = [d for d in offsets if d not in blocked]
        if len(offsets) <= 1:
            continue          # so' a posicao atual fecha: nada a decidir
        opening_index = candidate["opening_index"]
        record = choose_offset(
            candidate, lambda offset: evaluate(wall_idx, opening_index, offset, False), offsets,
            verify=lambda offset: evaluate(wall_idx, opening_index, offset, True))
        if record is not None:
            records.append(record)
    applied = [r for r in records if r["applied"]]
    return {"enabled": True, "required": required, "records": records, "applied": applied,
            "counts": {"OPENING_MICRO_ADJUSTMENT_REQUIRED": len(required),
                       "OPENING_MICRO_ADJUSTMENT_APPLIED": len(applied)}}


def mid_wall_half_blocks(course_candidates, walls_to_create, openings_per_wall, catalog,
                         half_block_code=None, near_cm=2.0, max_course=None):
    """MEIO BLOCO DESNECESSARIO (prioridade 11): meio bloco que nao encosta em
    jamba, nem em ponta de parede, nem em peca de no'. O humano usa meio bloco
    MAIS que o solver (secao 56.3), entao isto e' preferencia de qualidade, nunca
    portao."""
    from core.engine.wall_stepper import HALF_BLOCK_CODE
    code_wanted = half_block_code or HALF_BLOCK_CODE
    total = 0
    for course in sorted(course_candidates or {}):
        if max_course is not None and course > max_course:
            continue
        by_wall = {}
        for cand in course_candidates[course] or ():
            wall_idx = cand.get("wall_idx")
            if wall_idx is None or wall_idx >= len(walls_to_create or ()):
                continue
            by_wall.setdefault(wall_idx, []).append(cand)
        for wall_idx, cands in by_wall.items():
            p0, _p1, direction, length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
            length_cm = _ft_to_cm(length_ft)
            edges = []
            for opening in (openings_per_wall[wall_idx] if wall_idx < len(openings_per_wall or ()) else ()):
                edges.extend([_cm(opening[0]), _cm(opening[1])])
            spans = []
            for cand in cands:
                lo, hi = _extent(cand, p0, direction)
                spans.append((lo, hi, cand))
            spans.sort()
            for index, (lo, hi, cand) in enumerate(spans):
                if cand.get("logical_code") != code_wanted or cand.get("node_index") is not None:
                    continue
                if any(abs(lo - edge) <= near_cm or abs(hi - edge) <= near_cm for edge in edges):
                    continue
                if lo <= near_cm or hi >= length_cm - near_cm:
                    continue
                neighbours = []
                if index:
                    neighbours.append(spans[index - 1][2])
                if index + 1 < len(spans):
                    neighbours.append(spans[index + 1][2])
                if any(other.get("node_index") is not None for other in neighbours):
                    continue
                total += 1
    return total


def special_clusters(course_candidates, walls_to_create, catalog, window_cm=40.0, max_course=None):
    """AGLOMERADO DE ESPECIAIS (prioridade 13): pares de compensador/pastilha a
    menos de `window_cm` um do outro na mesma fiada."""
    total = 0
    for course in sorted(course_candidates or {}):
        if max_course is not None and course > max_course:
            continue
        by_wall = {}
        for cand in course_candidates[course] or ():
            wall_idx = cand.get("wall_idx")
            if wall_idx is None or wall_idx >= len(walls_to_create or ()):
                continue
            if not ((catalog or {}).get(cand.get("logical_code")) or {}).get("is_compensator"):
                continue
            by_wall.setdefault(wall_idx, []).append(cand)
        for wall_idx, cands in by_wall.items():
            p0, _p1, direction, _length_ft, _t = _wall_axis_and_length(walls_to_create, wall_idx)
            centres = sorted(sum(_extent(cand, p0, direction)) / 2.0 for cand in cands)
            for a, b in zip(centres, centres[1:]):
                if b - a <= window_cm:
                    total += 1
    return total
