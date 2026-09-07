# -*- coding: utf-8 -*-
"""C02 / RECONCILIACAO - prova de ownership no no' X.

Para cada no' X, mede POR FIADA quem ocupa o ponto do cruzamento, no
SOLVER e no GABARITO, e testa a alternancia:

  ALTERNA  : em cada fiada exatamente UMA das duas paredes ocupa o ponto
             (amarracao em X legitima)
  PASSAGEM : a MESMA parede ocupa em todas as fiadas e a outra nunca
             (uma parede e' dona do cruzamento; a outra abre vao)
  COLISAO  : as DUAS ocupam na mesma fiada
  VAZIO    : nenhuma ocupa

READ-ONLY.
"""
import json
import math
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nuvem.benchmark import solver_bridge as SB  # noqa: E402

PROJECTS = {
    "TGD": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tgd"),
    "TP1": os.path.join(ROOT, "nuvem/benchmark/projects/torre_easy_lo_r00_tp1"),
}
COURSES_CHECKED = (0, 1, 2, 3)


def axis_of(a, b):
    n = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[0] - a[0]) / n, (b[1] - a[1]) / n), n


def t_of(a, b, q):
    (ux, uy), n = axis_of(a, b)
    return (q[0] - a[0]) * ux + (q[1] - a[1]) * uy, n


def solver_cover(result, walls, ws, ft, wall_idx, point, course):
    p0, p1, _d, _L, _t = ws._wall_axis_and_length(walls, wall_idx)
    a = (p0.X / ft * 100.0, p0.Y / ft * 100.0)
    b = (p1.X / ft * 100.0, p1.Y / ft * 100.0)
    t0, _n = t_of(a, b, point)
    for c in (result.get("course_candidates") or {}).get(course) or []:
        if c.get("wall_idx") != wall_idx:
            continue
        o = c["origin_world"]
        tc, _ = t_of(a, b, (o.X / ft * 100.0, o.Y / ft * 100.0))
        half = float(c["length_cm"]) / 2.0
        if tc - half <= t0 <= tc + half:
            return {"code": c["logical_code"], "t_start_cm": round(tc - half, 2),
                    "t_end_cm": round(tc + half, 2), "reason": c.get("placement_reason")}
    return None


def ref_cover(ref_wall, point, course):
    a, b = tuple(ref_wall["start_cm"]), tuple(ref_wall["end_cm"])
    t0, length = t_of(a, b, point)
    rows = ref_wall.get("rows") or []
    if course >= len(rows):
        return "SEM_FIADA"
    for blk in (rows[course].get("blocks") or []):
        if blk["t_start_cm"] - 1e-9 <= t0 <= blk["t_end_cm"] + 1e-9:
            return {"code": blk["code"], "t_start_cm": blk["t_start_cm"],
                    "t_end_cm": blk["t_end_cm"]}
    return None


def ref_wall_matching(ref, walls, ws, ft, wall_idx, tol=3.0):
    p0, p1, _d, L, _t = ws._wall_axis_and_length(walls, wall_idx)
    a = (p0.X / ft * 100.0, p0.Y / ft * 100.0)
    b = (p1.X / ft * 100.0, p1.Y / ft * 100.0)
    for w in ref["walls"]:
        s, e = tuple(w["start_cm"]), tuple(w["end_cm"])
        if ((math.hypot(s[0] - a[0], s[1] - a[1]) <= tol and math.hypot(e[0] - b[0], e[1] - b[1]) <= tol) or
                (math.hypot(s[0] - b[0], s[1] - b[1]) <= tol and math.hypot(e[0] - a[0], e[1] - a[1]) <= tol)):
            return w
    return None


def verdict(per_course):
    """`per_course` = [(ocupa_A, ocupa_B), ...] por fiada."""
    if any(x and y for x, y in per_course):
        return "COLISAO"
    only_a = [bool(x) and not bool(y) for x, y in per_course]
    only_b = [bool(y) and not bool(x) for x, y in per_course]
    if all(not x and not y for x, y in per_course):
        return "VAZIO"
    if any(only_a) and any(only_b):
        return "ALTERNA"
    return "PASSAGEM"


def main():
    module = SB.engine()
    ft = module.FEET_PER_METER
    ws = sys.modules["core.engine.wall_stepper"]
    report = {"nota": ("`ocupa` = existe peca daquela parede cobrindo o ponto do "
                       "cruzamento naquela fiada. ALTERNA = amarracao em X; "
                       "PASSAGEM = uma parede e' dona do cruzamento nas duas fiadas."),
              "fiadas_checadas": list(COURSES_CHECKED), "nos": []}
    for proj, pdir in PROJECTS.items():
        data = json.load(open(os.path.join(pdir, "input.json"), encoding="utf-8"))
        ref = json.load(open(os.path.join(pdir, "reference.json"), encoding="utf-8"))
        result = SB.run_solver(data)[0]
        nodes, walls, _e2n, _op = SB.plan_from_input(data)
        for node in nodes:
            if node.get("kind") != "X_INTERSECTION":
                continue
            pair = node.get("crossing_walls")
            if not pair or pair[0] is None or pair[1] is None:
                continue
            p = node["point"]
            point = (p.X / ft * 100.0, p.Y / ft * 100.0)
            lens = []
            for widx in pair:
                lens.append(round(ws._wall_axis_and_length(walls, widx)[3] / ft * 100.0, 2))
            rw = [ref_wall_matching(ref, walls, ws, ft, w) for w in pair]
            solver_rows, ref_rows = [], []
            for course in COURSES_CHECKED:
                sa = solver_cover(result, walls, ws, ft, pair[0], point, course)
                sb = solver_cover(result, walls, ws, ft, pair[1], point, course)
                solver_rows.append((sa, sb))
                ra = ref_cover(rw[0], point, course) if rw[0] else "SEM_PAREDE"
                rb = ref_cover(rw[1], point, course) if rw[1] else "SEM_PAREDE"
                ref_rows.append((ra if isinstance(ra, dict) else None,
                                 rb if isinstance(rb, dict) else None))
            report["nos"].append({
                "project": proj,
                "no_cm": [round(v, 3) for v in point],
                "comprimentos_cm": lens,
                "menor_parede_cm": min(lens),
                "gabarito_tem_as_duas_paredes": bool(rw[0]) and bool(rw[1]),
                "solver_padrao": verdict(solver_rows),
                "gabarito_padrao": (verdict(ref_rows)
                                    if (rw[0] and rw[1]) else "SEM_PAREDE"),
                "solver_por_fiada": [
                    {"fiada": c, "parede_0": sa, "parede_1": sb}
                    for c, (sa, sb) in zip(COURSES_CHECKED, solver_rows)],
                "gabarito_por_fiada": [
                    {"fiada": c, "parede_0": ra, "parede_1": rb}
                    for c, (ra, rb) in zip(COURSES_CHECKED, ref_rows)],
            })
        print(proj, "ok")

    tally = collections.Counter(
        (n["solver_padrao"], n["gabarito_padrao"]) for n in report["nos"])
    report["resumo_solver_x_gabarito"] = {
        "solver=%s / gabarito=%s" % k: v for k, v in sorted(tally.items())}
    by_len = collections.defaultdict(collections.Counter)
    for n in report["nos"]:
        faixa = "transversal_curta_~124cm" if n["menor_parede_cm"] < 200 else "transversal_longa_>=200cm"
        by_len[faixa][n["gabarito_padrao"]] += 1
    report["gabarito_por_comprimento_da_transversal"] = {
        k: dict(v) for k, v in by_len.items()}
    report["colisoes_no_solver"] = sum(
        1 for n in report["nos"] if n["solver_padrao"] == "COLISAO")
    json.dump(report, open(os.path.join(HERE, "x_ownership_evidence.json"), "w",
                           encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report["resumo_solver_x_gabarito"], indent=1, ensure_ascii=False))
    print("por comprimento:", json.dumps(
        report["gabarito_por_comprimento_da_transversal"], ensure_ascii=False))
    print("colisoes no solver:", report["colisoes_no_solver"])


if __name__ == "__main__":
    main()
