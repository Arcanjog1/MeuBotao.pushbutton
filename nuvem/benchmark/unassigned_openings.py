# -*- coding: utf-8 -*-
"""Auditoria das aberturas que a FASE A NAO conseguiu atribuir a parede.

Etapa 2B.1, item 9. Das 91 aberturas do documento INPUT, 82 foram
atribuidas a uma parede e 9 ficaram de fora. "9 nao atribuidas" sozinho nao
diz nada: pode ser abertura em regiao que a pessoa nem modulou, pode ser
parede que o Wall Modeling deixou de formar, pode ser a atribuicao
rejeitando uma parede que existe. Este modulo separa os casos, com numero
medido em cada um.

NAO corrige nada - nem o Wall Modeling, nem o solver. So' classifica.

Os dois motivos de rejeicao sao os de
`core/engine/wall_pairing.py::assign_openings_to_walls`, reproduzidos aqui
com as MESMAS constantes (lidas do motor, nunca copiadas como numero):

  1. `perp_dist > thickness/2 + OPENING_ASSOC_TOLERANCE_FT`
     -> nenhuma parede perto o bastante do centro do vao;
  2. `t_hi - t_lo <= MIN_SEGMENT_LENGTH_FT`
     -> ha' parede perto, mas o vao cai fora do TRECHO dela.

Classificacao devolvida em `classification`:

  OUTSIDE_EVALUATION_SCOPE - a abertura esta' fora da regiao onde existe
      modulacao humana. Nao ha' gabarito para dizer que faltou parede.
  INPUT_EXPECTED_NO_WALL   - dentro do escopo, mas nao ha' eixo de gabarito
      nem linha de CAD pareavel por perto: o proprio input nao pede parede
      ali.
  WALL_MODELING_ERROR      - ha' eixo de gabarito humano no lugar (a pessoa
      construiu parede ali) mas o Wall Modeling nao formou parede nenhuma
      perto. A falha e' de FASE A.
  OPENING_ASSIGNMENT_ERROR - existe parede formada, dentro da distancia
      perpendicular, mas a abertura foi recusada por cair fora do trecho.
  AMBIGUOUS                - nenhuma das anteriores fecha com folga.
"""

import datetime
import math

# Fracao do vao que precisa cair sobre o eixo do gabarito para dizer "a
# pessoa construiu parede aqui". Metade e' o suficiente: uma abertura de
# porta encostada no fim de uma parede humana ainda conta.
GABARITO_HIT_TOLERANCE_CM = 20.0


def _project(px, py, x0, y0, x1, y1):
    """`(t, perp_dist, length)` do ponto sobre o segmento (t NAO e'
    grampeado - o sinal e o excesso dizem se caiu fora do trecho)."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return 0.0, math.hypot(px - x0, py - y0), 0.0
    ux, uy = dx / length, dy / length
    t = (px - x0) * ux + (py - y0) * uy
    perp = abs(-(px - x0) * uy + (py - y0) * ux)
    return t, perp, length


def _interval_on_wall(opening, wall):
    """Intervalo [t_lo, t_hi] do vao projetado no eixo, JA grampeado ao
    trecho da parede - mesma conta de `_project_opening_on_line`."""
    cx, cy = opening["center_cm"]
    x0, y0 = wall["start_cm"]
    x1, y1 = wall["end_cm"]
    t, perp, length = _project(cx, cy, x0, y0, x1, y1)
    half = float(opening["width_cm"]) / 2.0
    t_lo = max(0.0, t - half)
    t_hi = min(length, t + half)
    return t_lo, t_hi, perp, length


def audit(snapshot, scope=None, reference=None, input_real=None,
          engine_module=None):
    """Devolve o relatorio das aberturas nao atribuidas.

    `engine_module` (opcional) e' o motor real, de onde saem
    `OPENING_ASSOC_TOLERANCE_FT`/`MIN_SEGMENT_LENGTH_FT`/`FEET_PER_METER`.
    Sem ele, os valores documentados sao usados e isso fica registrado em
    `tolerances.source`."""
    if engine_module is not None:
        feet_per_meter = engine_module.FEET_PER_METER
        assoc_tolerance_cm = (engine_module.OPENING_ASSOC_TOLERANCE_FT
                              / feet_per_meter * 100.0)
        min_segment_cm = (engine_module.MIN_SEGMENT_LENGTH_FT
                          / feet_per_meter * 100.0)
        tolerance_source = "motor real (core/engine/tolerances.py)"
    else:
        assoc_tolerance_cm = 5.0
        min_segment_cm = 1.0
        tolerance_source = "valores documentados (motor nao carregado)"

    walls = snapshot.get("walls") or []
    diagnostics = (snapshot.get("diagnostics") or {}).get("openings") or {}
    unassigned = diagnostics.get("unassigned_openings") or []

    reference_axes = [
        (w["start_cm"][0], w["start_cm"][1], w["end_cm"][0], w["end_cm"][1])
        for w in ((reference or {}).get("walls") or [])
    ]
    cad_segments = [
        s for s in ((input_real or {}).get("segments") or [])
    ]

    scope_cells = None
    scope_cell_cm = None
    if scope is not None:
        scope_cells = set((int(a), int(b)) for a, b in scope["cells"])
        scope_cell_cm = float(scope["params"]["cell_cm"])

    records = []
    for opening in unassigned:
        cx, cy = opening["center_cm"]

        # --- paredes formadas candidatas -------------------------------
        # `interval_width_cm` NEGATIVO quer dizer que o vao projeta FORA do
        # trecho da parede - o valor e' o quanto ele passa do fim dela.
        nearest = None
        best_eligible = None
        candidates_within_perp = 0
        for index, wall in enumerate(walls):
            t_lo, t_hi, perp, _length = _interval_on_wall(opening, wall)
            max_perp = float(wall["thickness_cm"]) / 2.0 + assoc_tolerance_cm
            candidate = {
                "wall_index": index,
                "wall_key": wall.get("key"),
                "perp_dist_cm": round(perp, 3),
                "max_perp_allowed_cm": round(max_perp, 3),
                "interval_cm": [round(t_lo, 3), round(t_hi, 3)],
                "interval_width_cm": round(t_hi - t_lo, 3),
                "within_perp": perp <= max_perp,
                "interval_ok": (t_hi - t_lo) > min_segment_cm,
            }
            if nearest is None or perp < nearest["perp_dist_cm"]:
                nearest = candidate
            if not candidate["within_perp"]:
                continue
            candidates_within_perp += 1
            # Entre as que passam na distancia perpendicular, a MELHOR e' a
            # que cobre mais do vao - nao a mais proxima. Uma parede pode
            # estar a 0,2cm do eixo e ainda assim terminar 12m antes do vao
            # (fragmentacao), enquanto outra, um pouco mais longe, o cobre.
            if (best_eligible is None
                    or candidate["interval_width_cm"] > best_eligible["interval_width_cm"]):
                best_eligible = candidate

        # --- eixo do gabarito por baixo? -------------------------------
        gabarito_dist = None
        for ax0, ay0, ax1, ay1 in reference_axes:
            _t, perp, length = _project(cx, cy, ax0, ay0, ax1, ay1)
            t_clamped = max(0.0, min(length, _t))
            distance = math.hypot(
                cx - (ax0 + (ax1 - ax0) * (t_clamped / length if length else 0.0)),
                cy - (ay0 + (ay1 - ay0) * (t_clamped / length if length else 0.0)))
            if gabarito_dist is None or distance < gabarito_dist:
                gabarito_dist = distance
        has_gabarito_axis = (gabarito_dist is not None
                             and gabarito_dist <= GABARITO_HIT_TOLERANCE_CM)

        # --- linhas de CAD por perto -----------------------------------
        cad_near = 0
        cad_min_dist = None
        for segment in cad_segments:
            sx, sy = segment["start"]
            ex, ey = segment["end"]
            _t, _perp, length = _project(cx, cy, sx, sy, ex, ey)
            t_clamped = max(0.0, min(length, _t))
            distance = math.hypot(
                cx - (sx + (ex - sx) * (t_clamped / length if length else 0.0)),
                cy - (sy + (ey - sy) * (t_clamped / length if length else 0.0)))
            if distance <= 100.0:
                cad_near += 1
            if cad_min_dist is None or distance < cad_min_dist:
                cad_min_dist = distance

        # --- dentro do evaluation_scope? -------------------------------
        in_scope = None
        if scope_cells is not None:
            in_scope = (int(math.floor(cx / scope_cell_cm)),
                        int(math.floor(cy / scope_cell_cm))) in scope_cells

        # --- classificacao ---------------------------------------------
        if in_scope is False:
            classification = "OUTSIDE_EVALUATION_SCOPE"
            rationale = ("centro do vao cai fora da mascara de ocupacao do "
                         "gabarito - nao ha' modulacao humana nessa regiao "
                         "para dizer que faltou parede")
        elif best_eligible is not None and best_eligible["interval_ok"]:
            # Nao deveria acontecer: se existe parede elegivel que cobre o
            # vao, `assign_openings_to_walls` teria atribuido. Se aparecer,
            # e' de fato defeito da atribuicao.
            classification = "OPENING_ASSIGNMENT_ERROR"
            rationale = ("existe parede elegivel (perp {0:.1f} cm <= {1:.1f}) "
                         "cobrindo {2:.1f} cm do vao, e mesmo assim a abertura "
                         "nao foi atribuida".format(
                             best_eligible["perp_dist_cm"],
                             best_eligible["max_perp_allowed_cm"],
                             best_eligible["interval_width_cm"]))
        elif has_gabarito_axis:
            classification = "WALL_MODELING_ERROR"
            rationale = (
                "a pessoa construiu parede exatamente aqui (eixo do gabarito "
                "a {0:.2f} cm), mas nenhuma parede da FASE A cobre o vao: "
                "{1} parede(s) passam na distancia perpendicular e a melhor "
                "delas cobre {2} cm".format(
                    gabarito_dist, candidates_within_perp,
                    "nenhum" if best_eligible is None
                    else "%.1f" % best_eligible["interval_width_cm"]))
        elif cad_near == 0:
            classification = "INPUT_EXPECTED_NO_WALL"
            rationale = ("nao ha' eixo de gabarito nem linha de CAD a menos "
                         "de 1 m - o proprio input nao pede parede aqui")
        else:
            classification = "AMBIGUOUS"
            rationale = ("ha' linhas de CAD por perto mas nenhum eixo de "
                         "gabarito e nenhuma parede formada elegivel")

        records.append({
            "element_id": opening.get("element_id"),
            "center_cm": opening["center_cm"],
            "bbox_center_cm": opening.get("bbox_center_cm"),
            "width_cm": opening.get("width_cm"),
            "sill_cm": opening.get("sill_cm"),
            "head_cm": opening.get("head_cm"),
            "inside_evaluation_scope": in_scope,
            "nearest_wall": nearest,
            "best_eligible_wall": best_eligible,
            "walls_within_perp_tolerance": candidates_within_perp,
            "nearest_reference_axis_dist_cm": (
                None if gabarito_dist is None else round(gabarito_dist, 2)),
            "has_reference_axis_under_it": has_gabarito_axis,
            "cad_lines_within_100cm": cad_near,
            "nearest_cad_line_dist_cm": (
                None if cad_min_dist is None else round(cad_min_dist, 2)),
            "rejection_reason": (
                "nenhuma parede dentro de thickness/2 + OPENING_ASSOC_TOLERANCE"
                if candidates_within_perp == 0 else
                "ha' parede na distancia perpendicular, mas o vao projeta fora "
                "do trecho de todas elas (t_hi - t_lo <= MIN_SEGMENT_LENGTH)"),
            "classification": classification,
            "rationale": rationale,
        })

    counts = {}
    for record in records:
        counts[record["classification"]] = counts.get(record["classification"], 0) + 1

    return {
        "schema_version": 1,
        "generated_at": datetime.datetime.now().isoformat(),
        "openings_total": len(diagnostics.get("assignments") or []) + len(unassigned),
        "assigned": len(diagnostics.get("assignments") or []),
        "unassigned": len(unassigned),
        "tolerances": {
            "source": tolerance_source,
            "opening_assoc_tolerance_cm": round(assoc_tolerance_cm, 4),
            "min_segment_length_cm": round(min_segment_cm, 4),
            "gabarito_hit_tolerance_cm": GABARITO_HIT_TOLERANCE_CM,
        },
        "counts": counts,
        "note": "auditoria APENAS - nenhuma correcao de Wall Modeling ou de solver",
        "openings": records,
    }
