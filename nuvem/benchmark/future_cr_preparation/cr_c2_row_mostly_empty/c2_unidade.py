"""CR-C2 - PROVA da unidade: STATE_C avaliado na unidade de parede de STATE_R.
Os blocos sao os MESMOS (0 perdidos / 0 novos). Se o delta zerar, os +23 sao
100% mudanca de unidade de avaliacao, nao defeito fisico."""
import json, sys, os, collections, copy
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark.validators import validate_wall_coverage as VC
from nuvem.benchmark import model, analysis

def reagrupa(C, R):
    """Reconstroi STATE_C usando as PAREDES de R como unidade: cada bloco de C
    e' reatribuido a' parede de R que o contem (por projecao no eixo)."""
    novo = copy.deepcopy(R)
    for w in novo["walls"]:
        for r in w.get("rows") or []: r["blocks"] = []
    # indice das paredes de R por eixo
    alvos = []
    for w in novo["walls"]:
        d, L = model.direction_of(w["start_cm"], w["end_cm"])
        alvos.append((w, d, L))
    for wc in C["walls"]:
        for rc in wc.get("rows") or []:
            for b in rc.get("blocks") or []:
                melhor = None
                for w, d, L in alvos:
                    t, s = model.axial_coordinates(b["center_cm"], w["start_cm"], d)
                    if abs(s) > 8.0 or t < -20.0 or t > L + 20.0: continue
                    if abs(w["thickness_cm"] - wc["thickness_cm"]) > 0.5: continue
                    if melhor is None or abs(s) < melhor[2]: melhor = (w, t, abs(s))
                if melhor is None: continue
                w, t, _ = melhor
                nb = dict(b); nb["t_start_cm"] = t - (b["length_cm"]/2.0 if False else 0)
                # recalcula t_start/t_end no eixo da parede-mae
                d, _L = model.direction_of(w["start_cm"], w["end_cm"])
                half = (b["t_end_cm"] - b["t_start_cm"]) / 2.0
                nb["t_start_cm"], nb["t_end_cm"] = t - half, t + half
                linha = [x for x in w["rows"] if abs(x["elevation_cm"] - b["z_cm"]) < 0.5]
                if not linha:
                    novo_r = model.make_row(len(w["rows"]), b["z_cm"], [])
                    w["rows"].append(novo_r); linha = [novo_r]
                linha[0]["blocks"].append(nb)
    for w in novo["walls"]:
        w["rows"] = [r for r in w["rows"] if r["blocks"]]
        for i, r in enumerate(sorted(w["rows"], key=lambda r: r["elevation_cm"])): r["row"] = i
        w["rows"] = sorted(w["rows"], key=lambda r: r["elevation_cm"])
    return novo

for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    Cu = reagrupa(C, R)
    nb=lambda d: sum(len(r["blocks"]) for w in d["walls"] for r in w["rows"])
    cnt=lambda d: collections.Counter(f["code"] for f in VC.validate(d))
    cR, cC, cU = cnt(R), cnt(C), cnt(Cu)
    print(f"===== {proj}  (blocos R={nb(R)} C={nb(C)} C_reagrupado={nb(Cu)})")
    for k in sorted(set(cR)|set(cC)|set(cU)):
        print(f"   {k:30s} R={cR[k]:5d} C={cC[k]:5d} deltaC={cC[k]-cR[k]:+5d} || C_na_unidade_de_R={cU[k]:5d} delta={cU[k]-cR[k]:+5d}")
