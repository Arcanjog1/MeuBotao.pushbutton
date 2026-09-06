# -*- coding: utf-8 -*-
"""CLUSTERING CAUSAL AUTOMATICO (item 16/25): atribui a cada achado de
nivel 1 UM cluster causal primario, por regras sobre o contexto fisico ja'
medido (inventory, coverage_decomposition, compensator_chains,
prism_signatures, openings_decomposition, geometria dos nos). Gera as
contagens por cluster x projeto x codigo usadas no atlas.

    <SHORT>/cluster_assignment.json ; cluster_summary.json
"""
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402
from benchmark.comparator import match  # noqa: E402

LEVEL2 = ("PRISM_STAGGER_BELOW_TARGET", "COMPENSATOR_AVOIDABLE", "OPENING_MISSING_LINTEL",
          "OPENING_MISSING_COUNTER_LINTEL", "JUNCTION_WRONG_PIECE")


def _wall_class(b, wi):
    ctx = b.ctx(wi)
    if not ctx.get("in_scope", True):
        return "OUT_OF_SCOPE"
    hws = b.human_overlaps(wi)
    if not hws:
        return "SPURIOUS_OR_UNBUILT"
    sw = b.res_by_id[ctx["wall_id"]]
    if any((match.score_pair(sw, h) or 1e9) <= 10 for h in hws):
        return "ENDPOINT_MATCH"
    return "COLLINEAR_FRAGMENT"


def _rotated_nodes(b):
    out = set()
    for ni, node in enumerate(b.run["nodes"]):
        if node.get("kind") != "L_CORNER":
            continue
        owners = set(c["wall_idx"] for c in b.node_pieces.get(ni, []))
        if len(owners) == 1 and b.node_pieces.get(ni):
            out.add(ni)
    return out


def _walls_with_rotated(b, rotated):
    walls = set()
    for ni in rotated:
        for w, _e in b.run["nodes"][ni].get("arms") or []:
            walls.add(w)
    return walls


def _fit_distance(x):
    import math
    L = x["current_length_cm"]
    base = x["leading_joint_cm"] + x["trailing_joint_cm"] - 1.0
    m = (L - base) / 5.0
    return min(abs(L - (base + 5 * math.floor(m))), abs(L - (base + 5 * math.ceil(m))))


def build(project_id):
    b = al.Bundle(project_id)
    rotated = _rotated_nodes(b)
    rotated_walls = _walls_with_rotated(b, rotated)
    failures = set(ni for ni, _r in (b.run["solve_result"].get("intersection_failures") or []))
    cov = dict()
    for r in al.read_json(al.out_path(b.short, "coverage_decomposition.json")):
        cov.setdefault((r["code"], r["wall_id"], r.get("row"), tuple(r.get("gap") or [])), r)
    chains = al.read_json(al.out_path(b.short, "compensator_chains.json"))
    prism = al.read_json(al.out_path(b.short, "prism_signatures.json"))
    opens = al.read_json(al.out_path(b.short, "openings_decomposition.json"))
    nm_by_wall = defaultdict(list)
    for x in b.run["solve_result"].get("non_modular") or []:
        nm_by_wall[x["wall_idx"]].append(x)

    def fit_cluster(wi):
        cls = _wall_class(b, wi)
        fits = [x for x in nm_by_wall.get(wi, []) if x.get("conflict") is None]
        dmin = min((_fit_distance(x) for x in fits), default=None)
        if b.short == "TGD" and cls in ("COLLINEAR_FRAGMENT", "SPURIOUS_OR_UNBUILT", "OUT_OF_SCOPE"):
            return "C08_PHASEA_FRAGMENT_NONMODULAR"
        if dmin is not None and dmin <= 0.5:
            return "C04_FIT_TOLERANCE_NOISE"
        return "C04b_NONMODULAR_TRECHO_GEOMETRY"

    def chain_for(wall_id, row, t):
        best = None
        for c in chains:
            if c["wall_id"] == wall_id and row in c["courses"] and c["t_lo"] - 1.5 <= t <= c["t_hi"] + 1.5:
                best = c
                break
        return best

    def chain_cluster(c, wi):
        ctx = b.ctx(wi)
        reasons = "+".join(c["reasons"])
        lp, rp = c.get("left_piece"), c.get("right_piece")
        deg = ("DEGRADED" in reasons) or (lp and "DEGRADED" in str(lp[1])) or (rp and "DEGRADED" in str(rp[1]))
        xdeg = (lp and "X_INTERSECTION_DEGRADED" in str(lp[1])) or (rp and "X_INTERSECTION_DEGRADED" in str(rp[1]))
        if xdeg:
            return "C02_X_ROOM_BORDERLINE_DEGRADED"
        if ctx["length_cm"] <= 130 and ctx["ends"][0]["kind"] not in ("NONE", "FREE_END") and ctx["ends"][1]["kind"] not in ("NONE", "FREE_END"):
            return "C01_SHORT_WALL_NODE_ROLE"
        if c["left"] == "TIE_OWN" and c["right"] == "TIE_OWN":
            return "C03_NODE_INSIDE_OPENING_SPAN"
        if deg:
            return "C05_DEGRADED_NODE_PIECE_RESIDUE"
        if "OPENING_REPAIR_FILL" in reasons or "OPENING" in (c["left"], c["right"]):
            return "C06_REPAIR_RESIDUE_NEAR_OPENING"
        if b.short == "TGD" and _wall_class(b, wi) in ("COLLINEAR_FRAGMENT", "SPURIOUS_OR_UNBUILT"):
            return "C08_PHASEA_FRAGMENT_NONMODULAR"
        return "C07_FILL_RESIDUE_BETWEEN_TIES"

    prism_index = {}
    for p in prism:
        for ra, rb in p["row_pairs"]:
            prism_index[(p["wall_id"], ra, rb, p["t_cm"])] = p

    def prism_cluster(f, wi):
        ctx = b.ctx(wi)
        p = prism_index.get((f["wall"], int(f["row_a"]), int(f["row_b"]), round(float(f["joint_t_cm"]), 2)))
        if wi in rotated_walls and p is not None and p["nearest_feature"] == "NODE_END_L_CORNER" and p["nearest_dist_cm"] <= 30:
            return "C09_ROTATED_CORNER_SAME_WALL"
        kinds = (p["even_row_kinds"] + "|" + p["odd_row_kinds"]) if p else ""
        joints = (p["even_row_joint"] + "|" + p["odd_row_joint"]) if p else ""
        if "REPAIR" in kinds:
            return "C10_REPAIR_ANCHOR_RECREATES_NODE_JOINT"
        if any(m["degraded"] and m["kind"] == "X_INTERSECTION" and abs(m["t_cm"] - float(f["joint_t_cm"])) < 40 for m in ctx["midspan_nodes"]):
            return "C02_X_ROOM_BORDERLINE_DEGRADED"
        if ctx["length_cm"] <= 130 and ctx["ends"][0]["kind"] not in ("NONE", "FREE_END") and ctx["ends"][1]["kind"] not in ("NONE", "FREE_END"):
            return "C01_SHORT_WALL_NODE_ROLE"
        if "C09|C09" in joints:
            return "C05_DEGRADED_NODE_PIECE_RESIDUE" if any("DEGRADED" in str(pc["reason"]) for e in ctx["ends"].values() for pc in e["pieces"]) else "C07_FILL_RESIDUE_BETWEEN_TIES"
        if p and p["node_side"] == "NODE|FILL":
            return "C11_NODE_FILL_JOINT_RESIDUAL"
        return "C12_FILL_FILL_PRISM_OTHER"

    assign = []
    for f in b.findings():
        if f["level"] != 1 or not f.get("wall"):
            continue
        wi = b.idx(f["wall"])
        ctx = b.ctx(wi)
        code = f["code"]
        cluster = "UNASSIGNED"
        if code.startswith("COVERAGE_"):
            key = (code, f["wall"], f.get("row"), tuple(f.get("gap_t_cm") or []))
            r = cov.get(key)
            prim = r["primary"] if r else "UNKNOWN"
            if prim in ("NON_MODULAR_FIT",):
                cluster = fit_cluster(wi)
            elif prim == "NON_MODULAR_SEM_ESPACO":
                cluster = "C13_NODE_RESERVE_EXCEEDS_WALL(SEM_ESPACO)"
            elif prim == "FOREIGN_PIECE_COVERS":
                cluster = "V01_VALIDATOR_FOREIGN_PIECE_NOT_CREDITED"
            elif prim == "NODE_RESERVE_DEGRADED_SHORT":
                cluster = "C05_DEGRADED_NODE_PIECE_RESIDUE"
            elif prim.startswith("NODE_UNBOUND_RESERVE(intersection_failure"):
                cluster = "C14_INTERSECTION_FAILURE_NO_PIECE"
            elif prim.startswith("NODE_UNBOUND_RESERVE"):
                cluster = "C15_NODE_RESERVE_WITHOUT_PIECE_THIS_COURSE"
            elif prim == "OPENING_REPAIR_FAILED":
                cluster = "C16_OPENING_REPAIR_FAILED"
            elif prim == "DROPPED_FILL_COLLISION":
                cluster = "C17_FILL_DROPPED_BY_TIE_COLLISION"
            elif prim == "MIDSPAN_NODE_NO_PIECE_THIS_COURSE":
                cluster = "C15_NODE_RESERVE_WITHOUT_PIECE_THIS_COURSE"
            elif prim.startswith("TINY_WALL"):
                cluster = "C08_PHASEA_FRAGMENT_NONMODULAR"
            else:
                cluster = "UNKNOWN_COVERAGE"
        elif code in ("COMPENSATOR_CONSECUTIVE", "COMPENSATOR_EXCESS_IN_RUN", "COMPENSATOR_VERTICAL_STRIP"):
            t = f.get("t_cm")
            if isinstance(t, list):
                t = (t[0] + t[1]) / 2.0
            if t is None and f.get("run_t_cm"):
                t = (f["run_t_cm"][0] + f["run_t_cm"][1]) / 2.0
            row = f.get("row")
            if row is None and f.get("rows"):
                row = f["rows"][0]
            c = chain_for(f["wall"], row, t) if t is not None else None
            if c is None and code == "COMPENSATOR_EXCESS_IN_RUN":
                # procura qualquer cadeia no trecho
                for cc in chains:
                    if cc["wall_id"] == f["wall"] and row in cc["courses"] and f["run_t_cm"][0] - 1 <= cc["t_lo"] and cc["t_hi"] <= f["run_t_cm"][1] + 1:
                        c = cc
                        break
            cluster = chain_cluster(c, wi) if c else ("C08_PHASEA_FRAGMENT_NONMODULAR" if (b.short == "TGD" and _wall_class(b, wi) != "ENDPOINT_MATCH") else "C07_FILL_RESIDUE_BETWEEN_TIES")
        elif code == "PRISM_CONTINUOUS_JOINT":
            cluster = prism_cluster(f, wi)
        elif code == "PRISM_JOINT_STACK":
            cluster = "D01_DERIVED_FROM_PRISM_CONTINUOUS"
        elif code == "JUNCTION_NOT_ALTERNATING":
            cluster = "C09_ROTATED_CORNER_SAME_WALL" if wi in rotated_walls else "C18_JUNCTION_NOT_ALTERNATING_OTHER"
        elif code == "JUNCTION_MISSING_BINDING":
            cluster = "C19_L_ARM_NOT_EXTENDED_OR_C04_TOO_SHORT"
        elif code in ("OPENING_BLOCK_CROSSES_JAMB", "OPENING_BLOCK_INSIDE_DOOR", "OPENING_BLOCK_INSIDE_WINDOW"):
            o = next((r for r in opens if r["code"] == code and r["wall_id"] == f["wall"] and r.get("row") == f.get("row") and r.get("opening") == f.get("opening")), None)
            cause = o["cause"] if o else "?"
            if cause == "NODE_PIECE_AT_NODE_INSIDE_OPENING_SPAN":
                cluster = "C03_NODE_INSIDE_OPENING_SPAN"
            else:
                cluster = "C20_NODE_PIECE_ROOM_CHECK_MISS"
        elif code == "OPENING_SOLID_BELOW_SILL_MISSING":
            cluster = fit_cluster(wi)
        elif code == "POSITION_OVERLAP":
            cluster = "C21_NODE_PIECES_COLLIDE"
        elif code == "COVERAGE_ORPHAN_BLOCKS":
            cluster = "V02_VALIDATOR"
        assign.append({"code": code, "wall_id": f["wall"], "wall_idx": wi, "row": f.get("row", f.get("row_a")),
                       "cluster": cluster, "wall_class": _wall_class(b, wi), "human": ctx["human_wall"]})
    al.write_json(al.out_path(b.short, "cluster_assignment.json"), assign)
    return assign


def main():
    out = {}
    grand = Counter()
    for pid in al.PROJECT_IDS:
        rows = build(pid)
        by = Counter(r["cluster"] for r in rows)
        bycode = Counter((r["cluster"], r["code"]) for r in rows)
        byclass = Counter((r["cluster"], r["wall_class"]) for r in rows)
        out[al.SHORT[pid]] = {"total_level1": len(rows), "by_cluster": by.most_common(),
                              "by_cluster_code": {"{0}|{1}".format(k[0], k[1]): v for k, v in bycode.items()},
                              "by_cluster_wallclass": {"{0}|{1}".format(k[0], k[1]): v for k, v in byclass.items()},
                              "walls_by_cluster": {c: sorted(set(r["wall_id"] for r in rows if r["cluster"] == c))[:40] for c in by}}
        for k, v in by.items():
            grand[k] += v
        print("=====", al.SHORT[pid], "level-1 findings:", len(rows))
        for k, v in by.most_common():
            codes = Counter(r["code"] for r in rows if r["cluster"] == k).most_common(4)
            print("   %5d  %-46s %s" % (v, k, codes))
    out["ALL"] = grand.most_common()
    al.write_json(al.out_path("cluster_summary.json"), out)


if __name__ == "__main__":
    main()
