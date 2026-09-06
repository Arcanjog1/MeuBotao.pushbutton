# -*- coding: utf-8 -*-
"""PRIMEIRA DIVERGENCIA solver x humano (item 18): para cada parede casada
(pontas iguais) e cada fiada, percorre o eixo do solver de t=0 em diante e
acha o PRIMEIRO trecho em que a composicao do solver deixa de coincidir
com a humana (fronteira ou codigo). Classifica o ESTAGIO do pipeline em
que a peca divergente do solver nasceu (peca de no', preenchimento
continuo, reparo de abertura, vazio) e o que o humano tem ali.

Equivalencias de codigo (catalogo humano tem canaletas/cortados que o
solver nao conhece): CJ19~B19, CAN39~B39, CAN34~B34, CM19~B19, *_C ~ base.

    <SHORT>/first_divergence.json
    first_divergence_summary.json
"""
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import atlas_lib as al  # noqa: E402
from benchmark.comparator import match  # noqa: E402

TOL = 1.5
EQUIV = {"CJ19": "B19", "CAN39": "B39", "CAN34": "B34", "CM19": "B19"}


def norm_code(code):
    code = (code or "?").split("_C")[0]
    return EQUIV.get(code, code)


def stage_of(item):
    if item is None:
        return "SOLVER_EMPTY"
    if not item.get("is_own", True):
        return "FOREIGN_NODE_PIECE"
    reason = item.get("reason") or ""
    if al.is_tie_reason(reason):
        return "NODE_PIECE_DEGRADED" if "DEGRADED" in reason else "NODE_PIECE"
    if reason == "OPENING_REPAIR_FILL":
        return "OPENING_REPAIR"
    return "CONTINUOUS_FILL"


def first_divergence(solver_items, human_items, length_cm):
    """Devolve None se identicas (a menos de equivalencias), senao dict."""
    s = [it for it in solver_items if it["t1"] > -1.0 and it["t0"] < length_cm + 1.0]
    h = [it for it in human_items if it["t1"] > -1.0 and it["t0"] < length_cm + 1.0]
    i = j = 0
    while i < len(s) or j < len(h):
        si = s[i] if i < len(s) else None
        hj = h[j] if j < len(h) else None
        if si is None or hj is None:
            item = si or hj
            return {"t": round(item["t0"], 1), "solver": None if si is None else (si["code"], si["t0"], si["t1"], si.get("reason"), si.get("is_own", True)),
                    "human": None if hj is None else (hj["code"], hj["t0"], hj["t1"]), "kind": "SOLVER_EXTRA" if hj is None else "HUMAN_EXTRA",
                    "stage": stage_of(si)}
        if abs(si["t0"] - hj["t0"]) <= TOL and abs(si["t1"] - hj["t1"]) <= TOL:
            if norm_code(si["code"]) != norm_code(hj["code"]):
                return {"t": round(si["t0"], 1), "solver": (si["code"], si["t0"], si["t1"], si.get("reason"), si.get("is_own", True)),
                        "human": (hj["code"], hj["t0"], hj["t1"]), "kind": "SAME_EXTENT_DIFF_CODE", "stage": stage_of(si)}
            i += 1
            j += 1
            continue
        # fronteiras diferentes: quem comeca primeiro define o t da divergencia
        t = min(si["t0"], hj["t0"])
        return {"t": round(t, 1), "solver": (si["code"], si["t0"], si["t1"], si.get("reason"), si.get("is_own", True)),
                "human": (hj["code"], hj["t0"], hj["t1"]), "kind": "LAYOUT", "stage": stage_of(si if si["t0"] <= hj["t0"] + TOL else None)}
    return None


def build(project_id):
    b = al.Bundle(project_id)
    rows = []
    for sw in b.result["walls"]:
        hid = b.pairs.get(sw["id"])
        if not hid:
            continue
        hw = b.ref_by_id[hid]
        cost = match.score_pair(sw, hw)
        endpoints = cost is not None and cost <= 10
        wi = b.idx(sw["id"])
        ctx = b.ctx(wi)
        for ci in range(b.run["num_courses"]):
            # SO' pecas PROPRIAS dos dois lados: o humano atribui cada bloco a
            # UMA parede; o corpo da peca de no' da vizinha aparece como vazio
            # nas duas fontes.
            s_items = [it for it in b.solver_row(wi, ci, include_secondary=True) if it["is_own"]]
            h_items = b.human_row(wi, ci) or []
            div = first_divergence(s_items, h_items, ctx["length_cm"])
            rows.append({
                "project": b.short, "wall_id": sw["id"], "wall_idx": wi, "human_wall": hid,
                "endpoints_match": endpoints, "wall_len": ctx["length_cm"], "row": ci,
                "letter": al.course_letter(ci), "band": al.band_of_course(b.run, ci),
                "identical": div is None,
                "divergence": div,
                "feature_at_t": None if div is None else al.nearest_feature(ctx, div["t"])[:2],
            })
    al.write_json(al.out_path(b.short, "first_divergence.json"), rows)
    # PARIDADE por no': em que parede fica a peca de no' da fiada PAR (row 0)
    # no solver x no humano (mesma fiada fisica, por elevacao).
    from benchmark.validators import validate_junctions as vj
    parity = []
    for ni, node in enumerate(b.run["nodes"]):
        kind = node.get("kind")
        if kind not in ("L_CORNER", "T_INTERSECTION", "X_INTERSECTION"):
            continue
        pt = al.xyz_cm(node["point"])
        walls = set(a[0] for a in node.get("arms") or [])
        for k in ("main_wall_idx", "incoming_wall_idx"):
            if node.get(k) is not None:
                walls.add(node[k])
        for w in node.get("crossing_walls") or []:
            if w is not None:
                walls.add(w)
        if any(b.idx_to_id.get(w) not in b.pairs for w in walls):
            continue
        sol = {}
        for c in b.node_pieces.get(ni, []):
            sol.setdefault(c["course"], set()).add(b.idx_to_id[c["wall_idx"]])
        hum = {0: set(), 1: set()}
        for w in walls:
            hw = b.ref_by_id[b.pairs[b.idx_to_id[w]]]
            for row in hw["rows"]:
                if row["row"] not in (0, 1):
                    continue
                for bl in row["blocks"]:
                    if vj.block_covers_point(bl, pt):
                        hum[row["row"]].add((hw["id"], bl["code"]))
        parity.append({"node_index": ni, "kind": kind, "walls": sorted(b.idx_to_id[w] for w in walls),
                       "solver_A": sorted(sol.get("A", [])), "solver_B": sorted(sol.get("B", [])),
                       "human_row0": sorted(hum[0]), "human_row1": sorted(hum[1])})
    al.write_json(al.out_path(b.short, "node_parity.json"), parity)
    return rows


def summarize(rows):
    s = {}
    ep = [r for r in rows if r["endpoints_match"]]
    s["rows_compared(endpoint-matched walls)"] = len(ep)
    s["identical_rows"] = sum(1 for r in ep if r["identical"])
    s["walls_endpoint_matched"] = len(set(r["wall_id"] for r in ep))
    s["walls_all_rows_identical"] = len(set(r["wall_id"] for r in ep) - set(r["wall_id"] for r in ep if not r["identical"]))
    div = [r for r in ep if not r["identical"]]
    s["by_stage(rows)"] = Counter(r["divergence"]["stage"] for r in div).most_common()
    s["by_kind(rows)"] = Counter(r["divergence"]["kind"] for r in div).most_common()
    s["by_feature(rows)"] = Counter((r["feature_at_t"][0]) for r in div).most_common(10)
    # primeira divergencia POR PAREDE (menor t entre as fiadas 0 e 1)
    per_wall = {}
    for r in div:
        if r["row"] in (0, 1):
            cur = per_wall.get(r["wall_id"])
            if cur is None or r["divergence"]["t"] < cur["divergence"]["t"]:
                per_wall[r["wall_id"]] = r
    s["walls_diverging_in_band0"] = len(per_wall)
    s["per_wall_stage"] = Counter(r["divergence"]["stage"] for r in per_wall.values()).most_common()
    s["per_wall_feature"] = Counter(r["feature_at_t"][0] for r in per_wall.values()).most_common(10)
    s["per_wall_solver_vs_human"] = Counter(
        ("{0}({1})".format(r["divergence"]["solver"][0], r["divergence"]["solver"][3]) if r["divergence"]["solver"] else "NONE",
         r["divergence"]["human"][0] if r["divergence"]["human"] else "NONE")
        for r in per_wall.values()).most_common(20)
    s["examples"] = [(w, r["row"], r["divergence"]) for w, r in sorted(per_wall.items())[:12]]
    return s


def main(argv=None):
    ids = ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1") if not argv else tuple(argv)
    out = {}
    for pid in ids:
        rows = build(pid)
        s = summarize(rows)
        out[al.SHORT[pid]] = s
        print("=====", al.SHORT[pid])
        for k, v in s.items():
            print("  ", k, ":", v)
    al.write_json(al.out_path("first_divergence_summary.json"), out)


if __name__ == "__main__":
    main(sys.argv[1:])
