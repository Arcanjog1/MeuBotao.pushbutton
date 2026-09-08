"""REDUCAO do reproducer por SUBPLANTA + delta-debugging.

Parte do `input.json` OFICIAL e vai removendo paredes enquanto a
IDENTIDADE FISICA alvo (ponto global da junta + cotas das duas fiadas)
continuar sendo acusada com a correcao DESLIGADA. Mantem a geometria e os
parametros reais da abertura - nenhuma coordenada e' inventada.

Uso: reduzir.py <root> <projeto> <x> <y> <zA> <zB>
"""
import json, sys, os, copy
root, proj = sys.argv[1], sys.argv[2]
alvo_pt = (float(sys.argv[3]), float(sys.argv[4]))
alvo_z = (float(sys.argv[5]), float(sys.argv[6]))
sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver
MOD = solver_bridge.engine()
MOD.CROSS_BAND_JOINT_PROPAGATION_ENABLED = False

BASE = json.load(open(os.path.join(root, "nuvem/benchmark/projects", proj, "input.json")))


def subplanta(indices):
    p = copy.deepcopy(BASE)
    p["walls"] = [BASE["walls"][i] for i in sorted(indices)]
    return model.assign_ids(p)


def tem_alvo(indices, tol=0.6):
    p = subplanta(indices)
    try:
        res, walls, nodes, ops, cat, bz, nc, notes = solver_bridge.run_solver(p)
    except Exception:
        return False, None
    out = from_solver.project_from_solver(proj, res, walls, nodes, ops, cat, bz, nc)
    f, _e = validators.run_all(out, {})
    idx = {w["id"]: w for w in out["walls"]}
    for x in f:
        if x["code"] != "PRISM_CONTINUOUS_JOINT":
            continue
        w = idx[x["wall"]]
        dv, _ = model.direction_of(w["start_cm"], w["end_cm"])
        t = x["joint_t_cm"]
        pt = (w["start_cm"][0] + dv[0] * t, w["start_cm"][1] + dv[1] * t)
        if abs(pt[0] - alvo_pt[0]) > tol or abs(pt[1] - alvo_pt[1]) > tol:
            continue
        zs = []
        for rk in ("row_a", "row_b"):
            rr = [r for r in w["rows"] if r["row"] == x[rk]]
            zs.append(round(rr[0]["elevation_cm"], 1) if rr else None)
        if tuple(sorted(zs)) == tuple(sorted(alvo_z)):
            return True, (w["id"], w["length_cm"], x["joint_t_cm"], x["stagger_cm"])
    return False, None


todos = list(range(len(BASE["walls"])))
ok, det = tem_alvo(todos)
print("planta COMPLETA (%d paredes): alvo presente = %s %s" % (len(todos), ok, det))
if not ok:
    sys.exit(1)

atual = list(todos)
bloco = max(1, len(atual) // 2)
while bloco >= 1:
    i = 0
    mudou = False
    while i < len(atual):
        tentativa = atual[:i] + atual[i + bloco:]
        if tentativa and tem_alvo(tentativa)[0]:
            atual = tentativa
            mudou = True
        else:
            i += bloco
    if not mudou:
        bloco //= 2
    print("   ... %d paredes (bloco=%d)" % (len(atual), bloco))
ok, det = tem_alvo(atual)
print("SUBPLANTA MINIMA: %d paredes -> alvo presente = %s %s" % (len(atual), ok, det))
print("indices (0-based no input.json oficial):", atual)
json.dump({"projeto": proj, "alvo_pt": alvo_pt, "alvo_z": alvo_z,
           "indices": atual, "detalhe": det},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "subplanta_%s.json" % proj), "w"), indent=1)
