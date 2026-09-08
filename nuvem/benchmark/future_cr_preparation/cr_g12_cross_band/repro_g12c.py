"""REPRODUCER DA CR-G12 - subprojeto REAL isolado.

Extrai do input a parede alvo (939cm, y=187) e TODAS as paredes que tocam
as pontas dela, nos dois estados (IN_R e IN_C), e roda o solver so' nesse
subconjunto. Determinismo conferido em 2 execucoes.
"""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver

def sub(inp, alvo_pred, raio=30.0):
    alvo=[w for w in inp["walls"] if alvo_pred(w)]
    assert len(alvo)==1, [(w["id"],w["length_cm"]) for w in alvo]
    a=alvo[0]; pts=[tuple(a["start_cm"]), tuple(a["end_cm"])]
    keep=[a]
    for w in inp["walls"]:
        if w is a: continue
        for e in (w["start_cm"], w["end_cm"]):
            if any(abs(e[0]-p[0])<raio and abs(e[1]-p[1])<raio for p in pts): keep.append(w); break
        else:
            from nuvem.benchmark import analysis
            if any(analysis.distance_point_to_segment_cm(p, w["start_cm"], w["end_cm"])<raio for p in pts):
                keep.append(w)
    p=dict(inp); p["walls"]=[json.loads(json.dumps(w)) for w in keep]
    return model.assign_ids(json.loads(json.dumps(p))), a

def roda(inp, tag, alvo_pred):
    p, a = sub(inp, alvo_pred)
    (res,walls,nodes,ops,cat,bz,nc,notes)=solver_bridge.run_solver(p)
    o=from_solver.project_from_solver("repro",res,walls,nodes,ops,cat,bz,nc,metadata={"t":tag})
    f,e=validators.run_all(o,{})
    alvo=max(o["walls"], key=lambda w: w["length_cm"])
    cont=[x for x in f if x["code"]=="PRISM_CONTINUOUS_JOINT" and x["wall"]==alvo["id"]]
    tp={j.get("type") for w in o["walls"] for j in (w.get("junctions") or [])}
    print(f"\n### {tag}: subprojeto com {len(p['walls'])} paredes | alvo L={alvo['length_cm']} | tipos de no' {sorted(tp)}")
    print(f"    PRISM_CONTINUOUS_JOINT na parede alvo = {len(cont)}")
    for x in cont[:8]:
        ra=[r for r in alvo["rows"] if r["row"]==x["row_a"]][0]; rb=[r for r in alvo["rows"] if r["row"]==x["row_b"]][0]
        print(f"      t={x['joint_t_cm']:.1f} desenc={x['stagger_cm']:.2f} z={ra['elevation_cm']:.0f}/{rb['elevation_cm']:.0f}")
    for r in sorted(alvo["rows"], key=lambda r: r["elevation_cm"]):
        if 135<=r["elevation_cm"]<=165:
            print(f"      z={r['elevation_cm']:6.1f}: {sorted([(round(b['t_start_cm']),round(b['t_end_cm']),b['code']) for b in r['blocks']])[:6]}")
    return len(cont)

proj="torre_easy_lo_r00_tgd"
pred=lambda w: abs(w["start_cm"][1]-187.048)<.6 and abs(w["end_cm"][1]-187.048)<.6 and abs(w["length_cm"]-939.0)<.6 and abs(w["start_cm"][0]-(-1078.487))<1
IR=json.load(open(os.path.join(out,proj,"input_roundtrip.json")))
IC=json.load(open(os.path.join(out,proj,"input_candidate.json")))
a=roda(IR,"IN_R (no' T)",pred); b=roda(IC,"IN_C (no' L)",pred)
a2=roda(IR,"IN_R repeticao",pred); b2=roda(IC,"IN_C repeticao",pred)
print(f"\n>>> IN_R={a} IN_C={b} | determinismo: {a==a2 and b==b2}")
print(">>> REPRODUZIU" if b>a else ">>> nao reproduziu no subprojeto")
