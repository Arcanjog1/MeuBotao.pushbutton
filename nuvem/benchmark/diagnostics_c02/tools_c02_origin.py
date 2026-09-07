# -*- coding: utf-8 -*-
"""C02 / MODO A - de ONDE vem o deficit (0,003 / 0,01 / 0,02 / 0,10cm)?

A pergunta que decide a CR: o `room` que falta por 0,003cm e' RUIDO DE
REPRESENTACAO (conversao cm->ft->cm) ou GEOMETRIA REAL (a parede/abertura
esta' mesmo 0,003cm mais curta)? A resposta muda a solucao:
  - ruido        -> tolerancia numerica e' legitima (nada e' invadido);
  - geometria    -> a tolerancia INVADE 0,003cm de algo real. Ai' importa
                    O QUE e' invadido: junta de argamassa (cede) ou
                    reserva de amarracao de outro no' (nao cede - foi
                    exatamente o caso W087 que o C04 recusou).

Reimplementa `_room_at_t_on_wall` como wrapper que reporta o LIMITE que
venceu (abertura / reserva de no' na outra ponta / ponta fisica).
"""
import json
import os
import sys
import collections

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

RECORDS = []
_CTX = {"project": None, "in_x": False}


def install(module):
    ws = sys.modules["core.engine.wall_stepper"]
    FT = module.FEET_PER_METER

    def cm(v):
        return v / FT * 100.0

    orig_room = ws._room_at_t_on_wall
    orig_x_room = ws._x_intersection_wall_room_ft

    def room_at_t(walls_to_create, openings_per_wall, wall_idx, t_ft, sign,
                  safe_range_ft=None):
        value = orig_room(walls_to_create, openings_per_wall, wall_idx, t_ft, sign,
                          safe_range_ft)
        if not _CTX["in_x"]:
            return value
        _p0, _p1, _d, total_len_ft, _t = ws._wall_axis_and_length(walls_to_create, wall_idx)
        lo_ft, hi_ft = (0.0, total_len_ft) if safe_range_ft is None else safe_range_ft
        openings_here = (openings_per_wall[wall_idx]
                         if (openings_per_wall and wall_idx < len(openings_per_wall)) else [])
        if sign >= 0:
            boundary, src = hi_ft, ("RESERVA_OU_PONTA" if safe_range_ft
                                    and abs(hi_ft - total_len_ft) > 1e-9 else "PONTA_FISICA")
            for (t_lo, _t_hi, _s, _h) in openings_here:
                if t_lo >= t_ft - 1e-6 and t_lo < boundary:
                    boundary, src = t_lo, "ABERTURA"
        else:
            boundary, src = lo_ft, ("RESERVA_OU_PONTA" if safe_range_ft
                                    and abs(lo_ft) > 1e-9 else "PONTA_FISICA")
            for (_t_lo, t_hi, _s, _h) in openings_here:
                if t_hi <= t_ft + 1e-6 and t_hi > boundary:
                    boundary, src = t_hi, "ABERTURA"
        RECORDS.append({
            "project": _CTX["project"],
            "room_cm": round(cm(value), 6),
            "sign": int(sign),
            "boundary_source": src,
            "t_cm": round(cm(t_ft), 6),
            "boundary_cm": round(cm(boundary), 6),
            "wall_len_cm": round(cm(total_len_ft), 6),
            "lo_cm": round(cm(lo_ft), 6),
            "hi_cm": round(cm(hi_ft), 6),
            # a mesma conta refeita em CM PURO (sem passar por ft): se o
            # resultado bater com o de ft, o deficit NAO e' de conversao.
            "room_cm_exact": round(abs(cm(boundary) - cm(t_ft)), 6),
        })
        return value


    def x_room(walls_to_create, openings_per_wall, wall_idx, point, nodes=None,
               end_to_node=None, exclude_node_index=None):
        _CTX["in_x"] = True
        try:
            return orig_x_room(walls_to_create, openings_per_wall, wall_idx, point,
                               nodes, end_to_node, exclude_node_index)
        finally:
            _CTX["in_x"] = False

    ws._room_at_t_on_wall = room_at_t
    ws._x_intersection_wall_room_ft = x_room


def main():
    module = SB.engine()
    install(module)
    for name, path in PROJECTS.items():
        _CTX["project"] = name
        with open(path, "r", encoding="utf-8") as h:
            project = json.load(h)
        SB.run_solver(project)

    # so' os casos borderline (room entre 27,0 e 28,0cm)
    interesting = [r for r in RECORDS if 27.0 <= r["room_cm"] < 28.0]
    seen = {}
    for r in interesting:
        key = (r["project"], r["room_cm"], r["boundary_source"], r["t_cm"],
               r["boundary_cm"], r["wall_len_cm"], r["lo_cm"], r["hi_cm"])
        seen[key] = seen.get(key, 0) + 1
    rows = []
    for key, n in sorted(seen.items()):
        rows.append({"project": key[0], "room_cm": key[1], "boundary_source": key[2],
                     "t_cm": key[3], "boundary_cm": key[4], "wall_len_cm": key[5],
                     "lo_cm": key[6], "hi_cm": key[7], "evaluations": n})
    print(json.dumps(rows, indent=1, ensure_ascii=False))
    with open(os.path.join(HERE, "c02_deficit_origin.json"), "w", encoding="utf-8") as h:
        json.dump(rows, h, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
