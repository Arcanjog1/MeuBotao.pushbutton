"""Terceira geracao do reproducer: acrescenta o ingrediente que faltava nas
tres tentativas ja' versionadas E na sweep2 - um encontro T NO MEIO do eixo.

Por que ele importa (medido em W072/TGD, ver o relatorio): a junta que a
fronteira de banda empilha nao e' uma junta qualquer - de um lado ela e' a
BORDA DE UMA PECA DE AMARRACAO (B54 de um T de meio de parede), cuja
posicao NAO depende de layout nenhum e que o preenchimento nao tem como
mover. Quem tinha de sair da frente era a fiada da OUTRA banda. Sem um no'
de meio de parede, todas as juntas do eixo sao moveis e o acaso resolve.
"""
import sys
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

TH, H, STEP, BH, NC = 14.0, 340.0, 20.0, 19.0, 15
CAT = {c: {"length_cm": l, "height_cm": BH, "width_cm": TH} for c, l in
       (("B39", 39.0), ("B34", 34.0), ("B19", 19.0), ("B54", 54.0),
        ("C09", 9.0), ("C04", 4.0))}
MOD = solver_bridge.engine()
MOD.CROSS_BAND_JOINT_PROPAGATION_ENABLED = False


def cenario(L, tmid, janela, node_off=7.0):
    ops = [model.make_opening("window", janela[0], janela[1], janela[2], janela[3],
                              confidence="measured")]
    alvo = model.make_wall("ALVO", (0.0, 0.0), (L, 0.0), TH, base_z_cm=0.0,
                           height_cm=H, openings=ops, junctions=[], rows=[])
    p1 = model.make_wall("P1", (node_off, 0.0), (node_off, 300.0), TH, base_z_cm=0.0, height_cm=H)
    p2 = model.make_wall("P2", (L - node_off, 0.0), (L - node_off, 300.0), TH,
                         base_z_cm=0.0, height_cm=H)
    pm = model.make_wall("PM", (tmid, 0.0), (tmid, 300.0), TH, base_z_cm=0.0, height_cm=H)
    return model.assign_ids(model.make_project(
        "sweep3", "input", walls=[alvo, p1, p2, pm],
        settings={"base_z_cm": 0.0, "course_step_cm": STEP, "block_height_cm": BH,
                  "num_courses": NC, "expected_rows": NC},
        catalog=CAT))


def roda(inp):
    res, walls, nodes, ops, cat, bz, nc, notes = solver_bridge.run_solver(inp)
    out = from_solver.project_from_solver("sweep3", res, walls, nodes, ops, cat, bz, nc)
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
    return cont, cross, groups, alvo, ordem


achados, combos, com_algum = [], 0, 0
for L in (339.0, 419.0, 499.0, 579.0, 659.0, 739.0, 819.0, 899.0):
    for tmid in (129.0, 169.0, 209.0, 249.0, 289.0):
        if tmid > L - 90.0:
            continue
        for peit, verga in ((110.0, 210.0), (95.0, 215.0), (105.0, 225.0),
                            (150.0, 231.0), (85.0, 205.0)):
            for jt0 in (tmid + 60.0, tmid + 100.0, tmid + 140.0):
                jt1 = jt0 + 121.0
                if jt1 > L - 40.0:
                    continue
                combos += 1
                try:
                    cont, cross, groups, alvo, ordem = roda(cenario(L, tmid, (jt0, jt1, peit, verga)))
                except Exception:
                    continue
                if cont:
                    com_algum += 1
                if cross:
                    achados.append((L, tmid, jt0, jt1, peit, verga, len(cont), len(cross),
                                    [g[0] for g in groups]))
print("combinacoes:", combos, "| com alguma junta continua:", com_algum,
      "| com CROSS-BAND:", len(achados))
for a in sorted(achados, key=lambda x: (x[7], x[6]))[:15]:
    print("  L=%.0f Tmeio=%.0f janela=%.0f..%.0f peit=%.0f verga=%.0f -> total=%d cross=%d bandas=%s" % a)
