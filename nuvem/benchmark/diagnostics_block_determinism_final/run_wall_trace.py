# -*- coding: utf-8 -*-
"""INSTRUMENTACAO parede-a-parede (item 11 da missao): para as paredes que
ainda divergem entre `baseline` e uma variante de reversao, grava
geometria fisica, p0/p1 originais, eixo logico usado pelo solver, inicio/
fim de cada trecho, blocos escolhidos, posicoes, codigos, juntas, e a
abertura/regiao de reparo envolvida - dos DOIS lados, para comparacao
direta A->B contra B->A.

    python3 run_wall_trace.py [variant] [project_id]
"""
import sys
import json

import lib_final as F
import variants as V
import run_row_diff as RD


def _wall_key_of(walls, idx):
    return F.L.wall_geom_key(walls, idx)


def trace(project_id, input_project, target_keys):
    """Roda o solver com um espiao em `solve_wall_free_fill` e devolve
    {wall_key: [registros por chamada]}."""
    engine = F.L.engine()
    # `process_walls_one_by_one` e `solve_wall_free_fill` moram em
    # core/engine/wall_stepper.py; `wall_modeling` so' reexporta os nomes por
    # `import *`. O espiao tem que trocar o nome no MODULO DE ORIGEM, senao a
    # chamada interna continua indo para a funcao original.
    stepper = sys.modules[engine.solve_wall_free_fill.__module__]
    original = stepper.solve_wall_free_fill
    captured = {}
    state = {"walls": None}

    def _canon(value_cm, length_cm, reversed_axis):
        return round(length_cm - value_cm, 6) if reversed_axis else round(value_cm, 6)

    def spy(wall_idx, walls_to_create, *args, **kwargs):
        state["walls"] = walls_to_create
        key = _wall_key_of(walls_to_create, wall_idx)
        result = original(wall_idx, walls_to_create, *args, **kwargs)
        if key in target_keys:
            p0, p1, direction, length_ft, _t = engine._wall_axis_and_length(
                walls_to_create, wall_idx)
            c_start, c_end, c_dir, _l, _th = engine.canonical_wall_axis(
                walls_to_create, wall_idx)
            openings = engine.openings_for_wall(args[2] if len(args) > 2 else
                                                kwargs.get("openings_per_wall"), wall_idx)
            length_cm_value = length_ft / engine.FEET_PER_METER * 100.0
            rev = engine.wall_axis_is_reversed(walls_to_create, wall_idx)
            by_end = args[3] if len(args) > 3 else kwargs.get("node_candidates_by_wall_end")
            midspan = args[4] if len(args) > 4 else kwargs.get("node_midspan_by_wall_course")
            captured.setdefault(key, []).append({
                "orientation": engine.classify_wall_orientation(walls_to_create, wall_idx),
                "axis_reversed": engine.wall_axis_is_reversed(walls_to_create, wall_idx),
                "p0_cm": F.L.xyz_to_cm(p0), "p1_cm": F.L.xyz_to_cm(p1),
                "canonical_start_cm": F.L.xyz_to_cm(c_start),
                "canonical_end_cm": F.L.xyz_to_cm(c_end),
                "canonical_dir": (round(c_dir.X, 6), round(c_dir.Y, 6)),
                "length_cm": round(length_ft / engine.FEET_PER_METER * 100.0, 3),
                "openings_cm": [
                    (round(o[0] / engine.FEET_PER_METER * 100.0, 6),
                     round(o[1] / engine.FEET_PER_METER * 100.0, 6))
                    for o in openings],
                # As aberturas no EIXO CANONICO - e' o que o solver de fato
                # enxerga depois de `_canonical_wall_solving_view`. E' esta
                # lista (nao a do eixo de representacao) que precisa bater
                # entre A->B e B->A.
                "canonical_openings_cm": sorted(
                    (round(length_cm_value - o[1] / engine.FEET_PER_METER * 100.0, 6),
                     round(length_cm_value - o[0] / engine.FEET_PER_METER * 100.0, 6))
                    if engine.wall_axis_is_reversed(walls_to_create, wall_idx) else
                    (round(o[0] / engine.FEET_PER_METER * 100.0, 6),
                     round(o[1] / engine.FEET_PER_METER * 100.0, 6))
                    for o in openings),
                "n_candidates": len(result["candidates"]),
                # As RESERVAS de encontro e de meio-de-parede, ja' no eixo
                # canonico - as outras duas entradas reais do preenchimento
                # alem da geometria e das aberturas.
                "node_borders": sorted(
                    ((1 - k[1]) if rev else k[1], k[2],
                     _canon(border, length_cm_value, rev))
                    for k, border in (by_end or {}).items() if k[0] == wall_idx),
                "midspan": sorted(
                    (k[1], sorted((_canon(hi, length_cm_value, rev),
                                    _canon(lo, length_cm_value, rev)) if rev else
                                   (round(lo, 6), round(hi, 6))
                                   for lo, hi in intervals))
                    for k, intervals in (midspan or {}).items() if k[0] == wall_idx),
                "variants_per_course": kwargs.get("variants_per_course"),
                "pieces": sorted(
                    (c["logical_code"],
                     round(F.L.xyz_to_cm(c["origin_world"])[0], 1),
                     round(F.L.xyz_to_cm(c["origin_world"])[1], 1),
                     c["course"], c.get("course_variant"), c.get("placement_reason"))
                    for c in result["candidates"]),
                "non_modular": [
                    {k: (round(v, 2) if isinstance(v, float) else v)
                     for k, v in row.items() if k in
                     ("course", "variant_index", "segment_index", "seg_start_cm",
                      "seg_end_cm", "current_length_cm", "left_kind", "right_kind")}
                    for row in result["non_modular"]],
                "opening_repair_regions": [
                    {k: (round(v, 2) if isinstance(v, float) else v)
                     for k, v in row.items() if isinstance(v, (int, float, str))}
                    for row in (result.get("opening_repair_regions") or [])],
                "opening_cut_removals": [
                    {k: (round(v, 2) if isinstance(v, float) else v)
                     for k, v in row.items() if isinstance(v, (int, float, str))}
                    for row in (result.get("opening_cut_removals") or [])],
            })
        return result

    stepper.solve_wall_free_fill = spy
    try:
        F.run_solver(project_id, input_project=input_project)
    finally:
        stepper.solve_wall_free_fill = original
    return captured


def main():
    variant = sys.argv[1] if len(sys.argv) > 1 else "endpoint_reversal"
    project_id = sys.argv[2] if len(sys.argv) > 2 else F.PRIMARY_PROJECT_ID

    diff_path = F.out_path("out_row_diff_%s_%s.json" % (project_id, variant))
    with open(diff_path, "r", encoding="utf-8") as handle:
        diff = json.load(handle)
    keys = set()
    for layer in ("physical_ties", "physical_standard_fill",
                  "physical_opening_repair_fill"):
        for blob in diff["layers"][layer]["walls_touched"]:
            keys.add(tuple(json.loads(blob)))
    print("paredes divergentes:", len(keys))

    base_project = F.load_input(project_id)
    base = trace(project_id, base_project, keys)
    var = trace(project_id, RD.VARIANT_BUILDERS[variant](base_project), keys)

    report = {"variant": variant, "project_id": project_id, "walls": []}
    for key in sorted(keys):
        b = base.get(key) or []
        v = var.get(key) or []
        entry = {"wall_key": list(key), "n_calls_base": len(b), "n_calls_variant": len(v),
                 "calls": []}
        for call_index in range(min(len(b), len(v))):
            bc, vc = b[call_index], v[call_index]
            only_b = [p for p in bc["pieces"] if p not in set(map(tuple, vc["pieces"]))]
            only_v = [p for p in vc["pieces"] if p not in set(map(tuple, bc["pieces"]))]
            entry["calls"].append({
                "call_index": call_index,
                "pieces_equal": bc["pieces"] == vc["pieces"],
                "n_pieces_base": len(bc["pieces"]), "n_pieces_variant": len(vc["pieces"]),
                "openings_equal": bc["canonical_openings_cm"] == vc["canonical_openings_cm"],
                "max_opening_delta_cm": (
                    max([max(abs(a[0] - b[0]), abs(a[1] - b[1]))
                         for a, b in zip(bc["canonical_openings_cm"],
                                          vc["canonical_openings_cm"])] or [0.0])
                    if len(bc["canonical_openings_cm"]) == len(vc["canonical_openings_cm"])
                    else None),
                "base_canonical_openings_cm": bc["canonical_openings_cm"],
                "variant_canonical_openings_cm": vc["canonical_openings_cm"],
                "node_borders_equal": bc["node_borders"] == vc["node_borders"],
                "midspan_equal": bc["midspan"] == vc["midspan"],
                "base_node_borders": bc["node_borders"],
                "variant_node_borders": vc["node_borders"],
                "base_midspan": bc["midspan"], "variant_midspan": vc["midspan"],
                "base_variants_per_course": bc["variants_per_course"],
                "variant_variants_per_course": vc["variants_per_course"],
                "canonical_axis_equal": (
                    bc["canonical_start_cm"] == vc["canonical_start_cm"]
                    and bc["canonical_dir"] == vc["canonical_dir"]
                    and bc["length_cm"] == vc["length_cm"]),
                "base_openings_cm": bc["openings_cm"],
                "variant_openings_cm": vc["openings_cm"],
                "base_axis_reversed": bc["axis_reversed"],
                "variant_axis_reversed": vc["axis_reversed"],
                "base_length_cm": bc["length_cm"], "variant_length_cm": vc["length_cm"],
                "base_canonical_start_cm": bc["canonical_start_cm"],
                "variant_canonical_start_cm": vc["canonical_start_cm"],
                "pieces_only_base": only_b[:12],
                "pieces_only_variant": only_v[:12],
                "base_non_modular": bc["non_modular"][:4],
                "variant_non_modular": vc["non_modular"][:4],
            })
        entry["first_divergent_call"] = next(
            (c["call_index"] for c in entry["calls"] if not c["pieces_equal"]), None)
        entry["first_input_divergent_call"] = next(
            (c["call_index"] for c in entry["calls"]
             if not (c["openings_equal"] and c["canonical_axis_equal"])), None)
        report["walls"].append(entry)
        print(" wall", key, "calls", len(b), len(v),
              "1a chamada com PECAS diferentes:", entry["first_divergent_call"],
              "| 1a com ENTRADA diferente:", entry["first_input_divergent_call"])
    F.write_json(F.out_path("out_wall_trace_%s_%s.json" % (project_id, variant)), report)
    return report


if __name__ == "__main__":
    main()
