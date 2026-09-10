"""FASE 4 - G18: stable_key sem ambiguidade + round-trip + blocos humanos."""
import json, sys, os, collections
root, out = sys.argv[1], sys.argv[2]; sys.path.insert(0, root)
from nuvem.benchmark import model
def bkey(b):  # identidade fisica do bloco
    return (b.get("code"), round(b["center_cm"][0],2), round(b["center_cm"][1],2),
            round(b["z_cm"],2), round(b.get("rotation_deg") or 0.0,1))
for proj in ("torre_easy_lo_r00_tgd","torre_easy_lo_r00_tp1"):
    A=json.load(open(os.path.join(root,"nuvem/benchmark/projects",proj,"reference.json")))
    R=json.load(open(os.path.join(out,proj,"reference_roundtrip.json")))
    C=json.load(open(os.path.join(out,proj,"reference_candidate.json")))
    print(f"===== {proj}")
    for nome,d in (("STATE_A",A),("STATE_R",R),("STATE_C",C)):
        keys=collections.Counter(w["key"] for w in d["walls"])
        dup={k:v for k,v in keys.items() if v>1}
        blocos=collections.Counter(bkey(b) for w in d["walls"] for r in w.get("rows") or [] for b in r.get("blocks") or [])
        dupb={k:v for k,v in blocos.items() if v>1}
        print(f"  {nome}: paredes={len(d['walls'])} chaves_distintas={len(keys)} AMBIGUAS={len(dup)} "
              f"| blocos={sum(blocos.values())} identidades_distintas={len(blocos)} DUPLICADOS={len(dupb)}")
    bA=collections.Counter(bkey(b) for w in A["walls"] for r in w.get("rows") or [] for b in r.get("blocks") or [])
    bR=collections.Counter(bkey(b) for w in R["walls"] for r in w.get("rows") or [] for b in r.get("blocks") or [])
    bC=collections.Counter(bkey(b) for w in C["walls"] for r in w.get("rows") or [] for b in r.get("blocks") or [])
    print(f"  ROUND-TRIP A->R: perdidos={sum((bA-bR).values())} novos={sum((bR-bA).values())}  (G-roundtrip)")
    print(f"  BLOCOS HUMANOS R->C: perdidos={sum((bR-bC).values())} novos={sum((bC-bR).values())}")
    # aberturas medidas preservadas
    def med(d): return [o for w in d["walls"] for o in w.get("openings") or [] if o.get("confidence")=="measured"]
    mA,mR,mC=med(A),med(R),med(C)
    kk=lambda L: collections.Counter((o.get("source_element_id"),round(o["t_start_cm"],1),round(o["t_end_cm"],1),round(o["sill_cm"],1),round(o["head_cm"],1)) for o in L)
    print(f"  ABERTURAS measured: A={len(mA)} R={len(mR)} C={len(mC)} | alteradas R->C={sum((kk(mR)-kk(mC)).values())}")
