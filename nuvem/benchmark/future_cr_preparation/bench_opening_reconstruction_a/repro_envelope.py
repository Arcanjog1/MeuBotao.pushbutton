# -*- coding: utf-8 -*-
"""REPRODUCER instrumentado (FASE 2) - NAO e' producao.

Replica, linha a linha, o agrupamento de `detect_wall_openings_from_courses`
do STATE_A, mas registra TODOS os vazios de fiada que entraram em cada run,
para medir separadamente:
  * ENVELOPE  = (min(inicio), max(fim))   <- o que o STATE_A grava
  * CONSENSO  = (max(inicio), min(fim))   <- o que toda fiada respeita
  * SPREAD    = desacordo entre fiadas, por borda
"""
import collections
import json
import os
import sys

ROOT = os.environ.get("REPO_ROOT", os.path.abspath("."))
sys.path.insert(0, ROOT)

from nuvem.core.engine import opening_audit as oa  # noqa: E402

TOL = oa.OPENING_RUN_EDGE_MATCH_TOLERANCE_CM


def runs_with_members(courses):
    ordered = sorted(courses, key=lambda c: c[0])
    if len(ordered) < oa.OPENING_MIN_CONSEC_COURSES:
        return []
    course_gaps = {}
    for z_cm, intervals in ordered:
        merged = oa.merge_axis_intervals([(s, e) for s, e, _f in intervals])
        course_gaps[z_cm] = [(s, e) for s, e in oa.gaps_between_intervals(merged)
                             if oa.OPENING_GAP_MIN_CM <= (e - s) <= oa.OPENING_GAP_MAX_CM]
    out, used = [], set()
    for i, (z_cm, _iv) in enumerate(ordered):
        for gi, (gs, ge) in enumerate(course_gaps.get(z_cm, [])):
            if (z_cm, gi) in used:
                continue
            used.add((z_cm, gi))
            members = [(z_cm, gs, ge)]
            run_start, run_end = gs, ge
            for z2, _iv2 in ordered[i + 1:]:
                match = None
                for gj, (gs2, ge2) in enumerate(course_gaps.get(z2, [])):
                    if (z2, gj) in used:
                        continue
                    if (abs(gs2 - run_start) <= TOL and abs(ge2 - run_end) <= TOL):
                        match = (gj, gs2, ge2)
                        break
                if match is None:
                    break
                gj, gs2, ge2 = match
                used.add((z2, gj))
                members.append((z2, gs2, ge2))
                run_start = min(run_start, gs2)
                run_end = max(run_end, ge2)
            if len(members) >= oa.OPENING_MIN_CONSEC_COURSES:
                out.append(members)
    return out


def courses_of(wall):
    by_z = {}
    for row in wall.get("rows") or []:
        bucket = by_z.setdefault(row.get("elevation_cm"), [])
        for b in row.get("blocks") or []:
            bucket.append((b["t_start_cm"], b["t_end_cm"], b.get("type_name")))
    return [(z, iv) for z, iv in sorted(by_z.items())]


def main():
    projects = sys.argv[1:] or ["torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"]
    report = {}
    for proj in projects:
        path = os.path.join(ROOT, "nuvem/benchmark/projects", proj, "reference.json")
        data = json.load(open(path, encoding="utf-8"))
        rows = []
        for wall in data.get("walls") or []:
            for members in runs_with_members(courses_of(wall)):
                starts = [m[1] for m in members]
                ends = [m[2] for m in members]
                env = (min(starts), max(ends))
                cons = (max(starts), min(ends))
                rows.append({
                    "wall": wall["id"],
                    "n_courses": len(members),
                    "envelope": [round(env[0], 3), round(env[1], 3)],
                    "consenso": [round(cons[0], 3), round(cons[1], 3)],
                    "largura_envelope": round(env[1] - env[0], 3),
                    "largura_consenso": round(cons[1] - cons[0], 3),
                    "spread_inicio": round(max(starts) - min(starts), 3),
                    "spread_fim": round(max(ends) - min(ends), 3),
                    "membros": [[round(z, 3), round(s, 3), round(e, 3)] for z, s, e in members],
                })
        assinatura = [r for r in rows
                      if r["spread_inicio"] == 15.0 and r["spread_fim"] == 15.0]
        com_desacordo = [r for r in rows if r["spread_inicio"] or r["spread_fim"]]
        consenso_abaixo_min = [r for r in rows
                               if r["largura_consenso"] < oa.OPENING_GAP_MIN_CM]
        consenso_invertido = [r for r in rows if r["largura_consenso"] < 0]
        report[proj] = {
            "n_runs": len(rows),
            "n_com_desacordo": len(com_desacordo),
            "n_assinatura_15cm": len(assinatura),
            "n_consenso_abaixo_de_OPENING_GAP_MIN": len(consenso_abaixo_min),
            "n_consenso_invertido": len(consenso_invertido),
            "spread_max_inicio": max([r["spread_inicio"] for r in rows] or [0]),
            "spread_max_fim": max([r["spread_fim"] for r in rows] or [0]),
            "hist_spread": dict(sorted(collections.Counter(
                (r["spread_inicio"], r["spread_fim"]) for r in rows).items(),
                key=lambda kv: -kv[1])[:10]) and {
                    str(k): v for k, v in sorted(collections.Counter(
                        (r["spread_inicio"], r["spread_fim"]) for r in rows).items())},
            "larguras_envelope": {str(k): v for k, v in sorted(collections.Counter(
                r["largura_envelope"] for r in rows).items())},
            "larguras_consenso": {str(k): v for k, v in sorted(collections.Counter(
                r["largura_consenso"] for r in rows).items())},
            "assinatura": assinatura,
            "runs": rows,
        }
        print("%-24s runs=%3d  com_desacordo=%3d  assinatura_15cm=%3d  "
              "consenso<min=%d  invertido=%d  spread_max=(%.1f,%.1f)" % (
                  proj, len(rows), len(com_desacordo), len(assinatura),
                  len(consenso_abaixo_min), len(consenso_invertido),
                  report[proj]["spread_max_inicio"], report[proj]["spread_max_fim"]))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repro_envelope.json")
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print("escrito:", out)


if __name__ == "__main__":
    main()
