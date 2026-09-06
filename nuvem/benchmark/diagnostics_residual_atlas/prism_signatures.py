# -*- coding: utf-8 -*-
"""PRISM_CONTINUOUS_JOINT (item 15): agrupa os achados por ASSINATURA
FISICA repetida - posicao da junta relativa ao no'/abertura mais proximo,
par de pecas de cada lado nas duas fiadas, se uma das pecas e' de no'
(junta NO'|FILL), banda - e mede a multiplicidade (quantos pares de fiadas
repetem a mesma junta). Cruza com o humano no mesmo t.

    <SHORT>/prism_signatures.json
    prism_signatures_summary.json
"""
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402


def _blocks_index(result):
    idx = {}
    for wall in result["walls"]:
        for row in wall["rows"]:
            for block in row["blocks"]:
                idx[block["id"]] = block
    return idx


def _side(block):
    if block is None:
        return ("?", "?")
    reason = block.get("placement_reason") or "?"
    kind = "TIE" if al.is_tie_reason(reason) else ("REPAIR" if reason == "OPENING_REPAIR_FILL" else "FILL")
    return (block.get("code"), kind)


def build(project_id):
    b = al.Bundle(project_id)
    blocks = _blocks_index(b.result)
    sig = {}
    for f in b.findings("PRISM_CONTINUOUS_JOINT"):
        wi = b.idx(f["wall"])
        ctx = b.ctx(wi)
        t = float(f["joint_t_cm"])
        ra, rb = int(f["row_a"]), int(f["row_b"])
        ja, jb = f["joint_a"], f["joint_b"]
        la, rra = _side(blocks.get(ja["left_block"])), _side(blocks.get(ja["right_block"]))
        lb, rrb = _side(blocks.get(jb["left_block"])), _side(blocks.get(jb["right_block"]))
        feat = al.nearest_feature(ctx, t)
        node_side = "NODE|FILL" if ("TIE" in (la[1], rra[1], lb[1], rrb[1])) else "FILL|FILL"
        key = (wi, round(t, 1), node_side, la, rra, lb, rrb) if ra % 2 == 0 else (wi, round(t, 1), node_side, lb, rrb, la, rra)
        inv = None
        for rec in b.inventory:
            pass
        e = sig.get(key)
        if e is None:
            e = {"project": b.short, "wall_id": f["wall"], "wall_idx": wi, "human_wall": ctx["human_wall"],
                 "wall_len": ctx["length_cm"], "t_cm": round(t, 2), "t_from_end_cm": round(ctx["length_cm"] - t, 2),
                 "node_side": node_side,
                 "even_row_joint": "{0}|{1}".format(la[0] if ra % 2 == 0 else lb[0], rra[0] if ra % 2 == 0 else rrb[0]),
                 "even_row_kinds": "{0}|{1}".format(la[1] if ra % 2 == 0 else lb[1], rra[1] if ra % 2 == 0 else rrb[1]),
                 "odd_row_joint": "{0}|{1}".format(lb[0] if ra % 2 == 0 else la[0], rrb[0] if ra % 2 == 0 else rra[0]),
                 "odd_row_kinds": "{0}|{1}".format(lb[1] if ra % 2 == 0 else la[1], rrb[1] if ra % 2 == 0 else rra[1]),
                 "nearest_feature": feat[0], "nearest_dist_cm": feat[1],
                 "row_pairs": [], "bands": set(), "human_verdicts": Counter()}
            sig[key] = e
        e["row_pairs"].append([ra, rb])
        e["bands"].add(al.band_of_course(b.run, ra))
        hv = None
        for rec in b.inventory:
            if rec["code"] == "PRISM_CONTINUOUS_JOINT" and rec["wall_id"] == f["wall"] and rec.get("rows") == sorted([ra, rb]) and abs((rec.get("t_cm") or -1) - t) < 0.05:
                hv = rec.get("human_verdict")
                break
        e["human_verdicts"][hv or "(sem humano)"] += 1
    rows = []
    for e in sig.values():
        e["bands"] = sorted(x for x in e["bands"] if x is not None)
        e["multiplicity"] = len(e["row_pairs"])
        e["human_verdicts"] = dict(e["human_verdicts"])
        rows.append(e)
    rows.sort(key=lambda e: (-e["multiplicity"], e["wall_id"], e["t_cm"]))
    al.write_json(al.out_path(b.short, "prism_signatures.json"), rows)
    return rows


def summarize(rows):
    s = {"unique_signatures": len(rows), "findings": sum(r["multiplicity"] for r in rows)}
    s["by_node_side"] = Counter(r["node_side"] for r in rows)
    s["findings_by_node_side"] = Counter()
    for r in rows:
        s["findings_by_node_side"][r["node_side"]] += r["multiplicity"]
    s["by_feature"] = Counter()
    for r in rows:
        s["by_feature"][(r["nearest_feature"], round(r["nearest_dist_cm"]))] += r["multiplicity"]
    s["by_feature"] = s["by_feature"].most_common(12)
    s["by_joint_pair"] = Counter()
    for r in rows:
        s["by_joint_pair"][(r["even_row_joint"], r["even_row_kinds"], r["odd_row_joint"], r["odd_row_kinds"])] += r["multiplicity"]
    s["by_joint_pair"] = s["by_joint_pair"].most_common(14)
    s["by_multiplicity"] = sorted(Counter(r["multiplicity"] for r in rows).items())
    hv = Counter()
    for r in rows:
        for k, v in r["human_verdicts"].items():
            hv[k] += v
    s["human_verdicts(findings)"] = hv
    s["by_wall(findings)"] = Counter()
    for r in rows:
        s["by_wall(findings)"][r["wall_id"]] += r["multiplicity"]
    s["by_wall(findings)"] = s["by_wall(findings)"].most_common(14)
    return s


def main(argv=None):
    ids = al.PROJECT_IDS if not argv else tuple(argv)
    out = {}
    for pid in ids:
        rows = build(pid)
        s = summarize(rows)
        out[al.SHORT[pid]] = s
        print("=====", al.SHORT[pid])
        for k, v in s.items():
            print("  ", k, ":", v)
    al.write_json(al.out_path("prism_signatures_summary.json"), out)


if __name__ == "__main__":
    main(sys.argv[1:])
