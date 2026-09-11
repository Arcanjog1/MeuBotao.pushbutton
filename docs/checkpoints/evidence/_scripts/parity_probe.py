# -*- coding: utf-8 -*-
"""Sonda do TETO de ganho da escolha de paridade por no' (Etapa 7 nunca
implementada): para cada no' T tocando uma parede REPROVADA pelo auditor,
inverte os rotulos A/B das duas pecas daquele no' (monkeypatch em
solve_all_intersections), re-resolve as 34 paredes de BUTANTA com as aberturas
reais e conta reprovacoes/compensadores. Medicao pura, nada e' alterado no
motor. Roda com a fileira de B34 desligada (default) e ligada."""
import json
import math
import os
import sys
import time
from collections import Counter

ROOT = r"C:\Users\twitc\Documents\AgentOrchestrator\MeuBotao.pushbutton"
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts"))
os.environ.setdefault("SCALE_BENCH_TESTS", os.path.join(ROOT, "tests"))
src = open(os.path.join(ROOT, "docs", "checkpoints", "evidence", "_scripts", "with_openings.py"), encoding="utf-8").read()
exec(src.split('print("\\n=== (B) AUDITOR')[0])   # walls, nodes, e2n, openings_per_wall, m, CATALOG, ids, frame

import core.engine.wall_stepper as ws  # noqa: E402

FLIP = set()
_orig = ws.solve_all_intersections


def _patched(nodes_, walls_, catalog_, openings_per_wall=None, end_to_node=None):
    out = _orig(nodes_, walls_, catalog_, openings_per_wall=openings_per_wall, end_to_node=end_to_node)
    for c in out["candidates"]:
        if c.get("node_index") in FLIP:
            c["course"] = "B" if c["course"] == "A" else "A"
    return out


ws.solve_all_intersections = _patched
m.solve_all_intersections = _patched


def solve():
    t0 = time.time()
    res = m.solve_building_blocks_all_courses(nodes, walls, e2n, openings_per_wall, CATALOG, 0.0, 14,
                                              variants_per_course=m.PIER_LAYOUT_VARIANTS_PER_COURSE)
    res["num_courses"] = 14
    pf = m.controlled_beta_preflight(res, walls, openings_per_wall, CATALOG, 0.0)
    aud = res["wall_bond_audits"]
    rep = sorted(wi for wi, a in aud.items() if not a["ok"])
    cc = res["course_candidates"]
    comp = sum(1 for v in cc.values() for c in v if c["logical_code"] in ("C09", "C04"))
    kinds = Counter()
    for wi in rep:
        for p in aud[wi]["problems"]:
            kinds[str(p).split(":")[0]] += 1
    return {"rep": rep, "n_rep": len(rep), "comp": comp, "pf": pf["ok"], "col": len(pf["collisions"]),
            "nmod": len(res["non_modular"] or []), "kinds": dict(kinds), "t": time.time() - t0}


t_nodes = [ni for ni, n in enumerate(nodes) if n["kind"] == "T_INTERSECTION"]
for flag in (False, True):
    ws.PREFER_B34_ROW_OVER_STACKED_COMPENSATORS = flag
    FLIP.clear()
    base = solve()
    print("\n##### PREFER_B34_ROW=%s | BASE: reprovadas=%d %s comp=%d nmod=%d pf=%s col=%d (%.1fs)" % (
        flag, base["n_rep"], [ids[w] for w in base["rep"]], base["comp"], base["nmod"], base["pf"], base["col"], base["t"]))
    print("   tipos: %s" % base["kinds"])
    cand_nodes = [ni for ni in t_nodes if nodes[ni]["main_wall_idx"] in base["rep"] or nodes[ni]["incoming_wall_idx"] in base["rep"]]
    print("   nos T tocando paredes reprovadas: %d" % len(cand_nodes))
    results = []
    for ni in cand_nodes:
        FLIP.clear(); FLIP.add(ni)
        r = solve()
        n = nodes[ni]
        gain = base["n_rep"] - r["n_rep"]
        results.append((gain, ni, r))
        print("   flip no %3d (main %d, chega %d): reprovadas=%2d (%+d) comp=%d nmod=%d pf=%s col=%d" % (
            ni, ids[n["main_wall_idx"]], ids[n["incoming_wall_idx"]], r["n_rep"], -gain, r["comp"], r["nmod"], r["pf"], r["col"]))
    # guloso: acumula flips que melhoram
    FLIP.clear(); cur = base
    for gain, ni, r in sorted(results, key=lambda x: -x[0]):
        if gain <= 0:
            break
        FLIP.add(ni)
        r2 = solve()
        if r2["n_rep"] < cur["n_rep"] and r2["pf"]:
            cur = r2
        else:
            FLIP.discard(ni)
    print("   GULOSO: flips=%s -> reprovadas=%d %s comp=%d nmod=%d pf=%s" % (
        sorted(FLIP), cur["n_rep"], [ids[w] for w in cur["rep"]], cur["comp"], cur["nmod"], cur["pf"]))
    print("   tipos apos guloso: %s" % cur["kinds"])
