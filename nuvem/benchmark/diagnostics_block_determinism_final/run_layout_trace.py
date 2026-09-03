# -*- coding: utf-8 -*-
"""Instrumentacao MAIS FUNDA que `run_wall_trace.py` (item 11/42/43 da
missao): grava a SEQUENCIA de chamadas ao solver de pilarete
(`_continuous_segment_layout`, `_pier_ordered_layout`,
`_pier_layout_avoiding_joints`) de UMA parede - argumentos e layout
devolvido - para comparar A->B contra B->A trecho a trecho.

    python3 run_layout_trace.py <wall_key_json> [variant] [project_id]
"""
import sys
import json

import lib_final as F
import variants as V
import run_row_diff as RD


def trace(project_id, input_project, target_key):
    engine = F.L.engine()
    stepper = sys.modules[engine.solve_wall_free_fill.__module__]
    originals = {}
    log = []
    state = {"active": False, "call": -1}

    names = ("_continuous_segment_layout", "_pier_ordered_layout",
             "_pier_layout_avoiding_joints", "_recut_openings_and_repair")

    def _norm(value):
        if isinstance(value, float):
            return repr(value)   # PRECISAO TOTAL - ver "purity" no relatorio
        if isinstance(value, dict):
            return [(k, _norm(v)) for k, v in sorted(value.items(), key=repr)]
        if isinstance(value, (list, tuple)):
            return [_norm(v) for v in value]
        return value

    def _sig(args, kwargs):
        return repr([_norm(list(args)),
                      sorted(((k, _norm(v)) for k, v in kwargs.items()), key=repr)])

    def make_spy(name, func):
        def spy(*args, **kwargs):
            out = func(*args, **kwargs)
            if state["active"]:
                if name == "_recut_openings_and_repair":
                    record = {"fn": name, "call": state["call"],
                              "n_candidates": len(out["candidates"]),
                              "n_removed": len(out["removed"]),
                              "regions": [
                                  (round(r.get("lo", 0.0), 4), round(r.get("hi", 0.0), 4))
                                  for r in (out.get("regions") or [])]}
                else:
                    record = {
                        "fn": name, "call": state["call"],
                        "pier_cm": round(float(args[0]), 4),
                        "lead_cm": round(float(args[2]), 4),
                        "trail_cm": round(float(args[3]), 4),
                        "seg_start_cm": (round(float(args[4]), 4)
                                          if len(args) > 4 and isinstance(args[4], float)
                                          else None),
                        "leading_open": kwargs.get("leading_is_open",
                                                    kwargs.get("leading_open",
                                                               kwargs.get("leading_open_override"))),
                        "trailing_open": kwargs.get("trailing_is_open",
                                                     kwargs.get("trailing_open",
                                                                kwargs.get("trailing_open_override"))),
                        "avoid_joints_cm": (
                            sorted(round(float(v), 4) for v in args[5])
                            if name == "_pier_layout_avoiding_joints" and len(args) > 5 else None),
                        "avoid_joints_raw": (
                            [round(float(v), 4) for v in args[5]]
                            if name == "_pier_layout_avoiding_joints" and len(args) > 5 else None),
                        "target_voids_cm": (
                            sorted(round(float(v), 4)
                                    for v in (kwargs.get("target_void_positions_cm") or []))
                            if name == "_pier_layout_avoiding_joints" else None),
                        # Assinatura COMPLETA da chamada - se ela bater e o
                        # layout nao, a funcao nao e' pura (e a causa esta'
                        # DENTRO dela, nao na entrada).
                        "args_sig": _sig(args, kwargs),
                        "layout": [(code, round(a, 4), round(b, 4)) for code, a, b in (out or [])],
                    }
                log.append(record)
            return out
        return spy

    original_fill = stepper.solve_wall_free_fill

    def fill_spy(wall_idx, walls_to_create, *args, **kwargs):
        key = F.L.wall_geom_key(walls_to_create, wall_idx)
        if key == target_key:
            state["active"] = True
            state["call"] += 1
        try:
            return original_fill(wall_idx, walls_to_create, *args, **kwargs)
        finally:
            state["active"] = False

    for name in names:
        originals[name] = getattr(stepper, name)
        setattr(stepper, name, make_spy(name, originals[name]))
    stepper.solve_wall_free_fill = fill_spy
    try:
        F.run_solver(project_id, input_project=input_project)
    finally:
        for name in names:
            setattr(stepper, name, originals[name])
        stepper.solve_wall_free_fill = original_fill
    return log


def main():
    target_key = tuple(json.loads(sys.argv[1]))
    variant = sys.argv[2] if len(sys.argv) > 2 else "endpoint_reversal"
    project_id = sys.argv[3] if len(sys.argv) > 3 else F.PRIMARY_PROJECT_ID

    base_project = F.load_input(project_id)
    base = trace(project_id, base_project, target_key)
    var = trace(project_id, RD.VARIANT_BUILDERS[variant](base_project), target_key)

    print("registros base=%d variante=%d" % (len(base), len(var)))
    def cmp_key(rec):
        # `args_sig` fica de FORA da comparacao de propósito: ele carrega o
        # repr float completo, que so' serve para PROVAR se a funcao e' pura
        # quando o layout ja' divergiu - usa-lo aqui acusaria como
        # "divergencia" o ruido de ultimo bit que o snap ja' absorve.
        return dict((k, v) for k, v in rec.items() if k != "args_sig")

    first = None
    for i in range(min(len(base), len(var))):
        if cmp_key(base[i]) != cmp_key(var[i]):
            first = i
            break
    if first is None and len(base) != len(var):
        first = min(len(base), len(var)) - 1
    print("primeira chamada divergente:", first)
    if first is not None:
        for i in range(max(0, first - 2), min(len(base), first + 3)):
            print(" [%d] base: %s" % (i, json.dumps(base[i], ensure_ascii=False)[:400]))
            print(" [%d] var : %s" % (i, json.dumps(var[i], ensure_ascii=False)[:400]))
    F.write_json(F.out_path("out_layout_trace_%s.json" % variant),
                 {"target_key": list(target_key), "variant": variant,
                  "first_divergent": first, "base": base, "variant_log": var})


if __name__ == "__main__":
    main()
