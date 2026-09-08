"""REPRODUCER MINIMO da CR-G12: parede de 939cm com no' de ponta T x L.

Hipotese: com no' `L` de ponta o solver escolhe B19 como 2a peca da fiada B,
o que RESTAURA a fase entre as duas familias e produz juntas continuas.
Com no' `T` na mesma geometria isso nao acontece.
"""
import json, sys, os, collections
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

L, TH, H, STEP = 939.0, 14.0, 300.0, 20.0
def parede(wid, s, e, junc):
    w = model.make_wall(wid, s, e, TH, base_z_cm=0.0, height_cm=H, openings=[], junctions=[], rows=[])
    w["junctions"] = junc
    return w

def cenario(tipo):
    """parede alvo de 939cm + duas perpendiculares. `tipo` decide se as
    perpendiculares ATRAVESSAM (no' T) ou TERMINAM (no' L) no ponto."""
    alvo = parede("ALVO", (0.0, 0.0), (L, 0.0), [])
    if tipo == "T":     # perpendicular passa direto (parede longa cruzando)
        p1 = parede("P1", (7.0, -300.0), (7.0, 300.0), [])
        p2 = parede("P2", (932.0, -300.0), (932.0, 300.0), [])
    else:               # perpendicular TERMINA no ponto -> no' L
        p1 = parede("P1", (7.0, 0.0), (7.0, 300.0), [])
        p2 = parede("P2", (932.0, 0.0), (932.0, 300.0), [])
    proj = model.make_project("repro_g12", "input", walls=[alvo, p1, p2],
        settings={"base_z_cm":0.0, "course_step_cm":STEP, "block_height_cm":19.0,
                  "num_courses":15, "expected_rows":15},
        catalog={c:{"length_cm":l,"height_cm":19.0,"width_cm":14.0} for c,l in
                 (("B39",39.0),("B34",34.0),("B19",19.0),("B54",54.0),("C09",9.0),("C04",4.0))})
    return model.assign_ids(proj)

def roda(tipo):
    inp = cenario(tipo)
    (res, walls, nodes, ops, cat, bz, nc, notes) = solver_bridge.run_solver(inp)
    out = from_solver.project_from_solver("repro_g12", res, walls, nodes, ops, cat, bz, nc,
                                          metadata={"repro": tipo})
    f, e = validators.run_all(out, {})
    idx = {w["id"]: w for w in out["walls"]}
    alvo = max(out["walls"], key=lambda w: w["length_cm"])
    cont = [x for x in f if x["code"]=="PRISM_CONTINUOUS_JOINT" and x["wall"]==alvo["id"]]
    tipos = sorted({(j.get("type")) for w in out["walls"] for j in (w.get("junctions") or [])})
    print(f"\n### no' de ponta = {tipo}  (tipos detectados: {tipos})")
    print(f"    parede alvo L={alvo['length_cm']} fiadas={len(alvo['rows'])}")
    print(f"    PRISM_CONTINUOUS_JOINT na parede alvo: {len(cont)}")
    for r in sorted(alvo["rows"], key=lambda r: r["elevation_cm"])[:4]:
        bl=sorted([(round(b['t_start_cm']),round(b['t_end_cm']),b['code']) for b in r["blocks"]])[:7]
        print(f"      z={r['elevation_cm']:6.1f}: {bl}")
    return len(cont)
a=roda("T"); b=roda("L")
print(f"\n>>> RESULTADO: no' T -> {a} juntas continuas | no' L -> {b} juntas continuas")
print(">>> REPRODUZIU" if b>a else ">>> NAO reproduziu neste cenario minimo")
