# -*- coding: utf-8 -*-
"""CADEIAS DE COMPENSADORES (item 10): censo fisico de toda sequencia de
>=2 compensadores encostados, com o CONTEXTO que a produziu (o que limita
o trecho de cada lado, a banda, o comprimento do residuo) e a composicao
HUMANA no mesmo intervalo. Deduplica por assinatura fisica (a mesma cadeia
repetida em N fiadas da mesma paridade conta uma vez, com multiplicidade).

    <SHORT>/compensator_chains.json
    compensator_chains_summary.json
"""
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402

COMP = ("C09", "C04")


def _neighbor_kind(item, ctx):
    if item is None:
        return "NONE"
    if not item["is_own"]:
        return "TIE_FOREIGN"
    if al.is_tie_reason(item["reason"]):
        return "TIE_OWN"
    if item["reason"] == "OPENING_REPAIR_FILL":
        return "FILL_REPAIR"
    return "FILL_STD"


def _boundary_at(ctx, t, side, run, course_index):
    """O que limita o trecho quando nao ha' peca vizinha: abertura ativa,
    ponta livre, no' sem peca (reserva), fim de parede."""
    for op in al.openings_active_in_course(ctx, run, course_index):
        if side == "left" and abs(op["t1"] - t) <= 2.0:
            return "OPENING"
        if side == "right" and abs(op["t0"] - t) <= 2.0:
            return "OPENING"
    end = ctx["ends"][0] if side == "left" else ctx["ends"][1]
    if abs((0.0 if side == "left" else ctx["length_cm"]) - t) <= 2.0:
        return "FREE_END" if end["kind"] in ("NONE", "FREE_END", "STRAIGHT_CONTINUATION") else "WALL_END_" + end["kind"]
    if abs(end["t_cm"] - t) <= 20.0 and end["kind"] not in ("NONE", "FREE_END"):
        return "NODE_RESERVE_" + end["kind"]
    for m in ctx["midspan_nodes"]:
        if abs(m["t_cm"] - t) <= 30.0:
            return "NODE_RESERVE_MID_" + m["kind"]
    return "GAP"


def _human_span(items, lo, hi):
    if items is None:
        return None
    return [it["code"] for it in items if it["t1"] > lo + 0.5 and it["t0"] < hi - 0.5]


def build(project_id):
    b = al.Bundle(project_id)
    chains = {}
    for wi in range(len(b.run["walls_to_create"])):
        ctx = b.ctx(wi)
        for ci in range(b.run["num_courses"]):
            items = b.solver_row(wi, ci, include_secondary=True)
            own = [it for it in items if it["is_own"]]
            i = 0
            while i < len(own):
                if own[i]["code"] not in COMP:
                    i += 1
                    continue
                j = i
                while j + 1 < len(own) and own[j + 1]["code"] in COMP and own[j + 1]["t0"] - own[j]["t1"] <= 5.0:
                    j += 1
                if j > i:
                    run_items = own[i:j + 1]
                    left = own[i - 1] if i > 0 and run_items[0]["t0"] - own[i - 1]["t1"] <= 5.0 else None
                    right = own[j + 1] if j + 1 < len(own) and own[j + 1]["t0"] - run_items[-1]["t1"] <= 5.0 else None
                    # vizinho estrangeiro (peca de no' da parede vizinha) encostado?
                    if left is None:
                        for it in items:
                            if not it["is_own"] and abs(it["t1"] - run_items[0]["t0"]) <= 5.0:
                                left = it
                    if right is None:
                        for it in items:
                            if not it["is_own"] and abs(it["t0"] - run_items[-1]["t1"]) <= 5.0:
                                right = it
                    lo, hi = run_items[0]["t0"], run_items[-1]["t1"]
                    lk = _neighbor_kind(left, ctx) if left is not None else _boundary_at(ctx, lo, "left", b.run, ci)
                    rk = _neighbor_kind(right, ctx) if right is not None else _boundary_at(ctx, hi, "right", b.run, ci)
                    codes = "+".join(it["code"] for it in run_items)
                    reasons = sorted(set(it["reason"] for it in run_items))
                    key = (wi, al.course_letter(ci), round(lo, 1), round(hi, 1), codes)
                    hum = b.human_row(wi, ci)
                    entry = chains.get(key)
                    if entry is None:
                        entry = {
                            "project": b.short, "wall_idx": wi, "wall_id": ctx["wall_id"],
                            "human_wall": ctx["human_wall"], "in_scope": ctx.get("in_scope", True),
                            "wall_len": ctx["length_cm"], "orientation": ctx["orientation"],
                            "letter": al.course_letter(ci), "courses": [],
                            "t_lo": round(lo, 2), "t_hi": round(hi, 2), "span_cm": round(hi - lo, 2),
                            "codes": codes, "n": len(run_items), "reasons": reasons,
                            "left": lk, "right": rk,
                            "left_piece": None if left is None else (left["code"], left["reason"], left["is_own"]),
                            "right_piece": None if right is None else (right["code"], right["reason"], right["is_own"]),
                            "nearest_feature": al.nearest_feature(ctx, (lo + hi) / 2.0)[:2],
                            "openings_active": [o["kind"] for o in al.openings_active_in_course(ctx, b.run, ci)],
                            "human_same_span": _human_span(hum, lo, hi),
                            "human_context_span": _human_span(hum, lo - 40, hi + 40),
                        }
                        chains[key] = entry
                    entry["courses"].append(ci)
                    i = j + 1
                else:
                    i += 1
    rows = sorted(chains.values(), key=lambda e: (e["wall_id"] or "", e["letter"], e["t_lo"]))
    al.write_json(al.out_path(b.short, "compensator_chains.json"), rows)
    return rows


def summarize(rows):
    s = {}
    s["unique_chains"] = len(rows)
    s["finding_equivalent(pairs x courses)"] = sum((r["n"] - 1) * len(r["courses"]) for r in rows)
    s["by_codes"] = Counter(r["codes"] for r in rows).most_common(12)
    s["by_context"] = Counter((r["left"], r["right"]) for r in rows).most_common(15)
    s["by_reasons"] = Counter("+".join(r["reasons"]) for r in rows).most_common(8)
    s["by_span"] = sorted(Counter(round(r["span_cm"]) for r in rows).items())
    hum = Counter()
    for r in rows:
        h = r["human_same_span"]
        if h is None:
            hum["(sem humano)"] += 1
        elif not h:
            hum["HUMAN_EMPTY"] += 1
        else:
            hum["+".join(h)] += 1
    s["human_same_span"] = hum.most_common(15)
    s["by_wall"] = Counter(r["wall_id"] for r in rows).most_common(12)
    s["weighted_by_wall(pairs x courses)"] = Counter()
    for r in rows:
        s["weighted_by_wall(pairs x courses)"][r["wall_id"]] += (r["n"] - 1) * len(r["courses"])
    s["weighted_by_wall(pairs x courses)"] = s["weighted_by_wall(pairs x courses)"].most_common(12)
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
    al.write_json(al.out_path("compensator_chains_summary.json"), out)


if __name__ == "__main__":
    main(sys.argv[1:])
