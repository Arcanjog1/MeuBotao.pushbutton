# -*- coding: utf-8 -*-
"""OPENING REPAIR x NODE-FILL (item 9): reexecuta o solver com WRAPPERS de
monkeypatch (so' nesta execucao) em `_recut_openings_and_repair` e
`_pier_layout_avoiding_joints`, capturando para as paredes-alvo:
  - composicao CONTINUA (antes do recorte) por fiada/variante/banda;
  - pecas derrubadas pelo recorte e regioes de reparo;
  - composicao depois do reparo;
  - cada busca de layout (trecho, avoid, target, resultado) dentro do reparo.
Nao altera producao.

    ATLAS_OUT_DIR=... python3 probe_opening_repair.py torre_easy_lo_r00_tp1 35 37
    -> <SHORT>/opening_repair_trace.json
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

FT = 30.48


def main(argv):
    pid = argv[0]
    targets = set(int(x) for x in argv[1:])
    st = al.stepper()
    trace = []
    band_counter = {"band": -1}
    orig_recut = st._recut_openings_and_repair
    orig_avoid = st._pier_layout_avoiding_joints
    orig_ordered = st._pier_ordered_layout
    depth = {"in_recut": 0, "wall": None, "course": None}

    def fmt(cands, p0, wall_dir):
        out = []
        for c in cands:
            a, b_ = st._candidate_t_range_on_wall(c, p0, wall_dir)
            out.append((round(min(a, b_), 1), round(max(a, b_), 1), c.get("logical_code"), c.get("placement_reason")))
        return sorted(out)

    def recut(wall_idx, wall_p0, wall_dir, catalog, candidates, seg_records, opening_intervals_cm,
              course, variant_index, **kw):
        if wall_idx not in targets:
            return orig_recut(wall_idx, wall_p0, wall_dir, catalog, candidates, seg_records,
                              opening_intervals_cm, course, variant_index, **kw)
        depth["in_recut"] += 1
        depth["wall"], depth["course"] = wall_idx, course
        before = fmt(candidates, wall_p0, wall_dir)
        searches = []
        depth["searches"] = searches
        result = orig_recut(wall_idx, wall_p0, wall_dir, catalog, candidates, seg_records,
                            opening_intervals_cm, course, variant_index, **kw)
        depth["in_recut"] -= 1
        trace.append({
            "wall_idx": wall_idx, "course": course, "variant": variant_index,
            "openings_cm": [list(o) for o in opening_intervals_cm],
            "avoid_joint_positions_cm": sorted(round(x, 1) for x in (kw.get("avoid_joint_positions_cm") or [])),
            "target_void_positions_cm": sorted(round(x, 1) for x in (kw.get("target_void_positions_cm") or [])),
            "prefer_avoiding": kw.get("prefer_avoiding"),
            "before": before,
            "removed": [(round(r["t_start_cm"], 1), round(r["t_end_cm"], 1), r["logical_code"]) for r in result["removed"]],
            "regions": [{k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()} for r in result["regions"]],
            "after": fmt(result["candidates"], wall_p0, wall_dir),
            "non_modular": [{k: v for k, v in x.items() if k in ("conflict", "seg_start_cm", "seg_end_cm", "current_length_cm")} for x in result["non_modular"]],
            "searches": searches,
        })
        return result

    def avoid(pier_cm, catalog, lead, trail, seg_start_cm, avoid_positions_cm, **kw):
        res = orig_avoid(pier_cm, catalog, lead, trail, seg_start_cm, avoid_positions_cm, **kw)
        if depth["in_recut"] and depth.get("searches") is not None:
            base = orig_ordered(pier_cm, catalog, lead, trail,
                                leading_open_override=kw.get("leading_is_open"),
                                trailing_open_override=kw.get("trailing_is_open"))
            depth["searches"].append({
                "fn": "_pier_layout_avoiding_joints", "pier_cm": round(pier_cm, 2), "seg_start_cm": round(seg_start_cm, 2),
                "lead": lead, "trail": trail, "leading_open": kw.get("leading_is_open"), "trailing_open": kw.get("trailing_is_open"),
                "avoid": sorted(round(x, 1) for x in (avoid_positions_cm or [])),
                "target_voids": sorted(round(x, 1) for x in (kw.get("target_void_positions_cm") or [])),
                "baseline": None if base is None else [(c, round(seg_start_cm + a, 1), round(seg_start_cm + b_, 1)) for c, a, b_ in base],
                "result": None if res is None else [(c, round(seg_start_cm + a, 1), round(seg_start_cm + b_, 1)) for c, a, b_ in res],
                "result_joints": None if res is None else [round(x, 1) for x in st._layout_internal_joint_positions_cm(res, seg_start_cm)],
            })
        return res

    def ordered(pier_cm, catalog, lead, trail, *a, **kw):
        res = orig_ordered(pier_cm, catalog, lead, trail, *a, **kw)
        if depth["in_recut"] and depth.get("searches") is not None and not kw.get("_allow_opening_joint_fallback") is False:
            depth["searches"].append({"fn": "_pier_ordered_layout", "pier_cm": round(pier_cm, 2), "lead": lead, "trail": trail,
                                      "first_code": kw.get("first_code"), "leading_open": kw.get("leading_open_override"),
                                      "trailing_open": kw.get("trailing_open_override"),
                                      "result": None if res is None else [(c, round(a_, 1), round(b_, 1)) for c, a_, b_ in res]})
        return res

    st._recut_openings_and_repair = recut
    st._pier_layout_avoiding_joints = avoid
    st._pier_ordered_layout = ordered
    try:
        run = al.run_solver_in_memory(al.load_input(pid))
    finally:
        st._recut_openings_and_repair = orig_recut
        st._pier_layout_avoiding_joints = orig_avoid
        st._pier_ordered_layout = orig_ordered
    # anota a banda (ordem de chamada: bandas em sequencia; cada banda chama recut por parede/fiada)
    al.write_json(al.out_path(al.SHORT[pid], "opening_repair_trace.json"), trace)
    print("trace entries:", len(trace))
    for t in trace:
        print("wall", t["wall_idx"], "course", t["course"], "openings", t["openings_cm"], "removed", t["removed"], "regions", [(r["lo"], r["hi"], r["left_anchor_is_block"], r["right_anchor_is_block"]) for r in t["regions"]])
        print("   before:", [x for x in t["before"] if x[0] < 120])
        print("   after :", [x for x in t["after"] if x[0] < 120])
        print("   avoid :", [x for x in t["avoid_joint_positions_cm"] if x < 120], "targets:", [x for x in t["target_void_positions_cm"] if x < 120])
        for s_ in t["searches"]:
            if s_["fn"] == "_pier_layout_avoiding_joints" and s_["seg_start_cm"] < 120:
                print("   search:", s_)
            elif s_["fn"] == "_pier_ordered_layout" and s_["pier_cm"] < 80:
                print("   ordered:", s_)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
