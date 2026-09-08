"""REPRODUCER DA CR-G12 - a coincidencia e' CROSS-BAND, na fronteira da
banda de abertura, e o tipo do no' de ponta decide qual layout a banda de
cima escolhe.

Geometria copiada do caso real: parede 939cm, porta t=314..405 head=160,
nos de ponta em t=7 e t=932. Unica variavel: no' T (STATE_R) x no' L
(STATE_C, apos a divisao de paredes da CR-B).
"""
import json, sys, os, collections
root = sys.argv[1]; sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver
L, TH, H, STEP = 939.0, 14.0, 340.0, 20.0

def cenario(tipo):
    porta = model.make_opening("door", 314.0, 405.0, 0.0, 160.0, confidence="measured")
    alvo = model.make_wall("ALVO", (0.0,0.0), (L,0.0), TH, base_z_cm=0.0,
                           height_cm=H, openings=[porta], junctions=[], rows=[])
    y1 = 0.0 if tipo=="L" else -300.0    # T = perpendicular ATRAVESSA
    p1 = model.make_wall("P1", (7.0,y1), (7.0,300.0), TH, base_z_cm=0.0, height_cm=H)
    p2 = model.make_wall("P2", (932.0,y1), (932.0,300.0), TH, base_z_cm=0.0, height_cm=H)
    return model.assign_ids(model.make_project("repro_g12","input", walls=[alvo,p1,p2],
        settings={"base_z_cm":0.0,"course_step_cm":STEP,"block_height_cm":19.0,
                  "num_courses":17,"expected_rows":17},
        catalog={c:{"length_cm":l,"height_cm":19.0,"width_cm":14.0} for c,l in
                 (("B39",39.0),("B34",34.0),("B19",19.0),("B54",54.0),("C09",9.0),("C04",4.0))}))

def roda(tipo):
    inp=cenario(tipo)
    (res,walls,nodes,ops,cat,bz,nc,notes)=solver_bridge.run_solver(inp)
    out=from_solver.project_from_solver("repro_g12",res,walls,nodes,ops,cat,bz,nc,metadata={"r":tipo})
    f,e=validators.run_all(out,{})
    alvo=max(out["walls"], key=lambda w: w["length_cm"])
    cont=[x for x in f if x["code"]=="PRISM_CONTINUOUS_JOINT" and x["wall"]==alvo["id"]]
    tipos=sorted({j.get("type") for w in out["walls"] for j in (w.get("junctions") or [])})
    print(f"\n### no' de ponta = {tipo}   (detectado: {tipos})   juntas continuas na parede alvo = {len(cont)}")
    for x in cont[:8]:
        ra=[r for r in alvo["rows"] if r["row"]==x["row_a"]][0]
        rb=[r for r in alvo["rows"] if r["row"]==x["row_b"]][0]
        print(f"     junta t={x['joint_t_cm']:.1f} desenc={x['stagger_cm']:.2f} entre z={ra['elevation_cm']:.0f} e z={rb['elevation_cm']:.0f}")
    for r in sorted(alvo["rows"], key=lambda r: r["elevation_cm"]):
        if 130 <= r["elevation_cm"] <= 190:
            print(f"     z={r['elevation_cm']:6.1f}: {sorted([(round(b['t_start_cm']),round(b['t_end_cm']),b['code']) for b in r['blocks']])[:6]}")
    return len(cont)
a=roda("T"); b=roda("L")
print(f"\n>>> no' T -> {a} | no' L -> {b}")
print(">>> REPRODUZIU o mecanismo do G12" if b>a else ">>> nao reproduziu")
