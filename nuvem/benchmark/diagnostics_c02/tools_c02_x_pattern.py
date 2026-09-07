# -*- coding: utf-8 -*-
"""C02 / RECONCILIACAO - qual padrao o HUMANO usa em CADA no' X?

Para TODOS os nos X que o solver reconhece, olha o gabarito nas duas
paredes participantes e classifica o padrao humano:

  PASSAGEM      uma parede continua atraves do cruzamento e a outra
                abre um vao >= espessura da que passa (ownership)
  AMARRACAO     ha' peca de amarracao (B54/B34) centrada no cruzamento
  MISTO/OUTRO   nao se encaixa em nenhum dos dois
  SEM_PAREDE    a parede nao existe no gabarito com essa geometria

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
AFFECTED = {  # nos que X @0,05cm mudaria (first_divergence.json)
    "TGD": [(1263.518, -507.951)],
    "TP1": [(6607.25, 594.93), (8942.24, 594.93),
            (6607.25, 1814.95), (8942.24, 1814.95)],
}


def d2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_t(p0, p1, q):
    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(vx, vy)
    if length < 1e-9:
        return d2(p0, q), 0.0, 0.0
    t = ((q[0] - p0[0]) * vx + (q[1] - p0[1]) * vy) / length
    tc = max(0.0, min(length, t))
    proj = (p0[0] + vx / length * tc, p0[1] + vy / length * tc)
    return d2(proj, q), t, length


def ref_wall_for(ref, point, axis_hint=None, tol=2.0):
    """Parede do gabarito que passa pelo ponto, opcionalmente filtrando
    pela direcao (para separar a vertical da horizontal do X)."""
    best = None
    for w in ref["walls"]:
        p0, p1 = tuple(w["start_cm"]), tuple(w["end_cm"])
        dist, t, length = seg_t(p0, p1, point)
        if dist > tol:
            continue
        ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
        if axis_hint is not None and abs(ux * axis_hint[0] + uy * axis_hint[1]) < 0.95:
            continue
        cand = (w, t, length)
        if best is None or length > best[2]:
            best = cand
    return best


def gap_at(wall, t_point, row_index):
    """Maior vao livre da fiada `row_index` que CONTEM `t_point`.
    Devolve (gap_cm, lo, hi) ou None se ha' peca cobrindo o ponto."""
    rows = wall.get("rows") or []
    if row_index >= len(rows):
        return None
    blocks = sorted((b["t_start_cm"], b["t_end_cm"])
                    for b in (rows[row_index].get("blocks") or []))
    lo = 0.0
    for (s, e) in blocks:
        if s - 1e-9 <= t_point <= e + 1e-9:
            return None  # coberto por peca
        if s > t_point:
            return (s - lo, lo, s)
        lo = max(lo, e)
    return (wall["length_cm"] - lo, lo, wall["length_cm"])


def piece_at(wall, t_point, row_index, tol=3.0):
    """Peca do gabarito CENTRADA (ate' `tol`) em `t_point`."""
    rows = wall.get("rows") or []
    if row_index >= len(rows):
        return None
    for b in (rows[row_index].get("blocks") or []):
        center = (b["t_start_cm"] + b["t_end_cm"]) / 2.0
        if abs(center - t_point) <= tol:
            return {"code": b["code"], "t_start_cm": b["t_start_cm"],
                    "t_end_cm": b["t_end_cm"],
                    "offset_do_no_cm": round(center - t_point, 3)}
    return None


def classify(project_dir, point, walls_pair_axes):
    ref = json.load(open(os.path.join(project_dir, "reference.json"), encoding="utf-8"))
    out = {"paredes": []}
    for axis in walls_pair_axes:
        hit = ref_wall_for(ref, point, axis)
        if hit is None:
            out["paredes"].append({"axis": list(axis), "status": "SEM_PAREDE"})
            continue
        w, t, length = hit
        rec = {"axis": list(axis), "id": w["id"], "length_cm": round(length, 3),
               "thickness_cm": w.get("thickness_cm"), "t_do_no_cm": round(t, 3),
               "fiadas": []}
        for row in (0, 1):
            g = gap_at(w, t, row)
            p = piece_at(w, t, row)
            rec["fiadas"].append({
                "row": row,
                "coberto_por_peca": g is None,
                "vao_cm": round(g[0], 3) if g else None,
                "vao_intervalo": [round(g[1], 2), round(g[2], 2)] if g else None,
                "peca_centrada_no_no": p,
            })
        out["paredes"].append(rec)

    # veredito
    thick = [p.get("thickness_cm") for p in out["paredes"] if p.get("thickness_cm")]
    thick = thick[0] if thick else 14.0
    passa, abre, amarra = [], [], []
    for p in out["paredes"]:
        if p.get("status") == "SEM_PAREDE":
            continue
        covered = [f["coberto_por_peca"] for f in p["fiadas"]]
        gaps = [f["vao_cm"] for f in p["fiadas"] if f["vao_cm"] is not None]
        centered = [f["peca_centrada_no_no"] for f in p["fiadas"]
                    if f["peca_centrada_no_no"]]
        if all(covered):
            passa.append(p["id"])
        if gaps and min(gaps) >= thick:
            abre.append(p["id"])
        if any(c["code"].startswith(("B54", "B34")) for c in centered):
            amarra.append(p["id"])
    if amarra:
        out["padrao_humano"] = "AMARRACAO"
    elif passa and abre:
        out["padrao_humano"] = "PASSAGEM"
    else:
        out["padrao_humano"] = "OUTRO"
    out["parede_que_passa"] = passa
    out["parede_que_abre_vao"] = abre
    out["parede_com_amarracao_centrada"] = amarra
    out["espessura_cm"] = thick
    return out


def main():
    module = SB.engine()
    ft = module.FEET_PER_METER
    ws = sys.modules["core.engine.wall_stepper"]
    report = {"nota": ("`vao_cm` e' o espaco livre da fiada que contem o ponto do "
                       "cruzamento; comparar com a espessura da parede que passa "
                       "(vao = espessura + 2 juntas e' passagem exata)."),
              "nos": []}
    for proj, pdir in PROJECTS.items():
        data = json.load(open(os.path.join(pdir, "input.json"), encoding="utf-8"))
        nodes, walls, end_to_node, openings = SB.plan_from_input(data)
        for i, node in enumerate(nodes):
            if node.get("kind") != "X_INTERSECTION":
                continue
            pair = node.get("crossing_walls")
            if not pair or pair[0] is None or pair[1] is None:
                continue
            p = node["point"]
            point = (p.X / ft * 100.0, p.Y / ft * 100.0)
            axes = []
            for widx in pair:
                p0, p1, _d, length_ft, _t = ws._wall_axis_and_length(walls, widx)
                vx, vy = p1.X - p0.X, p1.Y - p0.Y
                n = math.hypot(vx, vy) or 1.0
                axes.append((vx / n, vy / n))
            rec = classify(pdir, point, axes)
            rec["project"] = proj
            rec["no_cm"] = [round(v, 3) for v in point]
            rec["afetado_por_tol_005"] = any(
                d2(point, a) <= 1.5 for a in AFFECTED.get(proj, []))
            report["nos"].append(rec)
        print(proj, "nos X:", sum(1 for n in report["nos"] if n["project"] == proj))

    tally = collections.Counter((n["project"], n["padrao_humano"]) for n in report["nos"])
    report["resumo"] = {"%s / %s" % k: v for k, v in sorted(tally.items())}
    aff = [n for n in report["nos"] if n["afetado_por_tol_005"]]
    report["resumo_afetados"] = dict(collections.Counter(n["padrao_humano"] for n in aff))
    json.dump(report, open(os.path.join(HERE, "x_node_human_pattern.json"), "w",
                           encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(report["resumo"], indent=1, ensure_ascii=False))
    print("afetados:", report["resumo_afetados"])


if __name__ == "__main__":
    main()
