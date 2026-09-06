# -*- coding: utf-8 -*-
"""COBERTURA decomposta por CAUSA (item 14). Para cada COVERAGE_GAP_IN_ROW /
COVERAGE_MISSING_ROW / COVERAGE_ROW_MOSTLY_EMPTY / COVERAGE_PARTIAL_WALL /
COVERAGE_WALL_NOT_MODULATED, cruza o intervalo vazio com o que o SOLVER
registrou naquela parede/fiada:

  FOREIGN_PIECE_COVERS     peca de no' da vizinha ocupa o vazio -> artefato do validador (regua)
  NON_MODULAR_FIT          trecho registrado em non_modular sem conflito (aritmetica nao fecha)
  NON_MODULAR_SEM_ESPACO   trecho negativo (reserva de no' > espaco)
  OPENING_REPAIR_FAILED    ABERTURA_NAO_COMPATIVEL
  DROPPED_FILL_COLLISION   peca de preenchimento descartada por colidir com peca de no'
  NODE_UNBOUND_RESERVE     vazio na zona de reserva de um no' que ficou SEM peca (intersection failure/degradado curto)
  UNKNOWN

    <SHORT>/coverage_decomposition.json ; coverage_decomposition_summary.json
"""
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

COV = ("COVERAGE_GAP_IN_ROW", "COVERAGE_MISSING_ROW", "COVERAGE_ROW_MOSTLY_EMPTY",
       "COVERAGE_PARTIAL_WALL", "COVERAGE_WALL_NOT_MODULATED")


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def build(project_id):
    b = al.Bundle(project_id)
    sr = b.run["solve_result"]
    nm_by_wall = {}
    for x in sr.get("non_modular") or []:
        nm_by_wall.setdefault(x["wall_idx"], []).append(x)
    dropped = {}
    for ci, lst in (sr.get("dropped_fill_by_course") or {}).items():
        for c in lst:
            dropped.setdefault((c.get("wall_idx"), int(ci)), []).append(c)
    failures = dict((ni, reason) for ni, reason in (sr.get("intersection_failures") or []))
    rows = []
    for f in b.findings():
        if f["code"] not in COV:
            continue
        wi = b.idx(f["wall"])
        ctx = b.ctx(wi)
        rec = {"project": b.short, "code": f["code"], "wall_id": f["wall"], "wall_idx": wi,
               "human_wall": ctx["human_wall"], "in_scope": ctx.get("in_scope", True),
               "wall_len": ctx["length_cm"], "row": f.get("row"), "detail": f.get("detail")}
        causes = []
        if f["code"] == "COVERAGE_GAP_IN_ROW":
            lo, hi = f["gap_t_cm"]
            row = f["row"]
            letter = al.course_letter(row)
            # peca estrangeira cobre?
            items = b.solver_row(wi, row, include_secondary=True)
            foreign = [it for it in items if not it["is_own"] and overlap((it["t0"], it["t1"]), (lo, hi)) > 1.0]
            if foreign and sum(overlap((it["t0"], it["t1"]), (lo, hi)) for it in foreign) >= 0.8 * (hi - lo):
                causes.append("FOREIGN_PIECE_COVERS")
            for x in nm_by_wall.get(wi, []):
                if x["course"] != letter:
                    continue
                seg = (min(x["seg_start_cm"], x["seg_end_cm"]) - 2, max(x["seg_start_cm"], x["seg_end_cm"]) + 2)
                if overlap(seg, (lo, hi)) > 1.0:
                    conf = x.get("conflict")
                    causes.append("NON_MODULAR_SEM_ESPACO" if conf == "SEM_ESPACO" else
                                  "OPENING_REPAIR_FAILED" if conf == "ABERTURA_NAO_COMPATIVEL" else "NON_MODULAR_FIT")
            for c in dropped.get((wi, row), []):
                t0, t1, _s = al.candidate_extent_cm(c, b.run["walls_to_create"], wi)
                if overlap((t0, t1), (lo, hi)) > 1.0:
                    causes.append("DROPPED_FILL_COLLISION")
            # reserva de no' sem peca
            for e in (0, 1):
                end = ctx["ends"][e]
                if end["kind"] in ("NONE", "FREE_END", "STRAIGHT_CONTINUATION"):
                    continue
                zone = (end["t_cm"] - 30, end["t_cm"] + 30)
                if overlap(zone, (lo, hi)) > 1.0:
                    pieces_here = [p for p in end["pieces"] if p["course"] == letter]
                    if end.get("node_index") in failures:
                        causes.append("NODE_UNBOUND_RESERVE(intersection_failure)")
                    elif not pieces_here:
                        causes.append("NODE_UNBOUND_RESERVE(no_piece_this_course)")
                    elif any(p["code"] in ("C09", "C04") for p in pieces_here):
                        causes.append("NODE_RESERVE_DEGRADED_SHORT")
            for m in ctx["midspan_nodes"]:
                zone = (m["t_cm"] - 30, m["t_cm"] + 30)
                if overlap(zone, (lo, hi)) > 1.0:
                    pieces_here = [p for p in m["pieces"] if p["course"] == letter]
                    if m["node_index"] in failures:
                        causes.append("NODE_UNBOUND_RESERVE(intersection_failure)")
                    elif not pieces_here:
                        causes.append("MIDSPAN_NODE_NO_PIECE_THIS_COURSE")
            rec["gap"] = [lo, hi]
            rec["gap_cm"] = round(hi - lo, 1)
        else:
            # fiada/parede inteira: decide pela familia vazia x non_modular
            nm = nm_by_wall.get(wi, [])
            confs = Counter(x.get("conflict") or "fit" for x in nm)
            if confs:
                top = confs.most_common(1)[0][0]
                causes.append({"fit": "NON_MODULAR_FIT", "SEM_ESPACO": "NON_MODULAR_SEM_ESPACO",
                               "ABERTURA_NAO_COMPATIVEL": "OPENING_REPAIR_FAILED"}[top])
            if ctx["length_cm"] < 40:
                causes.append("TINY_WALL_FRAGMENT(<40cm)")
        rec["causes"] = sorted(set(causes)) or ["UNKNOWN"]
        rec["primary"] = rec["causes"][0]
        rows.append(rec)
    al.write_json(al.out_path(b.short, "coverage_decomposition.json"), rows)
    return rows


def summarize(rows):
    s = {}
    for code in COV:
        sub = [r for r in rows if r["code"] == code]
        if not sub:
            continue
        s[code] = {"total": len(sub),
                   "by_primary": Counter(r["primary"] for r in sub).most_common(),
                   "by_causes": Counter("+".join(r["causes"]) for r in sub).most_common(8),
                   "in_scope": sum(1 for r in sub if r["in_scope"]),
                   "with_human": sum(1 for r in sub if r["human_wall"])}
    return s


def main(argv=None):
    ids = al.PROJECT_IDS if not argv else tuple(argv)
    out = {}
    for pid in ids:
        rows = build(pid)
        s = summarize(rows)
        out[al.SHORT[pid]] = s
        print("=====", al.SHORT[pid])
        for code, v in s.items():
            print("  ", code, v["total"], "in_scope", v["in_scope"], "human", v["with_human"])
            print("      primary:", v["by_primary"])
    al.write_json(al.out_path("coverage_decomposition_summary.json"), out)


if __name__ == "__main__":
    main(sys.argv[1:])
