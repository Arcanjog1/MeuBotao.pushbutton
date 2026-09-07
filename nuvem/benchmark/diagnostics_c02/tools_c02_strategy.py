# -*- coding: utf-8 -*-
"""C02 / MODO A - comparacao DIAGNOSTICA de estrategias.

Nao altera producao: cada variante e' um monkey-patch em memoria, aplicado
num PROCESSO proprio (cada execucao do script roda UMA variante), e o
resultado e' o conjunto de PECAS FINAIS (`course_candidates`), nao
contagem de avaliacoes.

Identidade fisica estavel de peca:
    (fiada, x_cm, y_cm, codigo, rotacao, comprimento)
- nunca wall_idx / block_id / ordem de lista.

Uso:  python3 tools_c02_strategy.py <variante>
      variantes: baseline | x005 | x030 | xt005
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# raiz do repositorio: este diretorio vive em nuvem/benchmark/diagnostics_c02/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from nuvem.benchmark import solver_bridge as SB  # noqa: E402

PROJECTS = {
    "TGD": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tgd/input.json"),
    "TP1": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tp1/input.json"),
    "PILOTO": os.path.join(ROOT, "nuvem/benchmark/projects/piloto_sintetico_2x2/input.json"),
}


def apply_variant(module, variant):
    ws = sys.modules["core.engine.wall_stepper"]
    if variant == "baseline":
        return 0.0
    tol_cm = {"x005": 0.05, "x030": 0.30, "xt005": 0.05}[variant]
    tol_ft = ws._cm_to_ft(tol_cm)

    # X: somar a tolerancia ao ROOM medido e' algebricamente identico a
    # `half+joint <= room + tol` tanto no gate do B54 quanto na degradacao
    # (`_x_intersection_centered_candidate` recebe esse mesmo minimo).
    orig_x_room = ws._x_intersection_wall_room_ft

    def x_room(*args, **kwargs):
        rp, rm = orig_x_room(*args, **kwargs)
        return rp + tol_ft, rm + tol_ft

    ws._x_intersection_wall_room_ft = x_room

    if variant == "xt005":
        # T: o gate e' pequeno e puro - reimplementado fielmente com a
        # tolerancia, SEM tocar no assessment (que tambem posiciona).
        orig_assess = ws._t_intersection_room_assessment

        def t_ok(node, walls_to_create, openings_per_wall, nodes=None,
                 end_to_node=None, node_index=None):
            if openings_per_wall is None:
                return True
            a = orig_assess(node, walls_to_create, openings_per_wall, nodes=nodes,
                            end_to_node=end_to_node, node_index=node_index)
            if a is None:
                return True
            if min(a["room_plus_ft"], a["room_minus_ft"]) + tol_ft < ws.T_INTERSECTION_B54_HALF_ROOM_FT:
                return False
            return a["room_incoming_ft"] + tol_ft >= ws.CORNER_B34_ROOM_FT

        ws._t_intersection_room_ok = t_ok
        if hasattr(module, "_t_intersection_room_ok"):
            module._t_intersection_room_ok = t_ok
    return tol_cm


def pieces(solve_result, module):
    """Peças FINAIS por identidade geometrica estavel."""
    ft = module.FEET_PER_METER
    out = {}
    for course_index, cands in (solve_result.get("course_candidates") or {}).items():
        for c in cands or []:
            o = c["origin_world"]
            key = "%d|%.3f|%.3f|%s|%.1f|%.2f" % (
                course_index, o.X / ft * 100.0, o.Y / ft * 100.0,
                c["logical_code"], c.get("rotation_deg") or 0.0,
                float(c["length_cm"]))
            out[key] = {
                "course": course_index,
                "x_cm": round(o.X / ft * 100.0, 3),
                "y_cm": round(o.Y / ft * 100.0, 3),
                "code": c["logical_code"],
                "reason": c.get("placement_reason"),
                "length_cm": float(c["length_cm"]),
            }
    return out


def main():
    variant = sys.argv[1]
    module = SB.engine()
    tol = apply_variant(module, variant)
    result = {"variant": variant, "tolerance_cm": tol, "projects": {}}
    for name, path in PROJECTS.items():
        with open(path, "r", encoding="utf-8") as h:
            project = json.load(h)
        solve_result = SB.run_solver(project)[0]
        p = pieces(solve_result, module)
        by_code = {}
        for v in p.values():
            by_code[v["code"]] = by_code.get(v["code"], 0) + 1
        result["projects"][name] = {
            "total_pieces": len(p),
            "by_code": by_code,
            "failures": len(solve_result.get("failures") or []),
            "pieces": p,
        }
        print("%-7s %s pecas=%d %s" % (name, variant, len(p), by_code))
    out = os.path.join(HERE, "c02_pieces_%s.json" % variant)
    with open(out, "w", encoding="utf-8") as h:
        json.dump(result, h)
    print("gravado", out)


if __name__ == "__main__":
    main()
