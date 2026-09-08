"""FASE 3 - classifica as identidades NOVAS de JUNCTION_MISSING_BINDING:
no' que ja' existia em R (piora real) x no' que so' existe em C (criado pela
divisao da parede = mudanca de unidade)."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_junctions
def nodes(d):
    """todo no' declarado no estado, por (ponto, tipo)."""
    s=collections.Counter()
    for w in d["walls"]:
        for j in w.get("junctions") or []:
            s[(tuple(round(v,1) for v in j["point_cm"]), j.get("type"))]+=1
    return s
def achados(d):
    s=collections.Counter()
    for f in validate_junctions.validate(d):
        if f["code"]!="JUNCTION_MISSING_BINDING": continue
        s[(tuple(round(v,1) for v in f["point_cm"]), round(f["elevation_cm"],1), f.get("junction_type"))]+=1
    return s
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    nR,nC=nodes(R),nodes(C); aR,aC=achados(R),achados(C)
    novas=[i for i in aC if i not in aR]; sumiu=[i for i in aR if i not in aC]
    ptsR={p for p,_ in nR}
    em_no_preexistente=[i for i in novas if i[0] in ptsR]
    em_no_novo=[i for i in novas if i[0] not in ptsR]
    print(f"===== {proj}")
    print(f"   nos declarados: R={sum(nR.values())} C={sum(nC.values())} | pontos distintos R={len(ptsR)} C={len({p for p,_ in nC})}")
    print(f"   JUNCTION_MISSING_BINDING: R={sum(aR.values())} C={sum(aC.values())} saldo={sum(aC.values())-sum(aR.values()):+d}")
    print(f"   identidades NOVAS={len(novas)}  das quais:")
    print(f"       em no' que JA EXISTIA em R (piora candidata a REAL): {len(em_no_preexistente)}")
    print(f"       em no' que SO' existe em C (criado pela divisao):     {len(em_no_novo)}")
    print(f"   identidades que SUMIRAM={len(sumiu)}")
    for i in em_no_preexistente[:6]: print(f"       >> preexistente: {i}")
