"""Varredura em busca de um REPRODUCER REDUZIDO do mecanismo cross-band.

Diferenca para a `sweep.py` (que falhou, como as tres tentativas ja'
versionadas): duas aberturas em COTAS diferentes, com peitoril/verga que
caem no MEIO de uma fiada. Isso e' o que o projeto real tem e o que os
cenarios anteriores nao tinham - a grade de bandas deixa de ser
{abaixo da verga, acima da verga} e passa a ter BANDAS DE UMA FIADA SO'
(a fiada que o peitoril/verga atravessa), que e' onde as 12 identidades
do G12 caem.
"""
import sys, itertools
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

TH, H, STEP, BH, NC = 14.0, 340.0, 20.0, 19.0, 17
CAT = {c: {"length_cm": l, "height_cm": BH, "width_cm": TH} for c, l in
       (("B39", 39.0), ("B34", 34.0), ("B19", 19.0), ("B54", 54.0),
        ("C09", 9.0), ("C04", 4.0))}
MOD = solver_bridge.engine()


def cenario(L, porta, janela, tipo, node_off=7.0):
    ops = [model.make_opening("door", porta[0], porta[1], 0.0, porta[2], confidence="measured"),
           model.make_opening("window", janela[0], janela[1], janela[2], janela[3],
                              confidence="measured")]
    alvo = model.make_wall("ALVO", (0.0, 0.0), (L, 0.0), TH, base_z_cm=0.0,
                           height_cm=H, openings=ops, junctions=[], rows=[])
    y1 = 0.0 if tipo == "L" else -300.0
    p1 = model.make_wall("P1", (node_off, y1), (node_off, 300.0), TH, base_z_cm=0.0, height_cm=H)
    p2 = model.make_wall("P2", (L - node_off, y1), (L - node_off, 300.0), TH,
                         base_z_cm=0.0, height_cm=H)
    return model.assign_ids(model.make_project(
        "sweep2", "input", walls=[alvo, p1, p2],
        settings={"base_z_cm": 0.0, "course_step_cm": STEP, "block_height_cm": BH,
                  "num_courses": NC, "expected_rows": NC},
        catalog=CAT))


def roda(inp):
    res, walls, nodes, ops, cat, bz, nc, notes = solver_bridge.run_solver(inp)
    out = from_solver.project_from_solver("sweep2", res, walls, nodes, ops, cat, bz, nc)
    f, _e = validators.run_all(out, {})
    ch, _ = MOD._course_height_ft(cat, None)
    bh = ch - MOD._cm_to_ft(MOD.COURSE_JOINT_CM)
    groups = MOD._group_course_indices_by_opening_band(ops, bz, ch, bh, nc)
    band_of = {ci: bi for bi, (cis, _x) in enumerate(groups) for ci in cis}
    alvo = max(out["walls"], key=lambda w: w["length_cm"])
    ordem = {r["row"]: i for i, r in enumerate(sorted(alvo["rows"], key=lambda r: r["elevation_cm"]))}
    cont = [x for x in f if x["code"] == "PRISM_CONTINUOUS_JOINT" and x["wall"] == alvo["id"]]
    cross = [x for x in cont
             if band_of.get(ordem.get(x["row_a"])) != band_of.get(ordem.get(x["row_b"]))]
    return cont, cross, groups, alvo


achados = []
combos = 0
MOD.CROSS_BAND_JOINT_PROPAGATION_ENABLED = False
for L in (339.0, 419.0, 499.0, 579.0, 659.0, 739.0, 819.0, 899.0, 939.0):
    for pverga in (140.0, 160.0, 170.0, 210.0):
        for peit, jverga in ((110.0, 210.0), (95.0, 215.0), (105.0, 225.0), (130.0, 230.0)):
            for pt0 in (54.0, 94.0, 134.0):
                pt1 = pt0 + 91.0
                for jt0 in (pt1 + 60.0, pt1 + 100.0, pt1 + 140.0):
                    jt1 = jt0 + 121.0
                    if jt1 > L - 60.0:
                        continue
                    for tipo in ("T", "L"):
                        combos += 1
                        inp = cenario(L, (pt0, pt1, pverga), (jt0, jt1, peit, jverga), tipo)
                        try:
                            cont, cross, groups, alvo = roda(inp)
                        except Exception:
                            continue
                        if cross:
                            achados.append((L, pt0, pt1, pverga, jt0, jt1, peit, jverga, tipo,
                                            len(cont), len(cross), [g[0] for g in groups]))
print("combinacoes:", combos, "| com cross-band:", len(achados))
for a in sorted(achados, key=lambda x: (x[10], -x[9]), reverse=True)[:15]:
    print("  L=%.0f porta=%.0f..%.0f/h%.0f janela=%.0f..%.0f/%.0f..%.0f no=%s -> total=%d cross=%d bandas=%s"
          % a)
