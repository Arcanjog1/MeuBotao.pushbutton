"""G12 - identidades FISICAS de PRISM_CONTINUOUS_JOINT no delta IN_R -> IN_C.

Reusa a metodologia ja' versionada (`g12.py`/`g12_classif.py`): identidade =
(ponto GLOBAL da junta, cotas fisicas das duas fiadas, espessura). Nunca
W0xx, nunca o eixo, nunca o tipo do no'.

Uso: g12_ident.py <arvore> <dir_com_inputs_CRB> <saida.json>
"""
import json, sys, os, collections
root, crb, saida = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, root)
from nuvem.benchmark import solver_bridge, validators, model
from nuvem.benchmark.extract import from_solver


def resolve(inp, pid):
    res, walls, nodes, ops, cat, bz, nc, notes = solver_bridge.run_solver(inp)
    proj = from_solver.project_from_solver(pid, res, walls, nodes, ops, cat, bz, nc)
    f, _e = validators.run_all(proj, {})
    return proj, f


def identidades(proj, findings, code="PRISM_CONTINUOUS_JOINT"):
    idx = {w["id"]: w for w in proj["walls"]}
    out = {}
    for f in findings:
        if f["code"] != code:
            continue
        w = idx[f["wall"]]
        dv, _ = model.direction_of(w["start_cm"], w["end_cm"])
        t = f["joint_t_cm"]
        pt = (round(w["start_cm"][0] + dv[0] * t, 1), round(w["start_cm"][1] + dv[1] * t, 1))
        z = []
        for rk in ("row_a", "row_b"):
            rr = [r for r in w["rows"] if r["row"] == f[rk]]
            z.append(round(rr[0]["elevation_cm"], 1) if rr else None)
        out.setdefault((pt, tuple(z), w["thickness_cm"]), []).append(
            {"wall": w["id"], "len": w["length_cm"], "stagger": f["stagger_cm"]})
    return out


rel = {}
for proj_id in ("torre_easy_lo_r00_tgd", "torre_easy_lo_r00_tp1"):
    est = {}
    for st, fn in (("R", "input_roundtrip.json"), ("C", "input_candidate.json")):
        p, f = resolve(json.load(open(os.path.join(crb, proj_id, fn))), proj_id)
        est[st] = {"ident": identidades(p, f),
                   "codigos": dict(collections.Counter(x["code"] for x in f))}
    novas = sorted(k for k in est["C"]["ident"] if k not in est["R"]["ident"])
    sumiram = sorted(k for k in est["R"]["ident"] if k not in est["C"]["ident"])
    rel[proj_id] = {
        "R_total": len(est["R"]["ident"]), "C_total": len(est["C"]["ident"]),
        "novas": [list(map(str, k)) for k in novas],
        "n_novas": len(novas), "n_sumiram": len(sumiram),
        "codigos_R": est["R"]["codigos"], "codigos_C": est["C"]["codigos"],
    }
    print("%s: R=%d C=%d saldo=%+d | NOVAS=%d sumiram=%d"
          % (proj_id, len(est["R"]["ident"]), len(est["C"]["ident"]),
             len(est["C"]["ident"]) - len(est["R"]["ident"]), len(novas), len(sumiram)))
    for k in novas[:14]:
        print("    NOVA ponto=%s cotas=%s esp=%s" % k)
json.dump(rel, open(saida, "w"), indent=1)
print("salvo em", saida)
